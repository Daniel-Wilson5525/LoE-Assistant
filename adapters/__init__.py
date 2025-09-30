# adapters/__init__.py
from .ai_client import AIClient as RealAIClient
from .mock_client import AIClient as MockAIClient

__all__ = ["RealAIClient", "MockAIClient"]
