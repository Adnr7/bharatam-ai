"""
Unit tests for Conversation Engine.

Tests conversation flow, state management, question selection, and session handling.

Requirements: 2.1, 2.2, 2.3, 2.4, 7.1, 7.2, 11.2
"""

import pytest
from datetime import datetime, timedelta
from time import sleep

from app.services.conversation import ConversationEngine
from app.models.conversation import ConversationState


@pytest.fixture
def engine():
    """Create a fresh conversation engine for each test."""
    # Clear any existing sessions
    ConversationEngine._sessions = {}
    return ConversationEngine()


@pytest.fixture
def sample_state(engine):
    """Create a sample conversation state."""
    return engine.start_conversation(language="en")


class TestConversationInitialization:
    """Test conversation initialization and session management."""
    
    def test_start_conversation_english(self, engine):
        """Test starting a conversation in English."""
        state = engine.start_conversation(language="en")
        
        assert state.session_id is not None
        assert state.language == "en"
        assert state.current_stage == "greeting"
        assert len(state.conversation_history) == 1
        assert state.conversation_history[0].role == "assistant"
        assert "Bharatam AI" in state.conversation_history[0].content
    
    def test_start_conversation_hindi(self, engine):
        """Test starting a conversation in Hindi."""
        state = engine.start_conversation(language="hi")
        
        assert state.session_id is not None
        assert state.language == "hi"
        assert state.current_stage == "greeting"
        assert len(state.conversation_history) == 1
        assert "भारतम" in state.conversation_history[0].content
    
    def test_unique_session_ids(self, engine):
        """Test that each conversation gets a unique session ID."""
        state1 = engine.start_conversation()
        state2 = engine.start_conversation()
        
        assert state1.session_id != state2.session_id
    
    def test_session_stored(self, engine):
        """Test that session is stored and retrievable."""
        state = engine.start_conversation()
        
        retrieved = engine.get_session(state.session_id)
        assert retrieved is not None
        assert retrieved.session_id == state.session_id


