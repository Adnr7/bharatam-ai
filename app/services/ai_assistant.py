"""
EXPERIMENTAL AI Assistant Layer for Bharatam AI

This module provides LLM-powered enhancements for natural language understanding
and conversational response generation. It acts as a thin layer on top of the
existing rule-based system.

SAFETY: All AI features have fallback to deterministic logic. The core eligibility
engine and conversation flow remain unchanged.

Requirements: OpenAI API (or compatible endpoint)
"""

import json
import os
from typing import Dict, Optional, Tuple, Any
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class AIAssistant:
    """
    EXPERIMENTAL: LLM-powered assistant for natural language understanding
    and response generation.
    
    This is a thin AI layer that enhances the existing system without
    replacing core logic.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the AI assistant.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-3.5-turbo for speed/cost)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info(f"AI Assistant initialized with model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            logger.warning("AI Assistant disabled: No API key provided")
            self.client = None
    
    def extract_user_info(self, user_message: str, language: str = "en") -> Tuple[Dict[str, Any], float]:
        """
        EXPERIMENTAL: Extract structured user information from free-form text.
        
        Uses LLM to parse natural language and extract profile fields.
        
        Args:
            user_message: User's message text
            language: Language code (en or hi)
            
        Returns:
            Tuple of (extracted_data, confidence_score)
            - extracted_data: Dict with fields like age, state, education_level, etc.
            - confidence_score: 0.0 to 1.0 indicating extraction confidence
            
        Fallback: Returns empty dict with 0.0 confidence if AI fails
        """
        if not self.enabled:
            return {}, 0.0
        
        try:
            prompt = self._build_extraction_prompt(user_message, language)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant. Extract structured information from user messages and return valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=300,
                timeout=5.0  # 5 second timeout
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            data = json.loads(content)
            
            # Validate and normalize
            extracted = self._normalize_extracted_data(data)
            confidence = data.get("confidence", 0.5)
            
            logger.info(f"AI extraction successful: {extracted} (confidence: {confidence})")
            return extracted, float(confidence)
            
        except json.JSONDecodeError as e:
            logger.error(f"AI extraction failed - invalid JSON: {e}")
            return {}, 0.0
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            return {}, 0.0
    
    def _build_extraction_prompt(self, user_message: str, language: str) -> str:
        """Build prompt for information extraction."""
        return f"""Extract user profile information from this message: "{user_message}"

Language: {language}

Extract these fields if present:
- age: integer (1-120)
- state: string (Indian state name in English)
- education_level: one of ["below_10th", "10th_pass", "12th_pass", "graduate", "postgraduate"]
- income_range: one of ["below_1lakh", "1-3lakh", "3-5lakh", "5-8lakh", "above_8lakh"]
- category: one of ["general", "sc", "st", "obc"]
- gender: one of ["male", "female", "other"]
- occupation: one of ["student", "farmer", "self_employed", "unemployed", "employed", "other"]

Return ONLY valid JSON in this format:
{{
  "age": <integer or null>,
  "state": "<state name or null>",
  "education_level": "<value or null>",
  "income_range": "<value or null>",
  "category": "<value or null>",
  "gender": "<value or null>",
  "occupation": "<value or null>",
  "confidence": <0.0 to 1.0>
}}

