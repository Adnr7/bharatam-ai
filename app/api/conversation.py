"""
Conversation API endpoints.

Provides REST API for managing conversation sessions and processing user messages.

Requirements: 2.1, 7.1, 7.2
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from app.services.conversation import ConversationEngine
from app.services.eligibility import EligibilityEngine
from app.services.data_loader import load_and_validate_schemes
from app.services.ai_assistant import get_ai_assistant
from app.models.conversation import Message
import logging

logger = logging.getLogger(__name__)

# Initialize services
conversation_engine = ConversationEngine()
eligibility_engine = EligibilityEngine()
ai_assistant = get_ai_assistant()  # EXPERIMENTAL: AI enhancement layer

# Load schemes once at startup
schemes, _ = load_and_validate_schemes()

# Create router
router = APIRouter()


# Helper function to extract category from scheme
def _get_scheme_category(scheme) -> str:
    """Extract category from scheme name or description."""
    name_lower = scheme.name.lower()
    desc_lower = scheme.description.lower()
    
    if any(word in name_lower or word in desc_lower for word in ["skill", "training", "kaushal", "education", "scholarship"]):
        return "education"
    elif any(word in name_lower or word in desc_lower for word in ["housing", "awas", "home"]):
        return "housing"
    elif any(word in name_lower or word in desc_lower for word in ["pension", "atal"]):
        return "pension"
    elif any(word in name_lower or word in desc_lower for word in ["crop", "fasal", "insurance", "farmer", "agriculture"]):
        return "agriculture"
    elif any(word in name_lower or word in desc_lower for word in ["business", "loan", "mudra", "entrepreneur", "stand-up"]):
        return "entrepreneurship"
    elif any(word in name_lower or word in desc_lower for word in ["girl", "daughter", "sukanya"]):
        return "social_welfare"
    else:
        return "general"


# Request/Response Models
class StartConversationRequest(BaseModel):
    """Request to start a new conversation."""
    language: str = Field(
        default="en",
        description="Language code (en or hi)"
    )


class StartConversationResponse(BaseModel):
    """Response with new session information."""
    session_id: str
    language: str
    greeting: str


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    message: str = Field(..., description="User message text")


class SendMessageResponse(BaseModel):
    """Response with assistant's reply."""
    session_id: str
    response: str
    next_question: Optional[str] = None
    stage: str
    information_complete: bool
    eligible_schemes: Optional[List[Dict]] = None


class ConversationStateResponse(BaseModel):
    """Response with current conversation state."""
    session_id: str
    language: str
    current_stage: str
    messages_count: int
    information_complete: bool
    missing_fields: List[str]
    user_profile: Dict