class TestSessionManagement:
    """Test session retrieval, expiration, and cleanup."""
    
    def test_get_existing_session(self, engine, sample_state):
        """Test retrieving an existing session."""
        retrieved = engine.get_session(sample_state.session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == sample_state.session_id
    
    def test_get_nonexistent_session(self, engine):
        """Test retrieving a non-existent session."""
        retrieved = engine.get_session("nonexistent-id")
        
        assert retrieved is None
    
    def test_end_conversation(self, engine, sample_state):
        """Test ending a conversation."""
        success = engine.end_conversation(sample_state.session_id)
        
        assert success is True
        assert engine.get_session(sample_state.session_id) is None
    
    def test_end_nonexistent_conversation(self, engine):
        """Test ending a non-existent conversation."""
        success = engine.end_conversation("nonexistent-id")
        
        assert success is False
    
    def test_session_expiration(self, engine):
        """Test that expired sessions are not retrievable."""
        state = engine.start_conversation()
        
        # Manually set last_activity to past
        state.last_activity = datetime.now() - timedelta(minutes=31)
        
        # Try to retrieve - should return None and cleanup
        retrieved = engine.get_session(state.session_id)
        
        assert retrieved is None
    
    def test_cleanup_expired_sessions(self, engine):
        """Test cleanup of expired sessions."""
        # Create multiple sessions
        state1 = engine.start_conversation()
        state2 = engine.start_conversation()
        state3 = engine.start_conversation()
        
        # Expire two of them
        state1.last_activity = datetime.now() - timedelta(minutes=31)
        state2.last_activity = datetime.now() - timedelta(minutes=31)
        
        # Cleanup
        count = engine.cleanup_expired_sessions()
        
        assert count == 2
        assert engine.get_session(state1.session_id) is None
        assert engine.get_session(state2.session_id) is None
        assert engine.get_session(state3.session_id) is not None
    
    def test_active_sessions_count(self, engine):
        """Test counting active sessions."""
        assert ConversationEngine.get_active_sessions_count() == 0
        
        engine.start_conversation()
        assert ConversationEngine.get_active_sessions_count() == 1
        
        engine.start_conversation()
        assert ConversationEngine.get_active_sessions_count() == 2



class TestQuestionFlow:
    """Test dynamic question flow and information collection."""
    
    def test_first_question_is_age(self, engine, sample_state):
        """Test that first question asks for age."""
        question = engine.get_next_question(sample_state)
        
        assert question is not None
        assert "age" in question.lower() or "old" in question.lower()
        assert "age" in sample_state.asked_questions
    
    def test_question_flow_order(self, engine, sample_state):
        """Test that questions follow the correct order."""
        # Get questions in sequence
        q1 = engine.get_next_question(sample_state)
        assert "age" in q1.lower() or "old" in q1.lower()
        
        q2 = engine.get_next_question(sample_state)
        assert "state" in q2.lower() or "live" in q2.lower()
        
        q3 = engine.get_next_question(sample_state)
        assert "education" in q3.lower()
    
    def test_no_duplicate_questions(self, engine, sample_state):
        """Test that same question is not asked twice."""
        # Ask all questions
        questions = []
        while True:
            q = engine.get_next_question(sample_state)
            if q is None:
                break
            questions.append(q)
        
        # Check no duplicates
        assert len(questions) == len(set(questions))
    
    def test_questions_in_hindi(self, engine):
        """Test that questions are in Hindi when language is Hindi."""
        state = engine.start_conversation(language="hi")
        question = engine.get_next_question(state)
        
        assert question is not None
        # Check for Hindi characters
        assert any(ord(char) > 2304 for char in question)
    
    def test_stage_transition_to_info_collection(self, engine, sample_state):
        """Test transition from greeting to info collection."""
        assert sample_state.current_stage == "greeting"
        
        engine.get_next_question(sample_state)
        
        assert sample_state.current_stage == "info_collection"
    
    def test_no_questions_after_completion(self, engine, sample_state):
        """Test that no questions are asked after all info is collected."""
        # Fill in all information
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        sample_state.user_profile.education_level = "graduate"
        sample_state.user_profile.income_range = "1-3lakh"
        sample_state.user_profile.category = "general"
        sample_state.user_profile.gender = "male"
        sample_state.user_profile.occupation = "student"
        
        # Mark all as asked
        sample_state.asked_questions = [
            "age", "state", "education_level", "income_range",
            "category", "gender", "occupation"
        ]
        
        question = engine.get_next_question(sample_state)
        
        assert question is None


class TestInformationCompleteness:
    """Test information completeness checking."""
    
    def test_incomplete_with_no_info(self, engine, sample_state):
        """Test that state is incomplete with no information."""
        assert not engine.is_information_complete(sample_state)
    
    def test_incomplete_with_only_age(self, engine, sample_state):
        """Test that state is incomplete with only age."""
        sample_state.user_profile.age = 25
        
        assert not engine.is_information_complete(sample_state)
    
    def test_incomplete_with_only_state(self, engine, sample_state):
        """Test that state is incomplete with only state."""
        sample_state.user_profile.state = "Maharashtra"
        
        assert not engine.is_information_complete(sample_state)
    
    def test_complete_with_minimum_info(self, engine, sample_state):
        """Test that state is complete with age and state."""
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        
        assert engine.is_information_complete(sample_state)
    
    def test_complete_with_all_info(self, engine, sample_state):
        """Test that state is complete with all information."""
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        sample_state.user_profile.education_level = "graduate"
        sample_state.user_profile.income_range = "1-3lakh"
        sample_state.user_profile.category = "general"
        sample_state.user_profile.gender = "male"
        sample_state.user_profile.occupation = "student"
        
        assert engine.is_information_complete(sample_state)


class TestProfileUpdates:
    """Test user profile updates."""
    
    def test_update_age(self, engine, sample_state):
        """Test updating age field."""
        engine.update_user_profile(sample_state, "age", 25)
        
        assert sample_state.user_profile.age == 25
    
    def test_update_state(self, engine, sample_state):
        """Test updating state field."""
        engine.update_user_profile(sample_state, "state", "Maharashtra")
        
        assert sample_state.user_profile.state == "Maharashtra"
    
    def test_update_multiple_fields(self, engine, sample_state):
        """Test updating multiple fields."""
        engine.update_user_profile(sample_state, "age", 25)
        engine.update_user_profile(sample_state, "state", "Maharashtra")
        engine.update_user_profile(sample_state, "education_level", "graduate")
        
        assert sample_state.user_profile.age == 25
        assert sample_state.user_profile.state == "Maharashtra"
        assert sample_state.user_profile.education_level == "graduate"
    
    def test_update_invalid_field(self, engine, sample_state):
        """Test that updating invalid field doesn't crash."""
        # Should not raise exception
        engine.update_user_profile(sample_state, "invalid_field", "value")
        
        # Profile should remain unchanged
        assert not hasattr(sample_state.user_profile, "invalid_field")


class TestMessageHandling:
    """Test message addition and conversation history."""
    
    def test_add_user_message(self, engine, sample_state):
        """Test adding a user message."""
        initial_count = len(sample_state.conversation_history)
        
        engine.add_user_message(sample_state, "I am 25 years old")
        
        assert len(sample_state.conversation_history) == initial_count + 1
        assert sample_state.conversation_history[-1].role == "user"
        assert sample_state.conversation_history[-1].content == "I am 25 years old"
    
    def test_add_assistant_message(self, engine, sample_state):
        """Test adding an assistant message."""
        initial_count = len(sample_state.conversation_history)
        
        engine.add_assistant_message(sample_state, "Thank you! What state do you live in?")
        
        assert len(sample_state.conversation_history) == initial_count + 1
        assert sample_state.conversation_history[-1].role == "assistant"
    
    def test_message_timestamps(self, engine, sample_state):
        """Test that messages have timestamps."""
        engine.add_user_message(sample_state, "Test message")
        
        message = sample_state.conversation_history[-1]
        assert message.timestamp is not None
        assert isinstance(message.timestamp, datetime)
    
    def test_conversation_history_order(self, engine, sample_state):
        """Test that conversation history maintains order."""
        engine.add_user_message(sample_state, "Message 1")
        engine.add_assistant_message(sample_state, "Message 2")
        engine.add_user_message(sample_state, "Message 3")
        
        assert sample_state.conversation_history[-3].content == "Message 1"
        assert sample_state.conversation_history[-2].content == "Message 2"
        assert sample_state.conversation_history[-1].content == "Message 3"



class TestMissingInformation:
    """Test missing information detection."""
    
    def test_all_missing_initially(self, engine, sample_state):
        """Test that all fields are missing initially."""
        missing = engine.get_missing_information(sample_state)
        
        assert len(missing) == 7
        assert "age" in missing
        assert "state" in missing
        assert "education_level" in missing
    
    def test_missing_after_partial_fill(self, engine, sample_state):
        """Test missing fields after partial information."""
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        
        missing = engine.get_missing_information(sample_state)
        
        assert "age" not in missing
        assert "state" not in missing
        assert "education_level" in missing
        assert len(missing) == 5
    
    def test_no_missing_when_complete(self, engine, sample_state):
        """Test no missing fields when all filled."""
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        sample_state.user_profile.education_level = "graduate"
        sample_state.user_profile.income_range = "1-3lakh"
        sample_state.user_profile.category = "general"
        sample_state.user_profile.gender = "male"
        sample_state.user_profile.occupation = "student"
        
        missing = engine.get_missing_information(sample_state)
        
        assert len(missing) == 0


class TestStageTransitions:
    """Test conversation stage transitions."""
    
    def test_transition_to_eligibility(self, engine, sample_state):
        """Test transition to eligibility stage."""
        # Fill minimum required info
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        
        engine.transition_to_eligibility(sample_state)
        
        assert sample_state.current_stage == "eligibility"
    
    def test_transition_to_eligibility_without_info(self, engine, sample_state):
        """Test that transition doesn't happen without required info."""
        # Try to transition without filling info
        engine.transition_to_eligibility(sample_state)
        
        # Should remain in current stage
        assert sample_state.current_stage != "eligibility"
    
    def test_transition_to_guidance(self, engine, sample_state):
        """Test transition to guidance stage."""
        engine.transition_to_guidance(sample_state)
        
        assert sample_state.current_stage == "guidance"
    
    def test_stage_flow(self, engine, sample_state):
        """Test complete stage flow."""
        # Start in greeting
        assert sample_state.current_stage == "greeting"
        
        # Move to info collection
        engine.get_next_question(sample_state)
        assert sample_state.current_stage == "info_collection"
        
        # Fill info and move to eligibility
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        engine.transition_to_eligibility(sample_state)
        assert sample_state.current_stage == "eligibility"
        
        # Move to guidance
        engine.transition_to_guidance(sample_state)
        assert sample_state.current_stage == "guidance"


class TestConversationSummary:
    """Test conversation summary generation."""
    
    def test_summary_structure(self, engine, sample_state):
        """Test that summary has correct structure."""
        summary = engine.get_conversation_summary(sample_state)
        
        assert "session_id" in summary
        assert "language" in summary
        assert "current_stage" in summary
        assert "messages_count" in summary
        assert "information_complete" in summary
        assert "missing_fields" in summary
        assert "user_profile" in summary
    
    def test_summary_values(self, engine, sample_state):
        """Test that summary contains correct values."""
        sample_state.user_profile.age = 25
        sample_state.user_profile.state = "Maharashtra"
        
        summary = engine.get_conversation_summary(sample_state)
        
        assert summary["session_id"] == sample_state.session_id
        assert summary["language"] == "en"
        assert summary["current_stage"] == "greeting"
        assert summary["information_complete"] is True
        assert summary["user_profile"]["age"] == 25
        assert summary["user_profile"]["state"] == "Maharashtra"
    
    def test_summary_messages_count(self, engine, sample_state):
        """Test that summary counts messages correctly."""
        engine.add_user_message(sample_state, "Test 1")
        engine.add_assistant_message(sample_state, "Test 2")
        
        summary = engine.get_conversation_summary(sample_state)
        
        # 1 greeting + 2 added = 3 total
        assert summary["messages_count"] == 3


class TestIntegrationScenarios:
    """Test complete conversation scenarios."""
    
    def test_complete_conversation_flow(self, engine):
        """Test a complete conversation from start to finish."""
        # Start conversation
        state = engine.start_conversation(language="en")
        assert state.current_stage == "greeting"
        
        # Get first question (age)
        q1 = engine.get_next_question(state)
        assert q1 is not None
        engine.add_user_message(state, "I am 25 years old")
        engine.update_user_profile(state, "age", 25)
        
        # Get second question (state)
        q2 = engine.get_next_question(state)
        assert q2 is not None
        engine.add_user_message(state, "Maharashtra")
        engine.update_user_profile(state, "state", "Maharashtra")
        
        # Check information is complete
        assert engine.is_information_complete(state)
        
        # Transition to eligibility
        engine.transition_to_eligibility(state)
        assert state.current_stage == "eligibility"
        
        # Verify session is retrievable
        retrieved = engine.get_session(state.session_id)
        assert retrieved is not None
        assert retrieved.user_profile.age == 25
    
    def test_multilingual_conversation(self, engine):
        """Test conversation in Hindi."""
        state = engine.start_conversation(language="hi")
        
        # Check greeting is in Hindi
        assert any(ord(char) > 2304 for char in state.conversation_history[0].content)
        
        # Get question in Hindi
        question = engine.get_next_question(state)
        assert any(ord(char) > 2304 for char in question)
    
    def test_session_lifecycle(self, engine):
        """Test complete session lifecycle."""
        # Create session
        state = engine.start_conversation()
        session_id = state.session_id
        assert engine.get_active_sessions_count() == 1
        
        # Use session
        engine.add_user_message(state, "Test")
        retrieved = engine.get_session(session_id)
        assert retrieved is not None
        
        # End session
        engine.end_conversation(session_id)
        assert engine.get_active_sessions_count() == 0
        assert engine.get_session(session_id) is None