If a field is not mentioned, use null. Set confidence based on clarity of information."""
    
    def _normalize_extracted_data(self, data: Dict) -> Dict[str, Any]:
        """Normalize and validate extracted data."""
        normalized = {}
        
        # Age validation
        if "age" in data and data["age"] is not None:
            try:
                age = int(data["age"])
                if 1 <= age <= 120:
                    normalized["age"] = age
            except (ValueError, TypeError):
                pass
        
        # State normalization
        if "state" in data and data["state"]:
            normalized["state"] = str(data["state"]).strip()
        
        # Education level
        valid_education = ["below_10th", "10th_pass", "12th_pass", "graduate", "postgraduate"]
        if "education_level" in data and data["education_level"] in valid_education:
            normalized["education_level"] = data["education_level"]
        
        # Income range
        valid_income = ["below_1lakh", "1-3lakh", "3-5lakh", "5-8lakh", "above_8lakh"]
        if "income_range" in data and data["income_range"] in valid_income:
            normalized["income_range"] = data["income_range"]
        
        # Category
        valid_category = ["general", "sc", "st", "obc"]
        if "category" in data and data["category"] in valid_category:
            normalized["category"] = data["category"]
        
        # Gender
        valid_gender = ["male", "female", "other"]
        if "gender" in data and data["gender"] in valid_gender:
            normalized["gender"] = data["gender"]
        
        # Occupation
        valid_occupation = ["student", "farmer", "self_employed", "unemployed", "employed", "other"]
        if "occupation" in data and data["occupation"] in valid_occupation:
            normalized["occupation"] = data["occupation"]
        
        return normalized

    
    def generate_explanation(
        self,
        scheme_name: str,
        is_eligible: bool,
        matching_criteria: list,
        missing_criteria: list,
        user_profile: Dict[str, Any],
        language: str = "en"
    ) -> Optional[str]:
        """
        EXPERIMENTAL: Generate human-friendly eligibility explanation.
        
        Uses LLM to create personalized, conversational explanations based on
        deterministic eligibility results.
        
        Args:
            scheme_name: Name of the scheme
            is_eligible: Whether user is eligible (from rule-based engine)
            matching_criteria: List of criteria that matched
            missing_criteria: List of criteria that didn't match
            user_profile: User's profile data
            language: Language code (en or hi)
            
        Returns:
            Generated explanation string, or None if AI fails
            
        Fallback: Returns None, caller should use template-based explanation
        """
        if not self.enabled:
            return None
        
        try:
            prompt = self._build_explanation_prompt(
                scheme_name, is_eligible, matching_criteria, 
                missing_criteria, user_profile, language
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful government scheme assistant. Explain eligibility in simple, clear language. Be factual and encouraging."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Slightly higher for natural language
                max_tokens=400,
                timeout=5.0
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info(f"AI explanation generated for {scheme_name}")
            return explanation
            
        except Exception as e:
            logger.error(f"AI explanation generation failed: {e}")
            return None
    
    def _build_explanation_prompt(
        self,
        scheme_name: str,
        is_eligible: bool,
        matching_criteria: list,
        missing_criteria: list,
        user_profile: Dict[str, Any],
        language: str
    ) -> str:
        """Build prompt for explanation generation."""
        status = "eligible" if is_eligible else "not eligible"
        
        prompt = f"""Generate a clear, friendly explanation for why a user is {status} for the "{scheme_name}" government scheme.

User Profile:
{json.dumps(user_profile, indent=2)}

Matching Criteria:
{json.dumps(matching_criteria, indent=2)}

Missing Criteria:
{json.dumps(missing_criteria, indent=2)}

Language: {language}

Requirements:
1. Use simple, conversational language
2. Be encouraging and helpful
3. Explain WHY they qualify or don't qualify
4. If not eligible, suggest what they could do
5. Keep it under 150 words
6. Use appropriate language ({language})
7. DO NOT invent facts or schemes
8. Base explanation ONLY on the provided criteria

Generate the explanation:"""
        
        return prompt
    
    def generate_conversational_response(
        self,
        user_message: str,
        conversation_context: str,
        language: str = "en"
    ) -> Optional[str]:
        """
        EXPERIMENTAL: Generate natural conversational response.
        
        Uses LLM to create contextual, natural responses for general queries
        or clarifications.
        
        Args:
            user_message: User's message
            conversation_context: Summary of conversation so far
            language: Language code
            
        Returns:
            Generated response, or None if AI fails
            
        Fallback: Returns None, caller should use template responses
        """
        if not self.enabled:
            return None
        
        try:
            prompt = f"""You are Bharatam AI, a helpful assistant for Indian government welfare schemes.

Conversation Context:
{conversation_context}

User Message: "{user_message}"

Language: {language}

Generate a helpful, natural response. Keep it brief (2-3 sentences). Be warm and encouraging.
If the user is asking about schemes, acknowledge and guide them through the process.

Response:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are Bharatam AI, a friendly government scheme assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=200,
                timeout=5.0
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if AI assistant is available."""
        return self.enabled
    
    def get_status(self) -> Dict[str, Any]:
        """Get AI assistant status."""
        return {
            "enabled": self.enabled,
            "model": self.model if self.enabled else None,
            "features": {
                "entity_extraction": self.enabled,
                "explanation_generation": self.enabled,
                "conversational_response": self.enabled
            }
        }


# Global instance (lazy initialization)
_ai_assistant: Optional[AIAssistant] = None


def get_ai_assistant() -> AIAssistant:
    """
    Get or create the global AI assistant instance.
    
    Returns:
        AIAssistant instance
    """
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIAssistant()
    return _ai_assistant
