"""
Knowlogy-Grounded RAG Example

Demonstrates RAG with Knowlogy integration for formula-grounded responses.
"""

from parquetframe.ai import AIConfig, SimpleRagPipeline
from parquetframe.ai.grounding import ground_response
from parquetframe.ai.models import OllamaModel


def main():
    """Run Knowlogy-grounded RAG demo."""
    print("=" * 60)
    print("Knowlogy-Grounded RAG Example")
    print("=" * 60)

    # Configure AI with local model
    try:
        model = OllamaModel("llama2", host="http://localhost:11434")
    except ImportError:
        print("\n⚠️  Ollama not installed. Install with: pip install ollama")
        print("Or use a different model provider.\n")
        return

    config = AIConfig(
        models=[model],
        default_generation_model="llama2",
        rag_enabled_entities=set(),  # No entity retrieval for this demo
    )

    # Create RAG pipeline with Knowlogy enabled
    pipeline = SimpleRagPipeline(
        config=config,
        entity_store=None,  # No entity store needed for Knowlogy-only demo
        use_knowlogy=True,
    )

    # Example queries
    queries = [
        "What is variance and how do I calculate it?",
        "Explain the t-test formula",
        "What is Newton's Second Law?",
        "How do I calculate the Sharpe Ratio?",
    ]

    print("\n" + "=" * 60)
    print("Running Queries with Knowlogy Integration")
    print("=" * 60 + "\n")

    for i, query in enumerate(queries, 1):
        print(f"\n[Query {i}]: {query}")
        print("-" * 60)

        # Run query
        result = pipeline.run_query(query, user_context="demo:user")

        # Show response
        print(f"\n📝 Response:\n{result['response_text']}\n")

        # Show Knowlogy sources
        knowlogy_sources = [
            ctx
            for ctx in result.get("context_used", [])
            if ctx.get("source") == "knowlogy"
        ]

        if knowlogy_sources:
            print(f"📚 Knowlogy Sources ({len(knowlogy_sources)}):")
            for source in knowlogy_sources:
                metadata = source.get("metadata", {})
                print(f"  - {metadata.get('concept_name')} ({metadata.get('domain')})")

        # Ground the response
        grounding_result = ground_response(query, result["response_text"])
        verification = grounding_result["formula_verification"]

        if verification["num_formulas"] > 0:
            print("\n🔬 Formula Verification:")
            print(f"  Found {verification['num_formulas']} formula(s)")
            for formula in verification["formulas_found"]:
                print(f"  - {formula}")

        print("\n" + "=" * 60)

    print("\n✅ Demo complete!")
    print("\nNote: This example requires:")
    print("  1. Ollama running locally (or another LLM)")
    print("  2. Knowlogy statistics library loaded")
    print("  3. Run: parquetframe.knowlogy.load_library('statistics')")


if __name__ == "__main__":
    main()
