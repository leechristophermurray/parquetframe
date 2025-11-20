"""
AI Configuration for RAG system.
"""

from dataclasses import dataclass, field

from .models import BaseLanguageModel

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant with access to a database.
Answer the user's query based ONLY on the context provided below.
If the context does not contain the answer, state that you cannot answer based on the available information.
Do not make up information. Be concise and accurate.

Context:
---
{context_str}
---
"""

DEFAULT_INTENT_PROMPT = """Extract key information from the user's query.
Identify:
1. Entity names they're asking about
2. Any filters or conditions
3. Query type (app_data or permission_data)

Available entities: {entity_names}

User Query: "{query}"

Respond with a JSON object.
"""


@dataclass
class AIConfig:
    """Configuration for AI/RAG features."""

    # Model configuration
    models: list[BaseLanguageModel]
    default_generation_model: str
    default_intent_model: str | None = None

    # RAG configuration
    rag_enabled_entities: set[str] = field(default_factory=set)

    # Prompt templates
    system_prompt_template: str = DEFAULT_SYSTEM_PROMPT
    intent_prompt_template: str = DEFAULT_INTENT_PROMPT

    # Retrieval parameters
    retrieval_k: int = 5  # Target number of context items

    # Response configuration
    enable_response_citation: bool = False  # Future feature

    def __post_init__(self):
        """Initialize defaults."""
        if not self.default_intent_model:
            self.default_intent_model = self.default_generation_model

        # Validate models exist
        self.get_model(self.default_generation_model)
        if self.default_intent_model:
            self.get_model(self.default_intent_model)

    def get_model(self, model_name: str | None = None) -> BaseLanguageModel:
        """
        Get model by name.

        Args:
            model_name: Model name, or None for default generation model

        Returns:
            BaseLanguageModel instance

        Raises:
            ValueError: If model not found
        """
        target_name = model_name or self.default_generation_model

        for model in self.models:
            if model.model_name == target_name:
                return model

        raise ValueError(
            f"Model '{target_name}' not registered in AIConfig. "
            f"Available models: {[m.model_name for m in self.models]}"
        )

    def get_intent_model(self) -> BaseLanguageModel:
        """Get the model used for intent parsing."""
        return self.get_model(self.default_intent_model)


__all__ = ["AIConfig", "DEFAULT_SYSTEM_PROMPT", "DEFAULT_INTENT_PROMPT"]
