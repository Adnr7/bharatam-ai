"""
Conversation Engine for Bharatam AI

This module manages conversation state, determines the next question to ask,
and handles the guided question flow for collecting user information.

Requirements: 2.1, 2.2, 2.3, 2.4, 7.1, 7.2, 11.2
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List
from uuid import uuid4

from app.models.conversation import ConversationState, Message
from app.models.user import UserProfile


class ConversationEngine:
    """
    Manages conversation flow and state for user interactions.
    
    Implements guided question flow to collect user information needed
    for eligibility determination.
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 7.1, 7.2
    """
    
    # Session storage (in-memory for MVP)
    _sessions: Dict[str, ConversationState] = {}
    
    # Session timeout (30 minutes)
    SESSION_TIMEOUT = timedelta(minutes=30)
    
    # Question templates for information collection
    QUESTIONS = {
        "age": {
            "en": "How old are you?",
            "hi": "आपकी उम्र क्या है?"
        },
        "state": {
            "en": "Which state do you live in?",
            "hi": "आप किस राज्य में रहते हैं?"
        },
        "education_level": {
            "en": "What is your highest education level? (e.g., 10th pass, 12th pass, graduate, postgraduate)",
            "hi": "आपकी उच्चतम शिक्षा स्तर क्या है? (जैसे, 10वीं पास, 12वीं पास, स्नातक, स्नातकोत्तर)"
        },
        "income_range": {
            "en": "What is your annual household income range? (e.g., below 1 lakh, 1-3 lakh, 3-5 lakh, above 5 lakh)",
            "hi": "आपकी वार्षिक घरेलू आय सीमा क्या है? (जैसे, 1 लाख से कम, 1-3 लाख, 3-5 लाख, 5 लाख से अधिक)"
        },
        "category": {
            "en": "What is your social category? (General, SC, ST, OBC)",
            "hi": "आपकी सामाजिक श्रेणी क्या है? (सामान्य, अनुसूचित जाति, अनुसूचित जनजाति, अन्य पिछड़ा वर्ग)"
        },
        "gender": {
            "en": "What is your gender? (male, female, other)",
            "hi": "आपका लिंग क्या है? (पुरुष, महिला, अन्य)"
        },
        "occupation": {
            "en": "What is your occupation? (e.g., student, farmer, self-employed, unemployed)",
            "hi": "आपका व्यवसाय क्या है? (जैसे, छात्र, किसान, स्व-रोजगार, बेरोजगार)"
        }
    }
    
    # Greeting messages
    GREETINGS = {
        "en": "Hello! I'm Bharatam AI, your assistant for discovering government welfare schemes. I'll ask you a few questions to understand your needs and find schemes you're eligible for. Let's get started!",
        "hi": "नमस्ते! मैं भारतम AI हूं, सरकारी कल्याण योजनाओं की खोज के लिए आपका सहायक। मैं आपकी आवश्यकताओं को समझने और आपके लिए उपयुक्त योजनाओं को खोजने के लिए कुछ प्रश्न पूछूंगा। चलिए शुरू करते हैं!"
    }
    
    def __init__(self):
        """Initialize the conversation engine."""
        pass
    
    def start_conversation(self, language: str = "en") -> ConversationState:
        """
        Start a new conversation session.
        
        Args:
            language: Language code ("en" or "hi")
            
        Returns:
            New ConversationState with session ID
            
        Requirements: 2.1, 7.1
        """
        session_id = str(uuid4())
        
        state = ConversationState(
            session_id=session_id,
            language=language,
            user_profile=UserProfile(),
            current_stage="greeting",
            conversation_history=[],
            asked_questions=[],
            created_at=datetime.now(),
            last_updated=datetime.now()
        )
        
        # Store session
        self._sessions[session_id] = state
        
        # Add greeting message
        greeting = self.GREETINGS.get(language, self.GREETINGS["en"])
        self._add_message(state, "assistant", greeting)
        
        return state

    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """
        Retrieve a conversation session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationState if found and not expired, None otherwise
            
        Requirements: 7.1, 7.2
        """
        state = self._sessions.get(session_id)
        
        if not state:
            return None
        
        # Check if session has expired
        if datetime.now() - state.last_activity > self.SESSION_TIMEOUT:
            self.end_conversation(session_id)
            return None
        
        return state
    
    def end_conversation(self, session_id: str) -> bool:
        """
        End a conversation session and cleanup.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and deleted, False otherwise
            
        Requirements: 7.2
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions cleaned up
            
        Requirements: 7.2
        """
        now = datetime.now()
        expired = [
            sid for sid, state in self._sessions.items()
            if now - state.last_activity > self.SESSION_TIMEOUT
        ]
        
        for sid in expired:
            del self._sessions[sid]
        
        return len(expired)
    
    def get_next_question(self, state: ConversationState) -> Optional[str]:
        """
        Determine the next question to ask based on current state.
        
        Implements guided question flow by identifying missing information
        and asking relevant questions.
        
        Args:
            state: Current conversation state
            
        Returns:
            Next question text, or None if all information is collected
            
        Requirements: 2.2, 2.3
        """
        # If in greeting stage, move to info collection
        if state.current_stage == "greeting":
            state.current_stage = "info_collection"
        
        # If not in info collection stage, no more questions
        if state.current_stage != "info_collection":
            return None
        
        # Determine which information is missing
        profile = state.user_profile
        language = state.language
        
        # Priority order for questions
        question_order = [
            ("age", profile.age),
            ("state", profile.state),
            ("education_level", profile.education_level),
            ("income_range", profile.income_range),
            ("category", profile.category),
            ("gender", profile.gender),
            ("occupation", profile.occupation)
        ]
        
        # Find first missing piece of information that hasn't been asked
        for field_name, field_value in question_order:
            if field_value is None and field_name not in state.asked_questions:
                # Mark as asked
                state.asked_questions.append(field_name)
                # Return question in appropriate language
                return self.QUESTIONS[field_name].get(language, self.QUESTIONS[field_name]["en"])
        
        # All information collected
        return None

    def is_information_complete(self, state: ConversationState) -> bool:
        """
        Check if sufficient information has been collected.
        
        Minimum required: age, state
        Optional but helpful: education, income, category, gender, occupation
        
        Args:
            state: Current conversation state
            
        Returns:
            True if minimum information is collected, False otherwise
            
        Requirements: 2.4
        """
        profile = state.user_profile
        
        # Minimum required information
        if profile.age is None or profile.state is None:
            return False
        
        return True
    
    def update_user_profile(
        self,
        state: ConversationState,
        field: str,
        value: any
    ) -> None:
        """
        Update a field in the user profile.
        
        Args:
            state: Current conversation state
            field: Field name to update
            value: New value
            
        Requirements: 2.1
        """
        if hasattr(state.user_profile, field):
            setattr(state.user_profile, field, value)
            state.last_activity = datetime.now()
    
    def add_user_message(self, state: ConversationState, content: str) -> None:
        """
        Add a user message to conversation history.
        
        Args:
            state: Current conversation state
            content: Message content
            
        Requirements: 2.1
        """
        self._add_message(state, "user", content)
    
    def add_assistant_message(self, state: ConversationState, content: str) -> None:
        """
        Add an assistant message to conversation history.
        
        Args:
            state: Current conversation state
            content: Message content
            
        Requirements: 2.1
        """
        self._add_message(state, "assistant", content)
    
    def _add_message(self, state: ConversationState, role: str, content: str) -> None:
        """
        Internal method to add a message to conversation history.
        
        Args:
            state: Current conversation state
            role: Message role ("user" or "assistant")
            content: Message content
        """
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        state.conversation_history.append(message)
        state.last_activity = datetime.now()
    
    def get_missing_information(self, state: ConversationState) -> List[str]:
        """
        Get list of missing information fields.
        
        Args:
            state: Current conversation state
            
        Returns:
            List of field names that are missing
            
        Requirements: 11.2
        """
        profile = state.user_profile
        missing = []
        
        fields = [
            ("age", profile.age),
            ("state", profile.state),
            ("education_level", profile.education_level),
            ("income_range", profile.income_range),
            ("category", profile.category),
            ("gender", profile.gender),
            ("occupation", profile.occupation)
        ]
        
        for field_name, field_value in fields:
            if field_value is None:
                missing.append(field_name)
        
        return missing
    
    def transition_to_eligibility(self, state: ConversationState) -> None:
        """
        Transition conversation to eligibility determination stage.
        
        Args:
            state: Current conversation state
            
        Requirements: 2.4
        """
        if self.is_information_complete(state):
            state.current_stage = "eligibility"
            state.last_activity = datetime.now()
    
    def transition_to_guidance(self, state: ConversationState) -> None:
        """
        Transition conversation to guidance stage.
        
        Args:
            state: Current conversation state
            
        Requirements: 2.4
        """
        state.current_stage = "guidance"
        state.last_activity = datetime.now()
    
    def get_conversation_summary(self, state: ConversationState) -> Dict:
        """
        Get a summary of the conversation state.
        
        Args:
            state: Current conversation state
            
        Returns:
            Dictionary with conversation summary
        """
        return {
            "session_id": state.session_id,
            "language": state.language,
            "current_stage": state.current_stage,
            "messages_count": len(state.conversation_history),
            "information_complete": self.is_information_complete(state),
            "missing_fields": self.get_missing_information(state),
            "user_profile": {
                "age": state.user_profile.age,
                "state": state.user_profile.state,
                "education_level": state.user_profile.education_level,
                "income_range": state.user_profile.income_range,
                "category": state.user_profile.category,
                "gender": state.user_profile.gender,
                "occupation": state.user_profile.occupation
            }
        }
    
    @classmethod
    def get_active_sessions_count(cls) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(cls._sessions)
