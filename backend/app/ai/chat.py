"""Basic conversational advisor for the floating chatbot."""

from __future__ import annotations

import logging

from app.ai import llm
from app.ai.llm import LLMError
from app.schemas.chat import ChatTurn

logger = logging.getLogger(__name__)

_MAX_HISTORY = 8

_FALLBACK_REPLIES = {
    "en": (
        "I am the UdyamAI assistant. I can help you explore business feasibility, "
        "nearby markets, competitors, government schemes (PMEGP, PMFME, MUDRA), and "
        "financial planning. Run an analysis from Onboarding to get location-specific "
        "scores, then open the Dashboard for market, map, scheme, and risk details. "
        "The live AI advisor is temporarily unavailable — ask again in a moment."
    ),
    "hi": (
        "मैं उद्यमएआई सहायक हूँ। मैं व्यवसाय व्यवहार्यता, पास के बाज़ार, प्रतिस्पर्धी, "
        "सरकारी योजनाएँ (पीएमईजीपी, पीएमएफएमई, मुद्रा) और वित्तीय योजना में मदद कर सकता हूँ। "
        "स्थान-विशिष्ट स्कोर के लिए पंजीकरण से विश्लेषण चलाएँ, फिर डैशबोर्ड खोलें। "
        "लाइव एआई सलाहकार अभी उपलब्ध नहीं है — थोड़ी देर बाद फिर पूछें।"
    ),
    "mr": (
        "मी उद्यमएआय सहाय्यक आहे. व्यवहार्यता, जवळचे बाजार, स्पर्धक, शासकीय योजना "
        "(पीएमईजीपी, पीएमएफएमई, मुद्रा) आणि आर्थिक नियोजनात मी मदत करू शकतो. "
        "स्थान-विशिष्ट गुणांसाठी नोंदणीतून विश्लेषण चालवा आणि डॅशबोर्ड उघडा. "
        "लाइव्ह एआय सल्लागार सध्या उपलब्ध नाही — थोड्या वेळाने पुन्हा विचारा."
    ),
}


def _build_prompt(message: str, history: list[ChatTurn], language: str) -> str:
    history_lines: list[str] = []
    for turn in history[-_MAX_HISTORY:]:
        speaker = "User" if turn.role == "user" else "Assistant"
        history_lines.append(f"{speaker}: {turn.content.strip()}")
    history_block = "\n".join(history_lines) if history_lines else "(no prior turns)"

    return f"""You are UdyamAI, a concise assistant for rural and semi-urban micro-entrepreneurs in Maharashtra.

Help with:
- business feasibility, markets, competitors, and infrastructure
- government schemes such as PMEGP, PMFME, MUDRA, and Maharashtra state schemes
- financial planning (capital, loan, EMI, break-even)
- how to use this app (Onboarding → Analysis → Dashboard → Map / Schemes / Report)

Rules:
- Keep answers short (2–6 sentences) unless the user asks for more.
- Do not invent subsidy percentages, loan rates, prices, or eligibility rules.
- If a number is unknown, say it must be checked in the dashboard or official scheme documents.
- Reply entirely in the user's language.
- Language code: {language} (en = English, hi = Hindi, mr = Marathi).
- If language is hi, write in Hindi (Devanagari). If mr, write in Marathi (Devanagari).

Conversation so far:
{history_block}

User: {message.strip()}
Assistant:"""


def generate_chat_reply(
    message: str,
    history: list[ChatTurn] | None = None,
    language: str = "en",
) -> tuple[str, bool]:
    """Return (reply_text, provider_available)."""
    fallback = _FALLBACK_REPLIES.get(language, _FALLBACK_REPLIES["en"])
    try:
        reply = llm.generate(_build_prompt(message, history or [], language)).strip()
        if reply:
            return reply, True
        logger.warning("Chat LLM returned empty text")
        return fallback, False
    except LLMError as exc:
        logger.warning("Chat LLM unavailable: %s", exc)
        return fallback, False
    except Exception:
        logger.exception("Chat generation failed")
        return fallback, False
