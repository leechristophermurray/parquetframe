"""
Unit tests for Knowlogy.
"""

from unittest.mock import MagicMock, patch

import pytest

from parquetframe.knowlogy import Concept, Formula, KnowlogyEngine


class TestKnowlogyEngine:
    """Test Knowlogy engine."""

    @pytest.fixture
    def engine(self):
        return KnowlogyEngine()

    @patch("parquetframe.knowlogy.core.Concept.find_all")
    def test_search_concepts(self, mock_find_all, engine):
        """Test concept search."""
        # Mock concepts
        c1 = MagicMock(spec=Concept)
        c1.name = "Arithmetic Mean"
        c1.aliases = ["Average"]

        c2 = MagicMock(spec=Concept)
        c2.name = "Variance"
        c2.aliases = []

        # Setup mock to return all concepts
        mock_find_all.return_value = [c1, c2]

        # Search "mean"
        results = engine.search_concepts("mean")
        assert len(results) == 1
        assert results[0].name == "Arithmetic Mean"

        # Search "average" (alias)
        results = engine.search_concepts("average")
        assert len(results) == 1
        assert results[0].name == "Arithmetic Mean"

    @patch("parquetframe.knowlogy.core.Concept.find_all")
    def test_get_formula(self, mock_find_all, engine):
        """Test getting formula."""
        # Mock concept with formula
        c1 = MagicMock(spec=Concept)
        c1.name = "Mean"
        c1.aliases = []

        f1 = MagicMock(spec=Formula)
        f1.name = "Mean Formula"

        # Mock relationship
        mock_rel = MagicMock()
        mock_rel.execute.return_value = [f1]
        c1.formulas.return_value = mock_rel

        mock_find_all.return_value = [c1]

        formula = engine.get_formula("Mean")
        assert formula is not None
        assert formula.name == "Mean Formula"

    @patch("parquetframe.knowlogy.core.Concept.save")
    def test_add_concept(self, mock_save, engine):
        """Test adding concept."""
        c = engine.add_concept(
            id="test:c1", name="Test Concept", description="Desc", domain="Test"
        )
        assert c.id == "test:c1"
        mock_save.assert_called_once()
