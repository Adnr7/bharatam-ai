"""Conversation state and message data models."""

from typing import List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.user import UserProfile


class Message(BaseModel):
    """
    A single message in the conversation.
    
    Validates: Requirements 2.1 (Guided Conversation Flow)
    """
    
    role: str = Field(
        ...,
        description="Message role: 'user' or 'assistant'"
    )
    
    content: str = Field(
        ...,
        description="Message content"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Message timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "assistant",
                "content": "Hello! I can help you find government schemes. What is your age?",
                "timestamp": "2023-01-01T12:00:00"
            }
        }


class ConversationState(BaseModel):
    """
    State of an active conversation session.
    This data is stored in-memory only and deleted when the session ends.
    
    Validates: Requirements 2.1, 7.1, 7.2 (Conversation Flow and Privacy)
    """
    
    session_id: str = Field(
        ...,
        description="Unique session identifier"
    )
    
    language: str = Field(
        default="en",
        description="User's chosen language code (e.g., 'en', 'hi')"
    )
    
    user_profile: UserProfile = Field(
        default_factory=UserProfile,
        description="User profile information collected during conversation"
    )
    
    asked_questions: List[str] = Field(
        default_factory=list,
        description="List of questions already asked to avoid repetition"
    )
    
    current_stage: str = Field(
        default="greeting",
        description="Current conversation stage: 'greeting', 'info_collection', 'eligibility', 'guidance'"
    )
    
    conversation_history: List[Message] = Field(
        default_factory=list,
        description="Complete conversation history"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Session creation timestamp"
    )
    
    last_activity: datetime = Field(
        default_factory=datetime.now,
        description="Last activity timestamp for timeout tracking"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123",
                "language": "en",
                "user_profile": {
                    "age": 25,
                    "state": "Karnataka"
                },
                "asked_questions": ["age", "state"],
                "current_stage": "info_collection",
                "conversation_history": [
                    {
                        "role": "assistant",
                        "content": "What is your age?",
                        "timestamp": "2023-01-01T12:00:00"
                    },
                    {
                        "role": "user",
                        "content": "I am 25 years old",
                        "timestamp": "2023-01-01T12:00:05"
                    }
                ],
                "created_at": "2023-01-01T12:00:00",
                "last_activity": "2023-01-01T12:00:05"
            }
        }
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        message = Message(role=role, content=content)
        self.conversation_history.append(message)
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int) -> bool:
        """Check if the session has expired based on last activity."""
        elapsed = datetime.now() - self.last_activity
        return elapsed.total_seconds() > (timeout_minutes * 60)
    
    def mark_question_asked(self, question_type: str) -> None:
        """Mark a question type as asked to avoid repetition."""
        if question_type not in self.asked_questions:
            self.asked_questions.append(question_type)
