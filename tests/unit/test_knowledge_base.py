"""
Unit tests for Knowledge Base and RAG system.

Tests semantic search, filtering, indexing, and persistence.

NOTE: These tests require sentence-transformers model to be downloaded.
On first run, the model (~70MB) will be downloaded automatically.
This may take a few minutes depending on your internet connection.

Requirements: 6.1, 6.2
"""

import pytest
import tempfile
import shutil
from pathlib import Path

# Skip tests if sentence-transformers is not available or model not downloaded
pytest.importorskip("sentence_transformers")

from app.services.knowledge_base import KnowledgeBase
from app.services.data_loader import load_and_validate_schemes
from app.models.scheme import Scheme, EligibilityCriteria


@pytest.fixture
def sample_schemes():
    """Create sample schemes for testing."""
    schemes = [
        Scheme(
            id="test-edu-1",
            name="Education Scholarship",
            name_hi="शिक्षा छात्रवृत्ति",
            description="Scholarship for students pursuing higher education",
            description_hi="उच्च शिक्षा प्राप्त करने वाले छात्रों के लिए छात्रवृत्ति",
            category="education",
            eligibility=EligibilityCriteria(
                min_age=18,
                max_age=25,
                state="Maharashtra",
                education_level="graduate"
            ),
            benefits="Financial assistance for tuition fees",
            benefits_hi="ट्यूशन फीस के लिए वित्तीय सहायता",
            required_documents=["Aadhar", "Income Certificate"],
            application_process="Apply online through portal",
            application_process_hi="पोर्टल के माध्यम से ऑनलाइन आवेदन करें",
            official_url="https://example.com/edu"
        ),
        Scheme(
            id="test-housing-1",
            name="Affordable Housing Scheme",
            name_hi="किफायती आवास योजना",
            description="Housing assistance for economically weaker sections",
            description_hi="आर्थिक रूप से कमजोर वर्गों के लिए आवास सहायता",
            category="housing",
            eligibility=EligibilityCriteria(
                income_range="0-1lakh",
                state="Maharashtra"
            ),
            benefits="Subsidized housing loans",
            benefits_hi="सब्सिडी वाले आवास ऋण",
            required_documents=["Aadhar", "Income Certificate"],
            application_process="Apply through bank",
            application_process_hi="बैंक के माध्यम से आवेदन करें",
            official_url="https://example.com/housing"
        ),
        Scheme(
            id="test-business-1",
            name="Women Entrepreneur Loan",
            name_hi="महिला उद्यमी ऋण",
            description="Business loans for women entrepreneurs",
            description_hi="महिला उद्यमियों के लिए व्यवसाय ऋण",
            category="entrepreneurship",
            eligibility=EligibilityCriteria(
                gender="female",
                min_age=18
            ),
            benefits="Low-interest business loans",
            benefits_hi="कम ब्याज वाले व्यवसाय ऋण",
            required_documents=["Aadhar", "Business Plan"],
            application_process="Apply through MUDRA portal",
            application_process_hi="मुद्रा पोर्टल के माध्यम से आवेदन करें",
            official_url="https://example.com/business"
        )
    ]
    return schemes


@pytest.fixture
def kb_with_schemes(sample_schemes):
    """Create knowledge base with indexed schemes."""
    kb = KnowledgeBase()
    kb.index_schemes(sample_schemes)
    return kb



class TestKnowledgeBaseInitialization:
    """Test knowledge base initialization."""
    
    def test_init_creates_empty_kb(self):
        """Test that initialization creates an empty knowledge base."""
        kb = KnowledgeBase()
        assert kb.schemes == []
        assert kb.index.ntotal == 0
        assert kb.embedding_dim > 0
    
    def test_init_with_custom_model(self):
        """Test initialization with custom model name."""
        kb = KnowledgeBase(model_name="sentence-transformers/paraphrase-MiniLM-L3-v2")
        assert kb.embedding_dim == 384  # Known dimension for MiniLM models


class TestSchemeIndexing:
    """Test scheme indexing functionality."""
    
    def test_index_schemes_success(self, sample_schemes):
        """Test successful scheme indexing."""
        kb = KnowledgeBase()
        kb.index_schemes(sample_schemes)
        
        assert len(kb.schemes) == 3
        assert kb.index.ntotal == 3
    
    def test_index_empty_schemes_raises_error(self):
        """Test that indexing empty list raises error."""
        kb = KnowledgeBase()
        with pytest.raises(ValueError, match="Cannot index empty scheme list"):
            kb.index_schemes([])
    
    def test_reindex_replaces_old_data(self, sample_schemes):
        """Test that re-indexing replaces old data."""
        kb = KnowledgeBase()
        kb.index_schemes(sample_schemes)
        
        # Re-index with fewer schemes
        kb.index_schemes(sample_schemes[:2])
        
        assert len(kb.schemes) == 2
        assert kb.index.ntotal == 2