# Endpoints
@router.post("/start", response_model=StartConversationResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(request: StartConversationRequest):
    """
    Start a new conversation session.
    
    Creates a new session with a unique ID and returns the greeting message.
    
    Requirements: 2.1, 7.1
    """
    try:
        # Start conversation
        state = conversation_engine.start_conversation(language=request.language)
        
        # Get greeting from conversation history
        greeting = state.conversation_history[0].content if state.conversation_history else ""
        
        return StartConversationResponse(
            session_id=state.session_id,
            language=state.language,
            greeting=greeting
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )


@router.post("/{session_id}/message", response_model=SendMessageResponse)
async def send_message(session_id: str, request: SendMessageRequest):
    """
    Send a message in an existing conversation.
    
    Processes the user's message, updates the conversation state,
    and returns the assistant's response.
    
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    # Get session
    state = conversation_engine.get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    try:
        # Add user message
        conversation_engine.add_user_message(state, request.message)
        
        # EXPERIMENTAL: Try AI-powered entity extraction first
        extracted_data = {}
        extraction_confidence = 0.0
        
        if ai_assistant.is_available():
            try:
                extracted_data, extraction_confidence = ai_assistant.extract_user_info(
                    request.message, 
                    state.language
                )
                logger.info(f"AI extraction: {extracted_data} (confidence: {extraction_confidence})")
            except Exception as e:
                logger.error(f"AI extraction error: {e}")
        
        # Apply AI-extracted data if confidence is high enough
        if extraction_confidence >= 0.6 and extracted_data:
            for field, value in extracted_data.items():
                if value is not None:
                    conversation_engine.update_user_profile(state, field, value)
            logger.info("Using AI-extracted data")
        else:
            # FALLBACK: Use rule-based extraction
            message_lower = request.message.lower()
            _extract_and_update_profile(state, message_lower)
            logger.info("Using rule-based extraction (AI confidence too low or unavailable)")
        
        # Determine response
        response_text = ""
        next_question = None
        eligible_schemes_data = None
        
        # Check if information is complete
        if conversation_engine.is_information_complete(state):
            # Transition to eligibility if not already there
            if state.current_stage == "info_collection":
                conversation_engine.transition_to_eligibility(state)
                
                # Determine eligibility
                results = eligibility_engine.determine_eligibility(
                    state.user_profile,
                    schemes
                )
                
                if results:
                    # Format results
                    response_text = f"Great! I found {len(results)} scheme(s) you're eligible for:\n\n"
                    eligible_schemes_data = []
                    
                    for result in results[:3]:  # Show top 3
                        category = _get_scheme_category(result.scheme)
                        
                        # EXPERIMENTAL: Try AI-generated explanation
                        ai_explanation = None
                        if ai_assistant.is_available():
                            try:
                                user_profile_dict = {
                                    "age": state.user_profile.age,
                                    "state": state.user_profile.state,
                                    "education_level": state.user_profile.education_level,
                                    "income_range": state.user_profile.income_range,
                                    "category": state.user_profile.category,
                                    "gender": state.user_profile.gender,
                                    "occupation": state.user_profile.occupation
                                }
                                ai_explanation = ai_assistant.generate_explanation(
                                    result.scheme.name,
                                    result.is_eligible,
                                    result.matching_criteria,
                                    result.missing_criteria,
                                    user_profile_dict,
                                    state.language
                                )
                            except Exception as e:
                                logger.error(f"AI explanation error: {e}")
                        
                        # Use AI explanation if available, otherwise use template
                        explanation = ai_explanation if ai_explanation else result.explanation
                        
                        response_text += f"✅ {result.scheme.name}\n{explanation}\n\n"
                        eligible_schemes_data.append({
                            "id": result.scheme.id,
                            "name": result.scheme.name,
                            "name_hi": result.scheme.name_translations.get("hi", result.scheme.name),
                            "category": category,
                            "confidence": result.confidence,
                            "explanation": explanation
                        })
                    
                    conversation_engine.transition_to_guidance(state)
                else:
                    response_text = "I couldn't find any schemes matching your profile at the moment. Let me ask a few more questions to help you better."
                    state.current_stage = "info_collection"
            else:
                response_text = "Is there anything else you'd like to know about these schemes?"
        else:
            # Get next question
            next_question = conversation_engine.get_next_question(state)
            if next_question:
                response_text = next_question
            else:
                response_text = "Thank you for providing that information."
        
        # Add assistant response
        conversation_engine.add_assistant_message(state, response_text)
        
        return SendMessageResponse(
            session_id=session_id,
            response=response_text,
            next_question=next_question if state.current_stage == "info_collection" else None,
            stage=state.current_stage,
            information_complete=conversation_engine.is_information_complete(state),
            eligible_schemes=eligible_schemes_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/{session_id}", response_model=ConversationStateResponse)
async def get_conversation_state(session_id: str):
    """
    Get the current state of a conversation.
    
    Returns conversation metadata and user profile information.
    
    Requirements: 7.1
    """
    state = conversation_engine.get_session(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired"
        )
    
    summary = conversation_engine.get_conversation_summary(state)
    
    return ConversationStateResponse(**summary)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_conversation(session_id: str):
    """
    End a conversation session and cleanup.
    
    Removes the session from memory.
    
    Requirements: 7.2
    """
    success = conversation_engine.end_conversation(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return None


@router.get("/ai/status")
async def get_ai_status():
    """
    EXPERIMENTAL: Get AI assistant status.
    
    Returns information about AI capabilities and availability.
    """
    return ai_assistant.get_status()


# Helper function for simple entity extraction (MVP)
def _extract_and_update_profile(state, message_lower: str):
    """
    Simple entity extraction from user message.
    
    This is a basic implementation for MVP. Task 6 will add proper NLU.
    """
    # Extract age
    import re
    age_match = re.search(r'\b(\d{1,2})\b', message_lower)
    if age_match and state.user_profile.age is None:
        age = int(age_match.group(1))
        if 1 <= age <= 120:
            conversation_engine.update_user_profile(state, "age", age)
    
    # Extract state (simple keyword matching)
    states = {
        "maharashtra": "Maharashtra",
        "karnataka": "Karnataka",
        "delhi": "Delhi",
        "tamil nadu": "Tamil Nadu",
        "west bengal": "West Bengal",
        "gujarat": "Gujarat",
        "rajasthan": "Rajasthan",
        "uttar pradesh": "Uttar Pradesh"
    }
    for key, value in states.items():
        if key in message_lower and state.user_profile.state is None:
            conversation_engine.update_user_profile(state, "state", value)
            break
    
    # Extract education
    if any(word in message_lower for word in ["graduate", "degree", "bachelor"]) and state.user_profile.education_level is None:
        conversation_engine.update_user_profile(state, "education_level", "graduate")
    elif any(word in message_lower for word in ["12th", "12", "intermediate"]) and state.user_profile.education_level is None:
        conversation_engine.update_user_profile(state, "education_level", "12th_pass")
    elif any(word in message_lower for word in ["10th", "10", "matriculation"]) and state.user_profile.education_level is None:
        conversation_engine.update_user_profile(state, "education_level", "10th_pass")
    
    # Extract income
    if any(word in message_lower for word in ["below 1 lakh", "less than 1 lakh", "under 1 lakh"]) and state.user_profile.income_range is None:
        conversation_engine.update_user_profile(state, "income_range", "below_1lakh")
    elif any(word in message_lower for word in ["1-3 lakh", "1 to 3 lakh"]) and state.user_profile.income_range is None:
        conversation_engine.update_user_profile(state, "income_range", "1-3lakh")
    
    # Extract category
    if any(word in message_lower for word in ["sc", "scheduled caste"]) and state.user_profile.category is None:
        conversation_engine.update_user_profile(state, "category", "sc")
    elif any(word in message_lower for word in ["st", "scheduled tribe"]) and state.user_profile.category is None:
        conversation_engine.update_user_profile(state, "category", "st")
    elif any(word in message_lower for word in ["obc", "other backward"]) and state.user_profile.category is None:
        conversation_engine.update_user_profile(state, "category", "obc")
    elif "general" in message_lower and state.user_profile.category is None:
        conversation_engine.update_user_profile(state, "category", "general")
    
    # Extract gender
    if any(word in message_lower for word in ["male", "man", "boy"]) and state.user_profile.gender is None:
        conversation_engine.update_user_profile(state, "gender", "male")
    elif any(word in message_lower for word in ["female", "woman", "girl"]) and state.user_profile.gender is None:
        conversation_engine.update_user_profile(state, "gender", "female")
    
    # Extract occupation
    if "student" in message_lower and state.user_profile.occupation is None:
        conversation_engine.update_user_profile(state, "occupation", "student")
    elif "farmer" in message_lower and state.user_profile.occupation is None:
        conversation_engine.update_user_profile(state, "occupation", "farmer")
    elif any(word in message_lower for word in ["unemployed", "jobless"]) and state.user_profile.occupation is None:
        conversation_engine.update_user_profile(state, "occupation", "unemployed")
