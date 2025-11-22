"""
Vector RAG Demo - Semantic Search with Embeddings

This demo shows how to use the enhanced RAG system with vector embeddings
for semantic similarity search.

Demonstrates:
- Vector embeddings with TetnusEmbeddingModel
- Entity indexing
- Semantic search vs keyword search
- Permission-aware retrieval
"""

from parquetframe.ai import (
    AIConfig,
    OllamaModel,
    SQLiteVectorStore,
    TetnusEmbeddingModel,
    VectorRagPipeline,
)


# Mock EntityStore for demo
class MockEntityStore:
    def __init__(self):
        self.data = {
            "projects": [
                {
                    "id": 1,
                    "name": "Skyline",
                    "description": "High-rise building construction in downtown",
                    "priority": "high",
                    "status": "active",
                },
                {
                    "id": 2,
                    "name": "Phoenix",
                    "description": "Renewable energy solar farm project",
                    "priority": "medium",
                    "status": "active",
                },
                {
                    "id": 3,
                    "name": "Aqua",
                    "description": "Water treatment plant modernization",
                    "priority": "high",
                    "status": "completed",
                },
            ],
            "documents": [
                {
                    "id": 101,
                    "title": "Q4 Financial Report",
                    "content": "Revenue increased by 25% quarter over quarter",
                    "project_id": 1,
                },
                {
                    "id": 102,
                    "title": "Architecture Specification",
                    "content": "Detailed technical design for solar panel installation",
                    "project_id": 2,
                },
            ],
        }
        # Mock permissions
        self.permissions = {
            "user:alice": {"projects", "documents"},
            "user:bob": {"projects"},  # Bob can't see documents
        }

    def get_all_entities(self, entity_name):
        """Get all entities for indexing (bypass permissions)."""
        return self.data.get(entity_name, [])

    def get_entities(self, entity_name, user_context, limit=5):
        """Permission-aware entity retrieval."""
        if entity_name not in self.permissions.get(user_context, set()):
            return []
        return self.data.get(entity_name, [])[:limit]

    def check(self, user_context, permission, obj):
        """Check if user has permission for object."""
        entity_name = obj.split(":")[0]
        return entity_name in self.permissions.get(user_context, set())


def main():
    print("=" * 70)
    print("Vector RAG Demo: Semantic Search with Embeddings")
    print("=" * 70)
    print()

    # Check if Ollama is available
    try:
        from parquetframe.ai import OLLAMA_AVAILABLE

        if not OLLAMA_AVAILABLE:
            print("❌ Ollama package not installed.")
            print("   Install with: pip install ollama")
            return
    except ImportError:
        print("❌ Ollama not available")
        return

    # Step 1: Setup components
    print("📋 Step 1: Setting up vector RAG components...")
    print()

    # LLM for generation
    try:
        llm = OllamaModel("llama2", temperature=0.7)
        print(f"✅ LLM: {llm.model_name}")
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("\\n   Make sure Ollama is running:")
        print("     ollama pull llama2")
        return

    # Embedding model
    try:
        embedding_model = TetnusEmbeddingModel(embedding_dim=384)
        print(f"✅ Embeddings: {embedding_model.model_name}")
    except ImportError:
        print("❌ Tetnus embeddings not available - ensure pf-py is built")
        return

    # Vector store
    vector_store = SQLiteVectorStore(":memory:", dimension=384)
    print(f"✅ Vector store: in-memory (dim={vector_store.dimension})")

    # Config
    config = AIConfig(
        models=[llm],
        default_generation_model="llama2",
        rag_enabled_entities={"projects", "documents"},
        retrieval_k=3,
    )
    print(f"✅ Config: retrieval_k={config.retrieval_k}")
    print()

    # Step 2: Create pipeline and index
    print("🤖 Step 2: Initializing vector RAG pipeline...")
    store = MockEntityStore()
    pipeline = VectorRagPipeline(config, store, vector_store, embedding_model)
    print("✅ Pipeline ready")
    print()

    print("📊 Step 3: Indexing entities...")
    pipeline.index_entities(["projects", "documents"])
    print(f"✅ Indexed {vector_store.count()} total chunks")
    print()

    # Step 4: Run queries
    print("=" * 70)
    print("Running Semantic Search Queries")
    print("=" * 70)
    print()

    queries = [
        ("Find construction projects", "user:alice"),
        ("Show me renewable energy initiatives", "user:alice"),
        ("What financial data do we have?", "user:alice"),
        ("Show me documents", "user:bob"),  # Bob has no access
    ]

    for i, (query, user) in enumerate(queries, 1):
        print(f'Query {i}: "{query}"')
        print(f"User: {user}")
        print("-" * 70)

        result = pipeline.run_query(query, user_context=user)

        print("✅ Response:")
        print(f"   {result['response_text']}")
        print()

        chunks = result.get("context_used", [])
        print(f"📦 Context: {len(chunks)} chunks retrieved")
        if chunks:
            for chunk in chunks:
                score = chunk.get("score", 0.0)
                entity_name = chunk.get("entity_name", "unknown")
                entity_id = chunk.get("entity_id", "?")
                print(f"   - {entity_name}:{entity_id} (similarity: {score:.3f})")
        print()

    # Comparison: Keyword vs Vector search
    print("=" * 70)
    print("Comparison: Semantic vs Keyword Matching")
    print("=" * 70)
    print()

    comparison_query = "renewable power generation"
    print(f'Query: "{comparison_query}"')
    print()

    # Vector search should find "Phoenix" (solar farm)
    # even though "renewable" and "power" aren't exact matches
    result = pipeline.run_query(comparison_query, user_context="user:alice")

    print("🎯 Semantic Search Results:")
    for chunk in result.get("context_used", []):
        print(f"  - {chunk['entity_name']}: {chunk.get('content', '')[:60]}...")
    print()

    print("💡 Key Features Demonstrated:")
    print("   ✅ Vector embeddings with TetnusEmbeddingModel")
    print("   ✅ Semantic similarity (not just keywords)")
    print("   ✅ Permission-aware filtering")
    print("   ✅ Hybrid retrieval (vector + keyword)")
    print("   ✅ Entity indexing workflow")
    print()

    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
