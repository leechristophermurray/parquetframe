# feat(ai): Add Vector Embeddings and Semantic Search to RAG

## Summary

This PR enhances the existing RAG system with **vector embeddings** and **semantic search** capabilities, enabling natural language queries to find semantically similar results beyond simple keyword matching.

## What's New

### 🎯 Embedding Model Abstraction
- **3 embedding model implementations:**
  - `TetnusEmbeddingModel` - Leverages tetnus-llm embeddings (Phase 5)
  - `SentenceTransformerModel` - HuggingFace sentence-transformers support
  - `OllamaEmbeddingModel` - Ollama embedding endpoints
- Normalized embeddings for cosine similarity
- Batch embedding support

### 💾 Lightweight Vector Store
- **`SQLiteVectorStore`** - No heavy dependencies
- Cosine similarity search
- Entity filtering capabilities
- Batch operations for efficient indexing

### 🔍 Enhanced RAG Pipeline
- **`VectorRagPipeline`** extends `SimpleRagPipeline`
- **Hybrid retrieval:** Combines vector similarity + keyword matching
- Permission-aware filtering maintained
- Entity indexing workflow

## Key Features

✅ **Semantic Search** - Find "solar farm" when asking about "renewable energy"
✅ **Tetnus Integration** - Uses tetnus-llm embeddings from Phase 5
✅ **Permission-Aware** - All retrieval respects EntityStore permissions
✅ **Backward Compatible** - `SimpleRagPipeline` still available
✅ **Lightweight** - SQLite-based, no FAISS/ChromaDB required

## Code Changes

### New Files
- `src/parquetframe/ai/embeddings.py` (300+ lines) - Embedding models
- `src/parquetframe/ai/vector_store.py` (300+ lines) - Vector database
- `examples/rag_vector_demo.py` (200+ lines) - Demo example
- `tests/ai/test_vector_rag.py` (200+ lines) - Comprehensive tests

### Modified Files
- `src/parquetframe/ai/__init__.py` - Added exports
- `src/parquetframe/ai/rag_pipeline.py` - Added `VectorRagPipeline` (+250 lines)

**Total:** ~1,450 lines added

## Example Usage

```python
from parquetframe.ai import (
    AIConfig,
    OllamaModel,
    TetnusEmbeddingModel,
    SQLiteVectorStore,
    VectorRagPipeline
)

# Setup components
llm = OllamaModel("llama2")
embedding_model = TetnusEmbeddingModel(embedding_dim=384)
vector_store = SQLiteVectorStore(":memory:", dimension=384)

config = AIConfig(
    models=[llm],
    default_generation_model="llama2",
    rag_enabled_entities={"projects", "documents"},
    retrieval_k=3
)

# Create vector-enabled pipeline
pipeline = VectorRagPipeline(config, store, vector_store, embedding_model)

# Index entities (one-time setup)
pipeline.index_entities(["projects", "documents"])

# Query with semantic search!
result = pipeline.run_query(
    "renewable energy initiatives",  # Semantically finds "solar farm project"
    user_context="user:alice"
)
```

## Testing

### Run Tests
```bash
pytest tests/ai/test_vector_rag.py -v
```

### Run Demo
```bash
python examples/rag_vector_demo.py
```

**Test Coverage:**
- ✅ Embedding model initialization
- ✅ Single & batch embedding
- ✅ Vector normalization
- ✅ Vector store CRUD operations
- ✅ Cosine similarity search
- ✅ Entity filtering

## Architecture

```
User Query
    ↓
Parse Intent (keyword extraction)
    ↓
Embed Query (TetnusEmbeddingModel)
    ↓
Vector Search (SQLiteVectorStore) → Semantic candidates
    ↓
Permission Filter (EntityStore.check) → Authorized results
    ↓
Generate Response (OllamaModel/LLM)
    ↓
Return with context + citations
```

## Performance

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Single embed | O(n) | n = text length |
| Batch embed | O(m×n) | m = batch size |
| Vector search | O(k×d) | k = DB size, d = dims |
| Permission check | O(1) | Per chunk |

**Scalability:**
- Good for <100K vectors with SQLite
- For production scale: Migrate to FAISS, Milvus, or pgvector

## Integration with Tetnus

This feature builds on **Phases 4-6**:
- **Phase 5 (tetnus-llm):** Uses `Embedding` layer for vector generation
- **Phase 6 (tetnus-edge):** Future: Embed on Edge TPU
- **Phase 7a (workflow):** Future: RAG in ML pipelines

## Future Enhancements

- [ ] Better tokenization (BPE/WordPiece instead of char-level)
- [ ] LLM-based intent parsing (replace keyword extraction)
- [ ] Response citations (track source chunks)
- [ ] Query caching
- [ ] FAISS integration for production scale

## Backward Compatibility

✅ **Non-breaking changes**
- `SimpleRagPipeline` remains unchanged
- New `VectorRagPipeline` is opt-in
- All existing APIs maintained

## Dependencies

### Required (existing)
- `numpy` (already in deps)
- `sqlite3` (stdlib)

### Optional
- `sentence-transformers` (for SentenceTransformerModel)
- `ollama` (for OllamaEmbeddingModel)

## Checklist

- [x] Code compiles without errors
- [x] All tests passing
- [x] Pre-commit hooks satisfied
- [x] Demo example included
- [x] Documentation updated
- [x] Conventional commits used
- [x] Backward compatible

## Related Work

- **Previous:** #44 (Phases 4-6: GNNs, LLM, Edge AI) - Merged
- **Previous:** #45 (Phase 7a: Workflow stubs) - Merged
- **This PR:** RAG Vector Embeddings
- **Next:** Interactive Mode with Jupyter integration

---

**Review Notes:** This enhances the RAG system while maintaining full backward compatibility. The lightweight SQLite approach works well for MVP and can be swapped for FAISS/Milvus later if needed.
