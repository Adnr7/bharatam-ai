"""Unit tests for Pydantic data models."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import (
    UserProfile,
    Scheme,
    EligibilityCriteria,
    EligibilityResult,
    ConversationState,
    Message
)


@pytest.mark.unit
class TestUserProfile:
    """Tests for UserProfile model."""
    
    def test_create_complete_profile(self, sample_user_profile):
        """Test creating a complete user profile."""
        assert sample_user_profile.age == 25
        assert sample_user_profile.state == "Karnataka"
        assert sample_user_profile.education_level == "graduate"
        assert sample_user_profile.is_complete_for_eligibility() is True
    
    def test_create_incomplete_profile(self):
        """Test creating an incomplete user profile."""
        profile = UserProfile(age=25)
        assert profile.age == 25
        assert profile.state is None
        assert profile.is_complete_for_eligibility() is False
    
    def test_get_missing_fields(self):
        """Test getting missing fields from profile."""
        profile = UserProfile(age=25, state="Karnataka")
        missing = profile.get_missing_fields()
        assert "age" not in missing
        assert "state" not in missing
        assert "education_level" in missing
        assert "income_range" in missing
    
    def test_age_validation(self):
        """Test age validation constraints."""
        # Valid age
        profile = UserProfile(age=25)
        assert profile.age == 25
        
        # Invalid age (negative)
        with pytest.raises(ValidationError):
            UserProfile(age=-5)
        
        # Invalid age (too high)
        with pytest.raises(ValidationError):
            UserProfile(age=150)
    
    def test_empty_profile(self):
        """Test creating an empty profile."""
        profile = UserProfile()
        assert profile.age is None
        assert profile.state is None
        assert len(profile.get_missing_fields()) == 7


@pytest.mark.unit
class TestEligibilityCriteria:
    """Tests for EligibilityCriteria model."""
    
    def test_create_criteria(self, sample_eligibility_criteria):
        """Test creating eligibility criteria."""
        assert sample_eligibility_criteria.min_age == 18
        assert sample_eligibility_criteria.max_age == 35
        assert "Karnataka" in sample_eligibility_criteria.states
    
    def test_criteria_with_none_values(self):
        """Test criteria with None values (no restrictions)."""
        criteria = EligibilityCriteria(
            min_age=18,
            max_age=None,  # No maximum age
            states=None,   # All states
            education_levels=None,
            income_max=None,
            categories=None,
            gender=None,
            occupations=None
        )
        assert criteria.min_age == 18
        assert criteria.max_age is None
        assert criteria.states is None
    
    def test_age_validation(self):
        """Test age validation in criteria."""
        # Valid ages
        criteria = EligibilityCriteria(min_age=18, max_age=60)
        assert criteria.min_age == 18
        
        # Invalid age (negative)
        with pytest.raises(ValidationError):
            EligibilityCriteria(min_age=-5)


@pytest.mark.unit
class TestScheme:
    """Tests for Scheme model."""
    
    def test_create_scheme(self, sample_scheme):
        """Test creating a scheme."""
        assert sample_scheme.id == "test-scheme-001"
        assert sample_scheme.name == "Test Skill Development Scheme"
        assert "hi" in sample_scheme.name_translations
        assert sample_scheme.eligibility.min_age == 18
    
    def test_scheme_with_translations(self):
        """Test scheme with multiple language translations."""
        scheme = Scheme(
            id="test-001",
            name="Test Scheme",
            name_translations={"hi": "परीक्षण योजना", "ta": "சோதனை திட்டம்"},
            description="Test description",
            description_translations={"hi": "परीक्षण विवरण"},
            eligibility=EligibilityCriteria(),
            benefits="Test benefits",
            required_documents=["Aadhar"],
            application_process="Apply online",
            source_url="https://example.gov.in"
        )
        assert len(scheme.name_translations) == 2
        assert scheme.name_translations["hi"] == "परीक्षण योजना"
    
    def test_scheme_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            Scheme()  # Missing required fields


@pytest.mark.unit
class TestEligibilityResult:
    """Tests for EligibilityResult model."""
    
    def test_create_result(self, sample_eligibility_result):
        """Test creating an eligibility result."""
        assert sample_eligibility_result.is_eligible is True
        assert sample_eligibility_result.confidence == 0.95
        assert len(sample_eligibility_result.matching_criteria) == 3
    
    def test_confidence_validation(self, sample_scheme):
        """Test confidence score validation."""
        # Valid confidence
        result = EligibilityResult(
            scheme=sample_scheme,
            is_eligible=True,
            confidence=0.5
        )
        assert result.confidence == 0.5
        
        # Invalid confidence (too high)
        with pytest.raises(ValidationError):
            EligibilityResult(
                scheme=sample_scheme,
                is_eligible=True,
                confidence=1.5
            )
        
        # Invalid confidence (negative)
        with pytest.raises(ValidationError):
            EligibilityResult(
                scheme=sample_scheme,
                is_eligible=True,
                confidence=-0.1
            )


@pytest.mark.unit
class TestMessage:
    """Tests for Message model."""
    
    def test_create_message(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, datetime)
    
    def test_message_timestamp(self):
        """Test that timestamp is automatically set."""
        msg1 = Message(role="assistant", content="Hi")
        msg2 = Message(role="user", content="Hello")
        assert msg1.timestamp <= msg2.timestamp


@pytest.mark.unit
class TestConversationState:
    """Tests for ConversationState model."""
    
    def test_create_conversation_state(self, sample_conversation_state):
        """Test creating a conversation state."""
        assert sample_conversation_state.session_id == "test-session-123"
        assert sample_conversation_state.language == "en"
        assert len(sample_conversation_state.conversation_history) == 2
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        state = ConversationState(session_id="test-123")
        assert len(state.conversation_history) == 0
        
        state.add_message("assistant", "Hello")
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0].role == "assistant"
        
        state.add_message("user", "Hi")
        assert len(state.conversation_history) == 2
    
    def test_mark_question_asked(self):
        """Test marking questions as asked."""
        state = ConversationState(session_id="test-123")
        assert len(state.asked_questions) == 0
        
        state.mark_question_asked("age")
        assert "age" in state.asked_questions
        
        # Should not add duplicates
        state.mark_question_asked("age")
        assert state.asked_questions.count("age") == 1
    
    def test_is_expired(self):
        """Test session expiration check."""
        state = ConversationState(session_id="test-123")
        
        # Fresh session should not be expired
        assert state.is_expired(timeout_minutes=30) is False
        
        # Manually set old timestamp
        state.last_activity = datetime(2020, 1, 1)
        assert state.is_expired(timeout_minutes=30) is True
    
    def test_default_values(self):
        """Test default values for conversation state."""
        state = ConversationState(session_id="test-123")
        assert state.language == "en"
        assert state.current_stage == "greeting"
        assert len(state.asked_questions) == 0
        assert len(state.conversation_history) == 0
        assert isinstance(state.user_profile, UserProfile)
