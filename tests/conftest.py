"""Pytest configuration and shared fixtures."""

import pytest
from datetime import datetime
from app.models import (
    UserProfile,
    Scheme,
    EligibilityCriteria,
    EligibilityResult,
    ConversationState,
    Message
)


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return UserProfile(
        age=25,
        state="Karnataka",
        education_level="graduate",
        income_range="1-3lakh",
        category="general",
        occupation="student",
        gender="female"
    )


@pytest.fixture
def incomplete_user_profile():
    """Incomplete user profile for testing conversation flow."""
    return UserProfile(
        age=25,
        state="Karnataka"
    )


@pytest.fixture
def sample_eligibility_criteria():
    """Sample eligibility criteria for testing."""
    return EligibilityCriteria(
        min_age=18,
        max_age=35,
        states=["Karnataka", "Tamil Nadu"],
        education_levels=["graduate", "postgraduate"],
        income_max=300000,
        categories=["general", "obc"],
        gender=None,
        occupations=["student", "unemployed"]
    )


@pytest.fixture
def sample_scheme(sample_eligibility_criteria):
    """Sample government scheme for testing."""
    return Scheme(
        id="test-scheme-001",
        name="Test Skill Development Scheme",
        name_translations={"hi": "परीक्षण कौशल विकास योजना"},
        description="A test scheme for skill development",
        description_translations={"hi": "कौशल विकास के लिए एक परीक्षण योजना"},
        eligibility=sample_eligibility_criteria,
        benefits="Free training and certification",
        required_documents=["Aadhar Card", "Educational Certificate"],
        application_process="1. Visit portal 2. Register 3. Apply",
        application_url="https://example.gov.in/scheme",
        office_location=None,
        deadline=None,
        source_url="https://example.gov.in/scheme",
        last_updated=datetime(2023, 1, 1)
    )


@pytest.fixture
def sample_conversation_state():
    """Sample conversation state for testing."""
    state = ConversationState(
        session_id="test-session-123",
        language="en",
        user_profile=UserProfile(age=25, state="Karnataka"),
        asked_questions=["age", "state"],
        current_stage="info_collection"
    )
    state.add_message("assistant", "What is your age?")
    state.add_message("user", "I am 25 years old")
    return state


@pytest.fixture
def sample_eligibility_result(sample_scheme):
    """Sample eligibility result for testing."""
    return EligibilityResult(
        scheme=sample_scheme,
        is_eligible=True,
        confidence=0.95,
        matching_criteria=[
            "Age is within range (18-35)",
            "State matches (Karnataka)",
            "Education level matches (graduate)"
        ],
        missing_criteria=[],
        explanation="You are eligible because you meet all the criteria."
    )
