"""
RAG Demo - Permission-Aware Querying

This demo shows how to use the RAG system with Ollama for
natural language querying over structured data.

NOTE: This simplified demo doesn't include full EntityStore integration
with Zanzibar permissions. It demonstrates the RAG pipeline using mock data.
"""

from parquetframe.ai import AIConfig, OllamaModel, SimpleRagPipeline


# Mock EntityStore for demo (simulates permission-aware retrieval)
class MockEntityStore:
    def __init__(self):
        self.data = {
            "projects": [
                {"id": 1, "name": "Skyline", "priority": "high", "status": "active"},
                {"id": 2, "name": "Phoenix", "priority": "medium", "status": "active"},
                {"id": 3, "name": "Titan", "priority": "high", "status": "completed"},
            ],
            "documents": [
                {"id": 101, "title": "Q4 Report", "project_id": 1},
                {"id": 102, "title": "Architecture Doc", "project_id": 1},
            ],
        }
        # Mock user permissions
        self.permissions = {
            "user:alice": {"projects", "documents"},
            "user:bob": {"projects"},  # Bob can't see documents
        }

    def get_entities(self, entity_name, user_context, limit=5):
        """Simulate permission-aware entity retrieval."""
        # Check permissions
        if entity_name not in self.permissions.get(user_context, set()):
            return []

        # Return data (in real system, this checks Zanzibar)
        return self.data.get(entity_name, [])[:limit]


def main():
    print("=" * 60)
    print("RAG Demo: Permission-Aware Querying with Ollama")
    print("=" * 60)
    print()

    # Check if Ollama is available
    try:
        from parquetframe.ai import OLLAMA_AVAILABLE

        if not OLLAMA_AVAILABLE:
            print("❌ Ollama package not installed.")
            print("   Install with:  pip install ollama")
            return
    except ImportError:
        print("❌ Ollama not available")
        return

    # Step 1: Configure AI
    print("📋 Step 1: Configuring RAG system...")
    print()

    try:
        model = OllamaModel("llama2", temperature=0.7)
        config = AIConfig(
            models=[model],
            default_generation_model="llama2",
            rag_enabled_entities={"projects", "documents"},
            retrieval_k=3,
        )
        print("✅ Configuration complete")
        print(f"   Model: {model.model_name}")
        print(f"   Enabled entities: {config.rag_enabled_entities}")
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("\n   Make sure Ollama is running and llama2 is pulled:")
        print("     ollama pull llama2")
        return

    print()

    # Step 2: Setup mock entity store
    print("📊 Step 2: Setting up entity store (mock)...")
    store = MockEntityStore()
    print(f"✅ Loaded {len(store.data)} entity types")
    print()

    # Step 3: Create RAG pipeline
    print("🤖 Step 3: Initializing RAG pipeline...")
    pipeline = SimpleRagPipeline(config, store)
    print("✅ Pipeline ready")
    print()

    # Step 4: Run queries
    print("=" * 60)
    print("Running Sample Queries")
    print("=" * 60)
    print()

    queries = [
        ("What are the high priority projects?", "user:alice"),
        ("List all active projects", "user:alice"),
        ("Show me the documents", "user:bob"),  # Bob has no doc access
    ]

    for i, (query, user) in enumerate(queries, 1):
        print(f'Query {i}: "{query}"')
        print(f"User: {user}")
        print("-" * 60)

        result = pipeline.run_query(query, user_context=user)

        print("✅ Response:")
        print(f"   {result['response_text']}")
        print()
        print(f"📦 Context used: {len(result['context_used'])} chunks")
        if result["context_used"]:
            for chunk in result["context_used"]:
                print(f"   - {chunk['entity_name']}: {chunk['entity_id']}")
        print()

    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("💡 Key Features Demonstrated:")
    print("   • Model abstraction (OllamaModel)")
    print("   • AIConfig for configuration")
    print("   • Permission-aware retrieval")
    print("   • Natural language query → LLM response")
    print()
    print("🔮 Future Enhancements:")
    print("   • Vector embeddings for similarity search")
    print("   • Full Zanzibar permission integration")
    print("   • Response citations")
    print("   • LLM-based intent parsing")


if __name__ == "__main__":
    main()
