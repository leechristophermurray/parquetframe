"""
Simple RAG Pipeline for permission-aware querying.

This module provides a simplified RAG implementation that uses
keyword-based intent parsing and EntityStore for retrieval.
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional

from .config import AIConfig
from .models import BaseLanguageModel

logger = logging.getLogger(__name__)


class SimpleRagPipeline:
    """Simplified RAG pipeline using keyword-based retrieval."""

    def __init__(self, config: AIConfig, entity_store: Any):
        """
        Initialize RAG pipeline.
        
        Args:
            config: AIConfig with model and prompt configuration
            entity_store: EntityStore instance for data retrieval
        """
        self.config = config
        self.entity_store = entity_store
        self.generation_model = config.get_model()

    def run_query(self, query: str, user_context: str) -> Dict[str, Any]:
        """
        Run end-to-end RAG query.
        
        Args:
            query: Natural language query
            user_context: User ID for permission checks (e.g., "user:alice")
        
        Returns:
            Dict with response_text, context_used, and metadata
        """
        logger.info(f"Running RAG query for user: {user_context}")
        
        try:
            # Step 1: Parse intent (simplified keyword extraction)
            intent = self._parse_intent(query)
            logger.debug(f"Parsed intent: {intent}")
            
            # Step 2: Retrieve authorized context
            context_chunks = self._retrieve_authorized_context(
                intent, user_context
            )
            logger.debug(f"Retrieved {len(context_chunks)} context chunks")
            
            # Step 3: Augment and generate
            response_text = self._generate_response(query, context_chunks)
            
            return {
                "response_text": response_text,
                "context_used": context_chunks,
                "intent": intent,
                "user_context": user_context,
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                "response_text": f"Error processing query: {str(e)}",
                "context_used": [],
                "intent": {},
                "error": str(e),
            }

    def _parse_intent(self, query: str) -> Dict[str, Any]:
        """
        Simple keyword-based intent parsing.
        
        Extracts:
        - Entity names mentioned
        - Filter keywords (high, low, priority, status, etc.)
        
        Args:
            query: Natural language query
        
        Returns:
            Dict with extracted intent
        """
        intent = {
            "entities": [],
            "filters": {},
            "keywords": [],
        }
        
        # Extract entity names from enabled entities
        query_lower = query.lower()
        for entity_name in self.config.rag_enabled_entities:
            # Check singular and plural forms
            if entity_name.lower() in query_lower or entity_name[:-1].lower() in query_lower:
                intent["entities"].append(entity_name)
        
        # Extract common filter keywords
        priority_match = re.search(r'\b(high|low|medium)\s+priority\b', query_lower)
        if priority_match:
            intent["filters"]["priority"] = priority_match.group(1)
        
        status_match = re.search(r'\b(active|inactive|completed|pending)\b', query_lower)
        if status_match:
            intent["filters"]["status"] = status_match.group(1)
        
        # Extract general keywords (words longer than 3 chars, not stopwords)
        stopwords = {'what', 'when', 'where', 'which', 'show', 'list', 'get', 'find', 'the', 'are'}
        words = re.findall(r'\b\w{4,}\b', query_lower)
        intent["keywords"] = [w for w in words if w not in stopwords]
        
        return intent

    def _retrieve_authorized_context(
        self, intent: Dict[str, Any], user_context: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve permission-aware context from EntityStore.
        
        Args:
            intent: Parsed intent dict
            user_context: User ID for permissions
        
        Returns:
            List of entity data dicts
        """
        context_chunks = []
        
        # Query each entity type mentioned
        for entity_name in intent["entities"]:
            try:
                # Use EntityStore's permission-aware get_entities
                # This automatically filters by user permissions
                entities = self.entity_store.get_entities(
                    entity_name=entity_name,
                    user_context=user_context,
                    limit=self.config.retrieval_k
                )
                
                # Apply filter keywords if any
                if intent["filters"]:
                    entities = self._apply_filters(entities, intent["filters"])
                
                # Convert to context format
                for entity in entities:
                    context_chunks.append({
                        "entity_name": entity_name,
                        "entity_id": entity.get("id", "unknown"),
                        "data": entity,
                    })
                
            except Exception as e:
                logger.warning(f"Failed to retrieve {entity_name}: {e}")
        
        # Limit to retrieval_k total
        return context_chunks[:self.config.retrieval_k]

    def _apply_filters(
        self, entities: List[Dict], filters: Dict[str, str]
    ) -> List[Dict]:
        """Apply simple field-based filters to entities."""
        filtered = []
        
        for entity in entities:
            match = True
            for field, value in filters.items():
                entity_value = entity.get(field, "").lower()
                if value.lower() not in entity_value:
                    match = False
                    break
            if match:
                filtered.append(entity)
        
        return filtered

    def _generate_response(
        self, query: str, context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Generate LLM response with context.
        
        Args:
            query: User query
            context_chunks: Retrieved context
        
        Returns:
            Generated response text
        """
        # Build context string
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            entity_name = chunk["entity_name"]
            data = chunk["data"]
            context_parts.append(
                f"[{i}] {entity_name}: {json.dumps(data, indent=2)}"
            )
        
        context_str = "\n\n".join(context_parts) if context_parts else "No relevant data found."
        
        # Build system prompt
        system_prompt = self.config.system_prompt_template.format(
            context_str=context_str
        )
        
        # Generate response
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        
        try:
            response = self.generation_model.generate(messages)
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Error generating response: {str(e)}"


__all__ = ["SimpleRagPipeline"]
