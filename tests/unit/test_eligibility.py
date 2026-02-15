"""Unit tests for eligibility determination engine."""

import pytest
from app.services.eligibility import EligibilityEngine
from app.models.user import UserProfile
from app.models.scheme import Scheme, EligibilityCriteria


@pytest.fixture
def eligibility_engine():
    """Create an eligibility engine instance."""
    return EligibilityEngine()


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile."""
    return UserProfile(
        age=25,
        state="Maharashtra",
        education_level="graduate",
        income_range="1-3lakh",
        category="general",
        gender="male",
        occupation="student"
    )


@pytest.fixture
def sample_scheme():
    """Create a sample scheme."""
    return Scheme(
        id="test-scheme-1",
        name="Test Scholarship Scheme",
        name_translations={"hi": "परीक्षण छात्रवृत्ति योजना"},
        description="A test scholarship scheme for students",
        description_translations={"hi": "छात्रों के लिए एक परीक्षण छात्रवृत्ति योजना"},
        eligibility=EligibilityCriteria(
            min_age=18,
            max_age=30,
            states=["Maharashtra", "Karnataka"],
            education_levels=["graduate", "postgraduate"],
            income_max=500000,
            categories=None,
            gender=None,
            occupations=["student"]
        ),
        benefits="Free education and stipend",
        required_documents=["Aadhar", "Income Certificate"],
        application_process="Apply online",
        application_url="https://example.com",
        office_location="District Office",
        deadline=None,
        source_url="https://example.com",
        last_updated="2024-01-01T00:00:00"
    )


def test_check_single_scheme_eligible(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check for an eligible user."""
    result = eligibility_engine.check_single_scheme(sample_user_profile, sample_scheme)
    
    assert result.is_eligible is True
    assert len(result.matching_criteria) > 0
    assert len(result.missing_criteria) == 0
    assert result.confidence > 0.9
    assert "eligible" in result.explanation.lower()