class TestSemanticSearch:
    """Test semantic search functionality."""
    
    def test_retrieve_education_schemes(self, kb_with_schemes):
        """Test retrieving education-related schemes."""
        results = kb_with_schemes.retrieve_schemes("scholarship for students", top_k=2)
        
        assert len(results) > 0
        # Education scheme should be most relevant
        assert results[0][0].category == "education"
        # Check similarity score is reasonable
        assert 0 < results[0][1] <= 1.0
    
    def test_retrieve_housing_schemes(self, kb_with_schemes):
        """Test retrieving housing-related schemes."""
        results = kb_with_schemes.retrieve_schemes("affordable housing for poor families", top_k=2)
        
        assert len(results) > 0
        assert results[0][0].category == "housing"
    
    def test_retrieve_business_schemes(self, kb_with_schemes):
        """Test retrieving business-related schemes."""
        results = kb_with_schemes.retrieve_schemes("business loan for women", top_k=2)
        
        assert len(results) > 0
        assert results[0][0].category == "entrepreneurship"
    
    def test_retrieve_returns_top_k_results(self, kb_with_schemes):
        """Test that retrieve returns correct number of results."""
        results = kb_with_schemes.retrieve_schemes("government scheme", top_k=2)
        
        assert len(results) <= 2
    
    def test_retrieve_from_empty_kb(self):
        """Test retrieval from empty knowledge base."""
        kb = KnowledgeBase()
        results = kb.retrieve_schemes("test query", top_k=5)
        
        assert results == []


class TestFiltering:
    """Test metadata filtering functionality."""
    
    def test_filter_by_state(self, kb_with_schemes):
        """Test filtering schemes by state."""
        results = kb_with_schemes.retrieve_schemes(
            "government scheme",
            top_k=5,
            filters={"state": "Maharashtra"}
        )
        
        # All results should be for Maharashtra or have no state restriction
        for scheme, _ in results:
            if scheme.eligibility.state:
                assert scheme.eligibility.state.lower() == "maharashtra"
    
    def test_filter_by_category(self, kb_with_schemes):
        """Test filtering schemes by category."""
        results = kb_with_schemes.retrieve_schemes(
            "help me",
            top_k=5,
            filters={"category": "education"}
        )
        
        assert len(results) > 0
        for scheme, _ in results:
            assert scheme.category == "education"
    
    def test_filter_by_multiple_criteria(self, kb_with_schemes):
        """Test filtering with multiple criteria."""
        results = kb_with_schemes.retrieve_schemes(
            "scheme",
            top_k=5,
            filters={"state": "Maharashtra", "category": "housing"}
        )
        
        assert len(results) > 0
        for scheme, _ in results:
            assert scheme.category == "housing"
            if scheme.eligibility.state:
                assert scheme.eligibility.state.lower() == "maharashtra"
    
    def test_filter_no_matches(self, kb_with_schemes):
        """Test filtering with no matching schemes."""
        results = kb_with_schemes.retrieve_schemes(
            "scheme",
            top_k=5,
            filters={"state": "NonExistentState"}
        )
        
        # Should return empty or only schemes with no state restriction
        assert len(results) == 0 or all(s.eligibility.state is None for s, _ in results)



class TestPersistence:
    """Test index saving and loading."""
    
    def test_save_and_load_index(self, kb_with_schemes):
        """Test saving and loading FAISS index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_path = Path(tmpdir) / "test_index"
            kb_with_schemes.index_path = str(index_path)
            
            # Save index
            kb_with_schemes.save_index()
            
            # Create new KB and load
            new_kb = KnowledgeBase()
            new_kb.index_path = str(index_path)
            success = new_kb.load_index()
            
            assert success
            assert len(new_kb.schemes) == 3
            assert new_kb.index.ntotal == 3
    
    def test_load_nonexistent_index(self):
        """Test loading from nonexistent path."""
        kb = KnowledgeBase()
        kb.index_path = "/nonexistent/path/index"
        success = kb.load_index()
        
        assert not success


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_get_scheme_by_id(self, kb_with_schemes):
        """Test retrieving scheme by ID."""
        scheme = kb_with_schemes.get_scheme_by_id("test-edu-1")
        
        assert scheme is not None
        assert scheme.name == "Education Scholarship"
    
    def test_get_scheme_by_invalid_id(self, kb_with_schemes):
        """Test retrieving scheme with invalid ID."""
        scheme = kb_with_schemes.get_scheme_by_id("nonexistent-id")
        
        assert scheme is None
    
    def test_get_all_schemes(self, kb_with_schemes):
        """Test getting all schemes."""
        schemes = kb_with_schemes.get_all_schemes()
        
        assert len(schemes) == 3
        # Should return a copy, not the original list
        schemes.append(None)
        assert len(kb_with_schemes.schemes) == 3
    
    def test_get_stats(self, kb_with_schemes):
        """Test getting knowledge base statistics."""
        stats = kb_with_schemes.get_stats()
        
        assert stats["total_schemes"] == 3
        assert stats["embedding_dimension"] > 0
        assert stats["indexed"] is True
    
    def test_get_stats_empty_kb(self):
        """Test getting stats from empty knowledge base."""
        kb = KnowledgeBase()
        stats = kb.get_stats()
        
        assert stats["total_schemes"] == 0
        assert stats["indexed"] is False


class TestRealSchemes:
    """Test with real scheme data."""
    
    def test_index_real_schemes(self):
        """Test indexing real schemes from JSON."""
        schemes, _ = load_and_validate_schemes()
        
        kb = KnowledgeBase()
        kb.index_schemes(schemes)
        
        assert len(kb.schemes) == len(schemes)
        assert kb.index.ntotal == len(schemes)
    
    def test_search_real_schemes(self):
        """Test semantic search on real schemes."""
        schemes, _ = load_and_validate_schemes()
        
        kb = KnowledgeBase()
        kb.index_schemes(schemes)
        
        # Test various queries
        queries = [
            "skill development training",
            "housing for poor families",
            "pension scheme for elderly",
            "business loan for small enterprises"
        ]
        
        for query in queries:
            results = kb.retrieve_schemes(query, top_k=3)
            assert len(results) > 0
            # Check that results have valid similarity scores
            for scheme, score in results:
                assert 0 < score <= 1.0
                assert isinstance(scheme, Scheme)
