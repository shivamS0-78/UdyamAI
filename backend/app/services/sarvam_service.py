import base64
import io
import logging
import re
import wave
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SARVAM_BASE_URL = "https://api.sarvam.ai"

# BCP-47 supported language codes in Sarvam AI
SUPPORTED_LANGUAGES = {
    "hi-IN": "hi-IN",
    "mr-IN": "mr-IN",
    "en-IN": "en-IN",
    "bn-IN": "bn-IN",
    "te-IN": "te-IN",
    "ta-IN": "ta-IN",
    "gu-IN": "gu-IN",
    "kn-IN": "kn-IN",
    "ml-IN": "ml-IN",
    "pa-IN": "pa-IN",
    "or-IN": "or-IN",
    "as-IN": "as-IN",
    # 2-letter aliases
    "hi": "hi-IN",
    "mr": "mr-IN",
    "en": "en-IN",
    "bn": "bn-IN",
    "te": "te-IN",
    "ta": "ta-IN",
    "gu": "gu-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "pa": "pa-IN",
    "or": "or-IN",
    "as": "as-IN",
}


VALID_SPEAKERS = {
    "shubh",
    "aditya",
    "ritu",
    "priya",
    "neha",
    "rahul",
    "pooja",
    "rohan",
    "simran",
    "kavya",
    "amit",
    "dev",
    "ishita",
    "shreya",
    "ratan",
    "varun",
    "manan",
    "sumit",
    "roopa",
    "kabir",
    "aayan",
    "ashutosh",
    "advait",
    "anand",
    "tanya",
    "tarun",
    "sunny",
    "mani",
    "gokul",
    "vijay",
    "shruti",
}


def clean_text_for_speech(text: str) -> str:
    """Remove markdown syntax, URLs, bullet symbols, and excessive formatting for natural speech."""
    if not text:
        return ""
    cleaned = re.sub(r"https?://\S+", "", text)
    cleaned = re.sub(r"[*#_~`>[\]()]", "", cleaned)
    cleaned = re.sub(r"[•\-]", "", cleaned)
    cleaned = re.sub(r"\n+", ". ", cleaned)
    return cleaned.strip()


def _chunk_text(text: str, max_len: int = 490) -> list[str]:
    """Split *text* into chunks of at most *max_len* characters.

    Splitting priorities:
    1. sentence boundary ('. ', '? ', '! ')
    2. clause boundary (', ', '; ', ' — ', ' – ')
    3. word boundary (' ')
    4. hard cut (last resort)
    """
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break
        window = remaining[:max_len]
        # Find last sentence boundary
        cut = -1
        for sep in (". ", "? ", "! "):
            idx = window.rfind(sep)
            if idx > cut:
                cut = idx + len(sep)
        if cut <= 0:
            # clause boundary
            for sep in (", ", "; ", " — ", " – "):
                idx = window.rfind(sep)
                if idx > cut:
                    cut = idx + len(sep)
        if cut <= 0:
            # word boundary
            idx = window.rfind(" ")
            if idx > 0:
                cut = idx + 1
        if cut <= 0:
            cut = max_len
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    return [c for c in chunks if c]


def _normalize_content_type(content_type: str) -> str:
    """Strip codec/params from MIME type so Sarvam accepts it.

    e.g. 'audio/webm;codecs=opus' → 'audio/webm'
    """
    return content_type.split(";")[0].strip() if content_type else "audio/webm"


def _concatenate_wav_base64(segments: list[str]) -> str:
    """Decode a list of base64-encoded WAV strings, concatenate PCM data,
    and return a single base64-encoded WAV string."""
    if len(segments) == 1:
        return segments[0]

    pcm_frames: list[bytes] = []
    params = None
    for seg in segments:
        raw = base64.b64decode(seg)
        buf = io.BytesIO(raw)
        try:
            with wave.open(buf, "rb") as wf:
                if params is None:
                    params = wf.getparams()
                pcm_frames.append(wf.readframes(wf.getnframes()))
        except wave.Error:
            # If one segment isn't valid WAV, just return the first one
            return segments[0]

    if not params or not pcm_frames:
        return segments[0]

    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setparams(params)
        for frame in pcm_frames:
            wf.writeframes(frame)

    return base64.b64encode(out.getvalue()).decode("ascii")


