"""
Tests for RAG vector embeddings and search.

Tests cover:
- Embedding models (Tetnus, SentenceTransformer, Ollama)
- Vector store operations
- Vector RAG pipeline
- Permission enforcement
"""

import numpy as np
import pytest

from parquetframe.ai import (
    SQLiteVectorStore,
    TetnusEmbeddingModel,
)

try:
    import importlib.util

    if importlib.util.find_spec("parquetframe._rustic.tetnus.Embedding"):
        TETNUS_AVAILABLE = True
except ImportError:
    TETNUS_AVAILABLE = False


@pytest.mark.skipif(not TETNUS_AVAILABLE, reason="Tetnus module not available")
class TestTetnusEmbeddingModel:
    """Test tetnus embedding model."""

    def test_initialization(self):
        """Test model initialization."""
        model = TetnusEmbeddingModel(embedding_dim=128)
        assert model.dimension == 128
        assert "tetnus" in model.model_name.lower()

    def test_single_embed(self):
        """Test embedding single text."""
        model = TetnusEmbeddingModel(embedding_dim=128)
        embedding = model.embed("hello world")

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (128,)
        assert not np.isnan(embedding).any()

    def test_batch_embed(self):
        """Test batch embedding."""
        model = TetnusEmbeddingModel(embedding_dim=128)
        texts = ["hello", "world", "test"]
        embeddings = model.embed_batch(texts)

        assert embeddings.shape == (3, 128)
        assert not np.isnan(embeddings).any()

    def test_normalized_embeddings(self):
        """Test embeddings are normalized."""
        model = TetnusEmbeddingModel(embedding_dim=128)
        embedding = model.embed("test text")

        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, atol=1e-6)


class TestSQLiteVectorStore:
    """Test SQLite vector store."""

    def test_initialization(self):
        """Test store initialization."""
        store = SQLiteVectorStore(":memory:", dimension=128)
        assert store.dimension == 128
        assert store.count() == 0

    def test_add_single(self):
        """Test adding single embedding."""
        store = SQLiteVectorStore(":memory:", dimension=128)
        vector = np.random.randn(128).astype(np.float32)

        store.add(
            chunk_id="test:1",
            vector=vector,
            entity_name="test",
            entity_id="1",
            content="test content",
        )

        assert store.count() == 1

    def test_add_batch(self):
        """Test batch add."""
        store = SQLiteVectorStore(":memory:", dimension=128)

        chunks = [
            {
                "chunk_id": f"test:{i}",
                "vector": np.random.randn(128).astype(np.float32),
                "entity_name": "test",
                "entity_id": str(i),
                "content": f"content {i}",
            }
            for i in range(5)
        ]

        store.add_batch(chunks)
        assert store.count() == 5

    def test_search(self):
        """Test vector search."""
        store = SQLiteVectorStore(":memory:", dimension=128)

        # Add some vectors - use deterministic seed for reliable test
        np.random.seed(42)
        vectors = [np.random.randn(128).astype(np.float32) for _ in range(5)]
        # Normalize vectors for consistent similarity scores
        vectors = [v / np.linalg.norm(v) for v in vectors]
        for i, vec in enumerate(vectors):
            store.add(
                chunk_id=f"test:{i}",
                vector=vec,
                entity_name="test",
                entity_id=str(i),
                content=f"content {i}",
            )

        # Search with first vector (should be top result)
        # Use negative threshold to ensure we get results even with low similarity
        results = store.search(vectors[0], top_k=3, score_threshold=-1.0)

        assert len(results) == 3
        assert results[0][0] == "test:0"  # Should find itself
        assert results[0][1] >= 0.99  # Almost 1.0 similarity

    def test_get_by_chunk_id(self):
        """Test retrieving by chunk ID."""
        store = SQLiteVectorStore(":memory:", dimension=128)
        vector = np.random.randn(128).astype(np.float32)

        store.add(
            chunk_id="test:1",
            vector=vector,
            entity_name="test",
            entity_id="1",
            content="test content",
        )

        chunk = store.get_by_chunk_id("test:1")
        assert chunk is not None
        assert chunk["chunk_id"] == "test:1"
        assert chunk["content"] == "test content"

    def test_delete(self):
        """Test deleting chunks."""
        store = SQLiteVectorStore(":memory:", dimension=128)

        # Add some vectors
        for i in range(3):
            store.add(
                chunk_id=f"test:{i}",
                vector=np.random.randn(128).astype(np.float32),
                entity_name="test",
                entity_id=str(i),
                content=f"content {i}",
            )

        assert store.count() == 3

        # Delete one
        deleted = store.delete("test:1")
        assert deleted is True
        assert store.count() == 2

    def test_entity_filter_search(self):
        """Test filtering by entity."""
        store = SQLiteVectorStore(":memory:", dimension=128)

        # Add mixed entities
        for i in range(3):
            store.add(
                chunk_id=f"projects:{i}",
                vector=np.random.randn(128).astype(np.float32),
                entity_name="projects",
                entity_id=str(i),
                content=f"project {i}",
            )
            store.add(
                chunk_id=f"documents:{i}",
                vector=np.random.randn(128).astype(np.float32),
                entity_name="documents",
                entity_id=str(i),
                content=f"document {i}",
            )

        assert store.count() == 6

        # Search only projects
        query = np.random.randn(128).astype(np.float32)
        results = store.search(
            query, top_k=10, entity_filter="projects", score_threshold=-1.0
        )
        assert len(results) == 3
        assert all("projects:" in r[0] for r in results)
        assert all("projects:" in r[0] for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
