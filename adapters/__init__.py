# adapters/__init__.py
import os

USE_MOCK = os.getenv("AI_USE_MOCK", "").lower() in {"1", "true", "yes"}

if USE_MOCK:
    from .mock_client import AIClient  # noqa: F401
    _SOURCE = "adapters.mock_client"
else:
    from .ai_client import AIClient  # noqa: F401
    _SOURCE = "adapters.ai_client"

__all__ = ["AIClient"]

def which_client() -> str:
    return _SOURCE