def test_check_single_scheme_age_too_young(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when user is too young."""
    young_user = sample_user_profile.model_copy()
    young_user.age = 15
    
    result = eligibility_engine.check_single_scheme(young_user, sample_scheme)
    
    assert result.is_eligible is False
    assert any("age" in criterion.lower() for criterion in result.missing_criteria)


def test_check_single_scheme_age_too_old(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when user is too old."""
    old_user = sample_user_profile.model_copy()
    old_user.age = 35
    
    result = eligibility_engine.check_single_scheme(old_user, sample_scheme)
    
    assert result.is_eligible is False
    assert any("age" in criterion.lower() for criterion in result.missing_criteria)


def test_check_single_scheme_wrong_state(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when user is from wrong state."""
    wrong_state_user = sample_user_profile.model_copy()
    wrong_state_user.state = "Delhi"
    
    result = eligibility_engine.check_single_scheme(wrong_state_user, sample_scheme)
    
    assert result.is_eligible is False
    assert any("state" in criterion.lower() or "Maharashtra" in criterion for criterion in result.missing_criteria)


def test_check_single_scheme_wrong_education(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when user has wrong education level."""
    wrong_edu_user = sample_user_profile.model_copy()
    wrong_edu_user.education_level = "10th_pass"
    
    result = eligibility_engine.check_single_scheme(wrong_edu_user, sample_scheme)
    
    assert result.is_eligible is False
    assert any("education" in criterion.lower() for criterion in result.missing_criteria)


def test_check_single_scheme_income_too_high(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when user income is too high."""
    high_income_user = sample_user_profile.model_copy()
    high_income_user.income_range = "above_8lakh"
    
    result = eligibility_engine.check_single_scheme(high_income_user, sample_scheme)
    
    assert result.is_eligible is False
    assert any("income" in criterion.lower() for criterion in result.missing_criteria)


def test_check_single_scheme_wrong_occupation(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when user has wrong occupation."""
    wrong_occ_user = sample_user_profile.model_copy()
    wrong_occ_user.occupation = "farmer"
    
    result = eligibility_engine.check_single_scheme(wrong_occ_user, sample_scheme)
    
    assert result.is_eligible is False
    # Check that the missing criteria mentions the required occupation
    assert any("student" in criterion.lower() for criterion in result.missing_criteria)


def test_check_single_scheme_missing_age(eligibility_engine, sample_user_profile, sample_scheme):
    """Test eligibility check when age information is missing."""
    no_age_user = sample_user_profile.model_copy()
    no_age_user.age = None
    
    result = eligibility_engine.check_single_scheme(no_age_user, sample_scheme)
    
    assert result.is_eligible is False
    assert any("age" in criterion.lower() and "required" in criterion.lower() for criterion in result.missing_criteria)


def test_check_single_scheme_no_restrictions():
    """Test eligibility check for scheme with no restrictions."""
    engine = EligibilityEngine()
    
    # User with minimal info
    user = UserProfile(age=25)
    
    # Scheme with no restrictions
    scheme = Scheme(
        id="open-scheme",
        name="Open Scheme",
        name_translations={},
        description="Scheme open to all",
        description_translations={},
        eligibility=EligibilityCriteria(
            min_age=None,
            max_age=None,
            states=None,
            education_levels=None,
            income_max=None,
            categories=None,
            gender=None,
            occupations=None
        ),
        benefits="Universal benefits",
        required_documents=[],
        application_process="Apply anytime",
        application_url="https://example.com",
        office_location=None,
        deadline=None,
        source_url="https://example.com",
        last_updated="2024-01-01T00:00:00"
    )
    
    result = engine.check_single_scheme(user, scheme)
    
    # Should be eligible since there are no restrictions
    assert result.is_eligible is True


def test_determine_eligibility_multiple_schemes(eligibility_engine, sample_user_profile):
    """Test eligibility determination across multiple schemes."""
    schemes = [
        Scheme(
            id="scheme-1",
            name="Scheme 1",
            name_translations={},
            description="First scheme",
            description_translations={},
            eligibility=EligibilityCriteria(
                min_age=18,
                max_age=30,
                states=["Maharashtra"],
                education_levels=["graduate"],
                income_max=500000,
                categories=None,
                gender=None,
                occupations=["student"]
            ),
            benefits="Benefits 1",
            required_documents=[],
            application_process="Process 1",
            application_url="https://example.com",
            office_location=None,
            deadline=None,
            source_url="https://example.com",
            last_updated="2024-01-01T00:00:00"
        ),
        Scheme(
            id="scheme-2",
            name="Scheme 2",
            name_translations={},
            description="Second scheme",
            description_translations={},
            eligibility=EligibilityCriteria(
                min_age=18,
                max_age=30,
                states=["Delhi"],  # Wrong state
                education_levels=["graduate"],
                income_max=500000,
                categories=None,
                gender=None,
                occupations=["student"]
            ),
            benefits="Benefits 2",
            required_documents=[],
            application_process="Process 2",
            application_url="https://example.com",
            office_location=None,
            deadline=None,
            source_url="https://example.com",
            last_updated="2024-01-01T00:00:00"
        ),
        Scheme(
            id="scheme-3",
            name="Scheme 3",
            name_translations={},
            description="Third scheme",
            description_translations={},
            eligibility=EligibilityCriteria(
                min_age=18,
                max_age=30,
                states=["Maharashtra"],
                education_levels=["graduate"],
                income_max=500000,
                categories=None,
                gender=None,
                occupations=None  # No occupation restriction
            ),
            benefits="Benefits 3",
            required_documents=[],
            application_process="Process 3",
            application_url="https://example.com",
            office_location=None,
            deadline=None,
            source_url="https://example.com",
            last_updated="2024-01-01T00:00:00"
        )
    ]
    
    results = eligibility_engine.determine_eligibility(sample_user_profile, schemes)
    
    # Should return 2 eligible schemes (scheme-1 and scheme-3)
    assert len(results) == 2
    assert all(r.is_eligible for r in results)
    assert results[0].scheme.id in ["scheme-1", "scheme-3"]
    assert results[1].scheme.id in ["scheme-1", "scheme-3"]


def test_determine_eligibility_ranking(eligibility_engine, sample_user_profile):
    """Test that schemes are ranked by number of matching criteria."""
    schemes = [
        Scheme(
            id="scheme-few-matches",
            name="Scheme with Few Matches",
            name_translations={},
            description="Scheme with minimal criteria",
            description_translations={},
            eligibility=EligibilityCriteria(
                min_age=18,
                max_age=30,
                states=None,
                education_levels=None,
                income_max=None,
                categories=None,
                gender=None,
                occupations=None
            ),
            benefits="Benefits",
            required_documents=[],
            application_process="Process",
            application_url="https://example.com",
            office_location=None,
            deadline=None,
            source_url="https://example.com",
            last_updated="2024-01-01T00:00:00"
        ),
        Scheme(
            id="scheme-many-matches",
            name="Scheme with Many Matches",
            name_translations={},
            description="Scheme with many criteria",
            description_translations={},
            eligibility=EligibilityCriteria(
                min_age=18,
                max_age=30,
                states=["Maharashtra"],
                education_levels=["graduate"],
                income_max=500000,
                categories=None,
                gender=None,
                occupations=["student"]
            ),
            benefits="Benefits",
            required_documents=[],
            application_process="Process",
            application_url="https://example.com",
            office_location=None,
            deadline=None,
            source_url="https://example.com",
            last_updated="2024-01-01T00:00:00"
        )
    ]
    
    results = eligibility_engine.determine_eligibility(sample_user_profile, schemes)
    
    # Scheme with more matching criteria should be ranked first
    assert len(results) == 2
    assert results[0].scheme.id == "scheme-many-matches"
    assert len(results[0].matching_criteria) > len(results[1].matching_criteria)


def test_generate_eligibility_explanation_eligible(eligibility_engine, sample_scheme):
    """Test explanation generation for eligible user."""
    matching_criteria = ["Age matches", "State matches", "Education matches"]
    missing_criteria = []
    
    explanation = eligibility_engine.generate_eligibility_explanation(
        sample_scheme, True, matching_criteria, missing_criteria
    )
    
    assert "eligible" in explanation.lower()
    assert "✅" in explanation
    assert all(criterion in explanation for criterion in matching_criteria)


def test_generate_eligibility_explanation_not_eligible(eligibility_engine, sample_scheme):
    """Test explanation generation for non-eligible user."""
    matching_criteria = ["Age matches"]
    missing_criteria = ["State doesn't match", "Income too high"]
    
    explanation = eligibility_engine.generate_eligibility_explanation(
        sample_scheme, False, matching_criteria, missing_criteria
    )
    
    assert "not eligible" in explanation.lower()
    assert "❌" in explanation
    assert all(criterion in explanation for criterion in missing_criteria)


def test_category_specific_scheme(eligibility_engine):
    """Test eligibility for category-specific schemes (SC/ST)."""
    sc_user = UserProfile(
        age=20,
        state="Maharashtra",
        education_level="graduate",
        income_range="below_1lakh",
        category="sc",
        gender="male",
        occupation="student"
    )
    
    general_user = UserProfile(
        age=20,
        state="Maharashtra",
        education_level="graduate",
        income_range="below_1lakh",
        category="general",
        gender="male",
        occupation="student"
    )
    
    sc_scheme = Scheme(
        id="sc-scheme",
        name="SC Scholarship",
        name_translations={},
        description="Scholarship for SC students",
        description_translations={},
        eligibility=EligibilityCriteria(
            min_age=18,
            max_age=30,
            states=None,
            education_levels=["graduate"],
            income_max=250000,
            categories=["sc"],
            gender=None,
            occupations=["student"]
        ),
        benefits="Scholarship",
        required_documents=[],
        application_process="Apply online",
        application_url="https://example.com",
        office_location=None,
        deadline=None,
        source_url="https://example.com",
        last_updated="2024-01-01T00:00:00"
    )
    
    # SC user should be eligible
    sc_result = eligibility_engine.check_single_scheme(sc_user, sc_scheme)
    assert sc_result.is_eligible is True
    
    # General category user should not be eligible
    general_result = eligibility_engine.check_single_scheme(general_user, sc_scheme)
    assert general_result.is_eligible is False


def test_gender_specific_scheme(eligibility_engine):
    """Test eligibility for gender-specific schemes."""
    female_user = UserProfile(
        age=8,
        state="Maharashtra",
        education_level=None,
        income_range="1-3lakh",
        category="general",
        gender="female",
        occupation=None
    )
    
    male_user = UserProfile(
        age=8,
        state="Maharashtra",
        education_level=None,
        income_range="1-3lakh",
        category="general",
        gender="male",
        occupation=None
    )
    
    female_scheme = Scheme(
        id="sukanya-samriddhi",
        name="Sukanya Samriddhi Yojana",
        name_translations={},
        description="Scheme for girl child",
        description_translations={},
        eligibility=EligibilityCriteria(
            min_age=0,
            max_age=10,
            states=None,
            education_levels=None,
            income_max=None,
            categories=None,
            gender="female",
            occupations=None
        ),
        benefits="Savings scheme",
        required_documents=[],
        application_process="Apply at post office",
        application_url="https://example.com",
        office_location=None,
        deadline=None,
        source_url="https://example.com",
        last_updated="2024-01-01T00:00:00"
    )
    
    # Female user should be eligible
    female_result = eligibility_engine.check_single_scheme(female_user, female_scheme)
    assert female_result.is_eligible is True
    
    # Male user should not be eligible
    male_result = eligibility_engine.check_single_scheme(male_user, female_scheme)
    assert male_result.is_eligible is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