class SarvamVoiceService:
    """Service client for interacting with Sarvam AI Voice APIs (Saaras & Bulbul).

    Uses a shared httpx.AsyncClient for connection pooling across requests.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.SARVAM_API_KEY
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        """Lazily create and return a shared, connection-pooled HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=60.0,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        return self._client

    @property
    def stt_model(self) -> str:
        return settings.SARVAM_STT_MODEL or "saaras:v3"

    @property
    def tts_model(self) -> str:
        return settings.SARVAM_TTS_MODEL or "bulbul:v3"

    @property
    def default_speaker(self) -> str:
        speaker = settings.SARVAM_TTS_DEFAULT_SPEAKER
        if speaker and speaker in VALID_SPEAKERS:
            return speaker
        return "shubh"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def speech_to_text(
        self,
        audio_bytes: bytes,
        filename: str = "audio.webm",
        content_type: str = "audio/webm",
        language_code: str = "hi-IN",
    ) -> dict[str, Any]:
        """Send audio to Sarvam AI Speech-to-Text (Saaras) endpoint."""
        if not self.is_configured():
            raise ValueError("SARVAM_API_KEY is not configured on the backend.")

        lang = SUPPORTED_LANGUAGES.get(language_code, "hi-IN")
        # Strip codec params — Sarvam rejects 'audio/webm;codecs=opus'
        safe_ct = _normalize_content_type(content_type)
        headers = {
            "api-subscription-key": self.api_key or "",
        }

        # Sarvam speech-to-text multipart payload
        files = {
            "file": (filename, audio_bytes, safe_ct),
        }
        data = {
            "model": self.stt_model,
            "language_code": lang,
        }

        client = self._get_client()
        try:
            response = await client.post(
                f"{SARVAM_BASE_URL}/speech-to-text",
                headers=headers,
                files=files,
                data=data,
            )
            response.raise_for_status()
            result = response.json()
            transcript = result.get("transcript", "")
            return {
                "transcript": transcript,
                "language_code": lang,
                "raw_response": result,
            }
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"[SarvamVoiceService] STT HTTP error {exc.response.status_code}: {exc.response.text}"
            )
            raise RuntimeError(
                f"Sarvam STT failed ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except Exception as exc:
            logger.error(f"[SarvamVoiceService] STT unexpected error: {exc}")
            raise RuntimeError(f"Sarvam STT request failed: {exc}") from exc

    async def text_to_speech(
        self,
        text: str,
        language_code: str = "hi-IN",
        speaker: str | None = None,
        pitch: float = 0.0,
        pace: float = 1.0,
        loudness: float = 1.0,
    ) -> dict[str, Any]:
        """Send text to Sarvam AI Text-to-Speech (Bulbul) endpoint.

        Sarvam Bulbul v3 limits each input string to 500 characters, so
        longer text is chunked at sentence boundaries and the resulting
        WAV segments are concatenated into a single audio response.
        """
        if not self.is_configured():
            raise ValueError("SARVAM_API_KEY is not configured on the backend.")

        cleaned_text = clean_text_for_speech(text)
        if not cleaned_text:
            raise ValueError("Input text is empty after sanitization.")

        lang = SUPPORTED_LANGUAGES.get(language_code, "hi-IN")
        selected_speaker = speaker or self.default_speaker

        # Chunk text to stay within Sarvam's 500-char-per-input limit
        chunks = _chunk_text(cleaned_text, max_len=490)

        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.api_key or "",
        }

        # Bulbul JSON payload — send all chunks in the inputs list
        payload = {
            "inputs": chunks,
            "target_language_code": lang,
            "speaker": selected_speaker,
            "pace": pace,
            "speech_sample_rate": 22050,
            "model": self.tts_model,
        }

        client = self._get_client()
        try:
            response = await client.post(
                f"{SARVAM_BASE_URL}/text-to-speech",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

            # Extract audio from response (audios list or audio string)
            audios = result.get("audios", [])
            if not audios:
                single = result.get("audio") or result.get("audio_content")
                if single:
                    audios = [single]

            if not audios:
                raise RuntimeError("Sarvam TTS returned an empty audio response.")

            # Concatenate WAV segments if multiple chunks were sent
            audio_b64 = _concatenate_wav_base64(audios)

            return {
                "audio_base64": audio_b64,
                "format": "audio/wav",
                "speaker": selected_speaker,
                "language_code": lang,
            }
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"[SarvamVoiceService] TTS HTTP error {exc.response.status_code}: {exc.response.text}"
            )
            raise RuntimeError(
                f"Sarvam TTS failed ({exc.response.status_code}): {exc.response.text}"
            ) from exc
        except Exception as exc:
            logger.error(f"[SarvamVoiceService] TTS unexpected error: {exc}")
            raise RuntimeError(f"Sarvam TTS request failed: {exc}") from exc


sarvam_voice_service = SarvamVoiceService()
