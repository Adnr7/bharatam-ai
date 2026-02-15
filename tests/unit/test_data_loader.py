"""Unit tests for scheme data loader."""

import pytest
import json
from pathlib import Path
from app.services.data_loader import SchemeDataLoader, load_and_validate_schemes
from app.models.scheme import Scheme


def test_load_schemes_success():
    """Test successful loading of schemes from JSON file."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    
    assert isinstance(schemes, list)
    assert len(schemes) > 0
    assert all(isinstance(scheme, Scheme) for scheme in schemes)


def test_load_schemes_file_not_found():
    """Test error handling when scheme file doesn't exist."""
    loader = SchemeDataLoader("nonexistent.json")
    
    with pytest.raises(FileNotFoundError):
        loader.load_schemes()


def test_validate_schemes():
    """Test scheme validation and statistics generation."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    stats = loader.validate_schemes(schemes)
    
    assert "total_schemes" in stats
    assert stats["total_schemes"] == len(schemes)
    assert "schemes_with_translations" in stats
    assert "unique_categories" in stats
    assert "unique_occupations" in stats


def test_scheme_has_required_fields():
    """Test that all loaded schemes have required fields."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    
    for scheme in schemes:
        assert scheme.id
        assert scheme.name
        assert scheme.description
        assert scheme.eligibility
        assert scheme.benefits
        assert scheme.application_process
        assert scheme.source_url


def test_scheme_translations():
    """Test that schemes have Hindi translations."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    
    # At least some schemes should have Hindi translations
    schemes_with_hindi = [s for s in schemes if "hi" in s.name_translations]
    assert len(schemes_with_hindi) > 0


def test_eligibility_criteria_validation():
    """Test that eligibility criteria are properly structured."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    
    for scheme in schemes:
        eligibility = scheme.eligibility
        
        # Age validation
        if eligibility.min_age is not None:
            assert eligibility.min_age >= 0
        if eligibility.max_age is not None:
            assert eligibility.max_age >= 0
        if eligibility.min_age and eligibility.max_age:
            assert eligibility.min_age <= eligibility.max_age
        
        # Income validation
        if eligibility.income_max is not None:
            assert eligibility.income_max >= 0


def test_load_and_validate_convenience_function():
    """Test the convenience function for loading and validating."""
    schemes, stats = load_and_validate_schemes("data/schemes.json")
    
    assert isinstance(schemes, list)
    assert isinstance(stats, dict)
    assert len(schemes) == stats["total_schemes"]


def test_scheme_documents_list():
    """Test that required documents are properly listed."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    
    for scheme in schemes:
        assert isinstance(scheme.required_documents, list)
        # Most schemes should have at least Aadhar card
        if len(scheme.required_documents) > 0:
            assert any("Aadhar" in doc for doc in scheme.required_documents)


def test_scheme_urls():
    """Test that schemes have valid URL fields."""
    loader = SchemeDataLoader("data/schemes.json")
    schemes = loader.load_schemes()
    
    for scheme in schemes:
        # Source URL is required
        assert scheme.source_url
        assert scheme.source_url.startswith("http")
        
        # Application URL is optional but should be valid if present
        if scheme.application_url:
            assert scheme.application_url.startswith("http")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
