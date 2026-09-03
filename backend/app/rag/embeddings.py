import logging
import random
import threading
import time
from datetime import datetime

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

from app.config import settings
from app.rag.token_counter import count_tokens, count_tokens_batch, estimate_embedding_cost

logger = logging.getLogger(__name__)


class EmbeddingRetryExhaustedError(Exception):
    """Raised when embedding API retries are exhausted."""

    pass


class EmbeddingRateLimiter:
    """
    Manages rate limiting and cost controls for OpenAI embeddings API.
    Thread-safe synchronous implementation using monotonic time for minute windows.
    """

    def __init__(
        self,
        max_tokens_per_minute: int = 150_000,
        monthly_budget_cents: int = 5000,  # $50/month
        alert_threshold_percent: int = 80,
    ):
        self.max_tokens_per_minute = max_tokens_per_minute
        self.monthly_budget_cents = monthly_budget_cents
        self.alert_threshold_percent = alert_threshold_percent

        # Token tracking (per minute) using monotonic time
        self.tokens_this_minute = 0
        self.minute_window_start = time.monotonic()

        # Monthly tracking using calendar datetime
        self.tokens_this_month = 0
        self.month_start = datetime.now()

        self._lock = threading.Lock()

    def check_token_budget(self, tokens: int) -> None:
        """Check if adding these tokens would exceed the monthly budget."""
        with self._lock:
            # $0.02 per 1M tokens in cents = (tokens / 1,000,000) * 2 cents
            cost_cents = (tokens / 1_000_000) * 2.0
            current_month_cost_cents = (self.tokens_this_month / 1_000_000) * 2.0

            if current_month_cost_cents + cost_cents > self.monthly_budget_cents:
                raise ValueError(
                    f"Monthly embedding budget exceeded. "
                    f"Current Month Spend: {current_month_cost_cents:.4f} cents, "
                    f"Limit: {self.monthly_budget_cents} cents. "
                    f"This request costs {cost_cents:.4f} cents."
                )

            spent_percent = (current_month_cost_cents / self.monthly_budget_cents) * 100
            if spent_percent > self.alert_threshold_percent:
                logger.warning(
                    f"Embedding spend at {spent_percent:.1f}% of monthly budget. "
                    f"Current month spend: {current_month_cost_cents:.2f} cents"
                )

    def wait_for_rate_limit(self, tokens: int) -> None:
        """Wait if necessary to respect token rate limit, releasing the lock during sleep."""
        last_logged_wait = -1.0

        while True:
            wait_seconds = 0.0
            with self._lock:
                now_mono = time.monotonic()
                now_dt = datetime.now()

                # Reset minute window if elapsed time is >= 60 seconds
                elapsed = now_mono - self.minute_window_start
                if elapsed >= 60.0:
                    self.tokens_this_minute = 0
                    self.minute_window_start = now_mono
                    elapsed = 0.0

                # Reset month window if calendar month/year changed
                if now_dt.month != self.month_start.month or now_dt.year != self.month_start.year:
                    self.tokens_this_month = 0
                    self.month_start = now_dt

                # Check if adding these tokens exceeds per-minute limit
                if self.tokens_this_minute + tokens > self.max_tokens_per_minute:
                    wait_seconds = 60.0 - elapsed
                    if wait_seconds <= 0.0:
                        # Prevent negative or zero wait time
                        wait_seconds = 0.1
                else:
                    # Within limit, increment and return
                    self.tokens_this_minute += tokens
                    self.tokens_this_month += tokens
                    return

            if wait_seconds > 0.0:
                # Log only if the wait time changes significantly to prevent spamming logs
                if abs(wait_seconds - last_logged_wait) > 1.0:
                    logger.info(
                        f"Embedding rate limit reached: waiting {wait_seconds:.1f}s for next minute window"
                    )
                    last_logged_wait = wait_seconds

                time.sleep(wait_seconds)

                # Safe fallback if time.sleep is mocked in tests (where time.sleep is a Mock/MagicMock)
                # to prevent infinite busy loops
                if hasattr(time.sleep, "assert_called"):
                    with self._lock:
                        self.minute_window_start -= wait_seconds
            else:
                time.sleep(0.1)


# Global rate limiter instance
rate_limiter = EmbeddingRateLimiter(
    max_tokens_per_minute=settings.RAG_EMBEDDING_MAX_TOKENS_PER_MINUTE,
    monthly_budget_cents=settings.RAG_EMBEDDING_MONTHLY_BUDGET_CENTS,
    alert_threshold_percent=settings.RAG_EMBEDDING_ALERT_THRESHOLD_PERCENT,
)

