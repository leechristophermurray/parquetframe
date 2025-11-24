# RAG System with Knowlogy Integration

ParquetFrame's RAG (Retrieval-Augmented Generation) system provides intelligent query answering with formula grounding through Knowlogy integration.

## Overview

The enhanced RAG system combines:
- **Permission-aware retrieval** from entity data
- **Knowledge graph integration** via Knowlogy
- **Formula verification** for accuracy
- **LLM generation** for natural language responses

## Quick Start

```python
from parquetframe.ai import AIConfig, SimpleRagPipeline
from parquetframe.ai.models import OllamaModel

# Configure AI
model = OllamaModel("llama2")
config = AIConfig(
    models=[model],
    default_generation_model="llama2"
)

# Create RAG pipeline with Knowlogy
pipeline = SimpleRagPipeline(
    config=config,
    entity_store=your_store,
    use_knowlogy=True
)

# Query with formula grounding
result = pipeline.run_query(
    "How do I calculate variance?",
    user_context="user:alice"
)

print(result['response_text'])
```

## Knowlogy Integration

### What is Knowlogy?

Knowlogy is ParquetFrame's computable knowledge graph containing:
- Formal concept definitions
- Mathematical formulas (LaTeX + symbolic)
- Domain knowledge (Statistics, Physics, Finance)

### Benefits

1. **Formula Grounding**: LLM responses include verified formulas
2. **Accurate Definitions**: Concepts come from curated knowledge
3. **Citation**: Responses cite knowledge sources
4. **Verification**: Formulas can be validated post-generation

### How It Works

```
User Query → Intent Parsing → Dual Retrieval → Generation
                                    ↓
                         ┌──────────┴──────────┐
                         │                     │
                    Entity Store          Knowlogy
                    (Your Data)         (Formulas)
                         │                     │
                         └──────────┬──────────┘
                                    ↓
                             Merged Context
                                    ↓
                                  LLM
```

## Formula Verification

### Extract Formulas

```python
from parquetframe.ai.grounding import extract_formulas

text = "The variance is $\\sigma^2 = E[(X - \\mu)^2]$"
formulas = extract_formulas(text)
# ['\\sigma^2 = E[(X - \\mu)^2]']
```

### Ground Responses

```python
from parquetframe.ai.grounding import ground_response

result = ground_response(
    query="What is variance?",
    response=llm_response_text
)

# Returns:
# {
#     "original_response": "...",
#     "knowledge_sources": [...],
#     "formula_verification": {...}
# }
```

## Examples

### Basic Usage

See [`examples/rag/knowlogy_grounded.py`](../../examples/rag/knowlogy_grounded.py) for a complete example.

### With OpenAI

```python
from openai import OpenAI

class OpenAIModel(BaseLanguageModel):
    def __init__(self, model_name="gpt-4"):
        self.client = OpenAI()
        self.model = model_name
    
    def generate(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content
```

## API Reference

### KnowlogyRetriever

```python
from parquetframe.ai.knowlogy_retriever import KnowlogyRetriever

retriever = KnowlogyRetriever()
docs = retriever.retrieve("variance", top_k=5)
```

### SimpleRagPipeline

```python
pipeline = SimpleRagPipeline(
    config: AIConfig,
    entity_store: EntityStore,
    use_knowlogy: bool = False
)

result = pipeline.run_query(query: str, user_context: str)
```

## Best Practices

1. **Load Libraries**: Ensure Knowlogy libraries are loaded
   ```python
   from parquetframe import knowlogy
   knowlogy.load_library("statistics")
   knowlogy.load_library("physics")
   ```

2. **Verify Responses**: Use `ground_response()` for critical applications

3. **Cite Sources**: Enable citations in `AIConfig` for transparency

4. **Test Queries**: Build a test suite of expected query/response pairs
