"""
AI module for Retrieval-Augmented Generation (RAG).

Provides permission-aware querying over EntityStore using LLMs.
"""

# Keep existing LLM agent for backwards compatibility
from .agent import LLMAgent, LLMError, QueryResult
from .config import AIConfig
from .models import OLLAMA_AVAILABLE, BaseLanguageModel, OllamaModel
from .rag_pipeline import SimpleRagPipeline

__all__ = [
    "BaseLanguageModel",
    "OllamaModel",
    "OLLAMA_AVAILABLE",
    "AIConfig",
    "SimpleRagPipeline",
    # Legacy exports
    "LLMAgent",
    "LLMError",
    "QueryResult",
]
