import logging

from app.config import settings

try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)

EMBEDDING_COST_PER_MILLION_TOKENS = 0.02


def _get_encoding():
    """Get tiktoken encoding for configured model or fallback to cl100k_base."""
    if tiktoken is None:
        return None
    model_name = getattr(settings, "RAG_EMBEDDING_MODEL", "text-embedding-3-small")
    try:
        return tiktoken.encoding_for_model(model_name)
    except Exception:
        try:
            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None


def count_tokens(text: str) -> int:
    """Count tokens in a string using tiktoken with fallback."""
    if not text:
        return 0
    encoding = _get_encoding()
    if encoding is not None:
        try:
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Tiktoken encoding failed: {str(e)}. Using fallback estimate.")
    # Fallback estimate: ~4 characters per token
    return max(1, len(text) // 4)


def count_tokens_batch(texts: list[str]) -> int:
    """Count total tokens in a batch of strings."""
    return sum(count_tokens(text) for text in texts)


def estimate_embedding_cost(tokens: int) -> float:
    """Estimate cost in dollars: $0.02 per 1M tokens."""
    return (tokens / 1_000_000) * EMBEDDING_COST_PER_MILLION_TOKENS