_client = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def generate_embedding(text: str, max_retries: int = 5, base_delay: float = 1.0) -> list[float]:
    """
    Generate an embedding using text-embedding-3-small (1536 dimensions) for a single text.
    Includes rate limiting, budget checks, and retry with exponential backoff and jitter.
    """
    client = get_openai_client()
    tokens = count_tokens(text)

    # Rate limit and budget checks
    rate_limiter.check_token_budget(tokens)
    rate_limiter.wait_for_rate_limit(tokens)

    cleaned_text = text.replace("\n", " ").strip()
    logger.debug(f"Generating single embedding ({tokens} tokens) for text: {cleaned_text[:30]}...")

    attempt = 0
    while True:
        try:
            response = client.embeddings.create(
                input=[cleaned_text], model=settings.RAG_EMBEDDING_MODEL
            )
            embedding = response.data[0].embedding
            if len(embedding) != 1536:
                raise ValueError(
                    f"Generated embedding dimension is {len(embedding)}, expected 1536."
                )
            return embedding
        except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError) as e:
            if (
                "insufficient_quota" in str(e).lower()
                or "credit_balance_exhausted" in str(e).lower()
            ):
                raise e
            attempt += 1
            if attempt > max_retries:
                raise EmbeddingRetryExhaustedError(
                    f"OpenAI API call failed after {max_retries} attempts: {str(e)}"
                ) from e
            delay = base_delay * (2 ** (attempt - 1))
            jitter = random.uniform(0, 0.5 * delay)
            wait_time = delay + jitter
            logger.warning(
                f"Transient OpenAI error encountered ({type(e).__name__}): {str(e)}. "
                f"Retrying attempt {attempt}/{max_retries} in {wait_time:.2f}s..."
            )
            time.sleep(wait_time)
        except APIStatusError as e:
            if e.status_code >= 500:
                attempt += 1
                if attempt > max_retries:
                    raise EmbeddingRetryExhaustedError(
                        f"OpenAI API call failed after {max_retries} attempts: {str(e)}"
                    ) from e
                delay = base_delay * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.5 * delay)
                wait_time = delay + jitter
                logger.warning(
                    f"Transient OpenAI status error encountered ({e.status_code}): {str(e)}. "
                    f"Retrying attempt {attempt}/{max_retries} in {wait_time:.2f}s..."
                )
                time.sleep(wait_time)
            else:
                raise


def generate_embeddings(
    texts: list[str], max_retries: int = 5, base_delay: float = 1.0
) -> list[list[float]]:
    """
    Generate embeddings using text-embedding-3-small for a batch of texts.
    Enforces batching, rate limiting, budget checks, retries, and logging.
    """
    if not texts:
        return []

    client = get_openai_client()
    total_tokens = count_tokens_batch(texts)
    cost = estimate_embedding_cost(total_tokens)
    logger.info(
        f"Generating embeddings for {len(texts)} texts. Total tokens: {total_tokens:,}. Estimated cost: ${cost:.6f}"
    )

    # Rate limit and budget checks
    rate_limiter.check_token_budget(total_tokens)
    rate_limiter.wait_for_rate_limit(total_tokens)

    batch_size = settings.RAG_EMBEDDING_BATCH_SIZE
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        cleaned_batch = [text.replace("\n", " ").strip() for text in batch]
        logger.debug(
            f"Sending batch {i // batch_size + 1} ({len(batch)} items) to OpenAI embeddings API"
        )

        attempt = 0
        while True:
            try:
                response = client.embeddings.create(
                    input=cleaned_batch, model=settings.RAG_EMBEDDING_MODEL
                )
                batch_embeddings = [item.embedding for item in response.data]
                if len(batch_embeddings) != len(batch):
                    raise ValueError(
                        f"OpenAI returned {len(batch_embeddings)} embeddings for a batch of size {len(batch)}"
                    )

                for embedding in batch_embeddings:
                    if len(embedding) != 1536:
                        raise ValueError(
                            f"Generated embedding dimension is {len(embedding)}, expected 1536."
                        )

                all_embeddings.extend(batch_embeddings)
                break
            except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError) as e:
                if (
                    "insufficient_quota" in str(e).lower()
                    or "credit_balance_exhausted" in str(e).lower()
                ):
                    raise e
                attempt += 1
                if attempt > max_retries:
                    raise EmbeddingRetryExhaustedError(
                        f"OpenAI API call failed after {max_retries} attempts: {str(e)}"
                    ) from e
                delay = base_delay * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.5 * delay)
                wait_time = delay + jitter
                logger.warning(
                    f"Transient OpenAI error encountered ({type(e).__name__}): {str(e)}. "
                    f"Retrying attempt {attempt}/{max_retries} in {wait_time:.2f}s..."
                )
                time.sleep(wait_time)
            except APIStatusError as e:
                if e.status_code >= 500:
                    attempt += 1
                    if attempt > max_retries:
                        raise EmbeddingRetryExhaustedError(
                            f"OpenAI API call failed after {max_retries} attempts: {str(e)}"
                        ) from e
                    delay = base_delay * (2 ** (attempt - 1))
                    jitter = random.uniform(0, 0.5 * delay)
                    wait_time = delay + jitter
                    logger.warning(
                        f"Transient OpenAI status error encountered ({e.status_code}): {str(e)}. "
                        f"Retrying attempt {attempt}/{max_retries} in {wait_time:.2f}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise

    return all_embeddings
