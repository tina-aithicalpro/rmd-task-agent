"""
Settings for the RMD Task Agent.
All secrets come from environment variables (set in Railway), never hardcoded.
"""
import os


class Settings:
    # Railway provisions DATABASE_URL automatically when you add a Postgres plugin.
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

    # Shared-secret API key. Every request must send it as header: X-API-Key.
    # Set this in Railway as API_KEY. If unset, the app refuses to start (see check).
    API_KEY: str = os.environ.get("API_KEY", "")

    # Anthropic key for the redaction/draft generation (used by the generators,
    # wired in the next build step). Set in Railway as ANTHROPIC_API_KEY.
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

    # Client identity (single-client agent for now).
    CLIENT_NAME: str = "RegenesisMD"


settings = Settings()


def require_startup_secrets() -> None:
    """Fail fast at boot if the two must-have secrets are missing.
    A task agent with no API key is world-open; refuse to run rather than
    silently expose the endpoints."""
    missing = []
    if not settings.DATABASE_URL:
        missing.append("DATABASE_URL")
    if not settings.API_KEY:
        missing.append("API_KEY")
    if missing:
        raise RuntimeError(
            "Refusing to start. Missing required env vars: "
            + ", ".join(missing)
            + ". Set them in Railway."
        )
