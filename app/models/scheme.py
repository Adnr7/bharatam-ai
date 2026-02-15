"""Scheme and eligibility data models."""

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class EligibilityCriteria(BaseModel):
    """
    Eligibility criteria for a government scheme.
    None values indicate no restriction for that criterion.
    
    Validates: Requirements 3.1, 3.2 (Eligibility Determination)
    """
    
    min_age: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum age requirement (None means no minimum)"
    )
    
    max_age: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum age requirement (None means no maximum)"
    )
    
    states: Optional[List[str]] = Field(
        None,
        description="List of eligible states (None means all states)"
    )
    
    education_levels: Optional[List[str]] = Field(
        None,
        description="List of eligible education levels (None means all levels)"
    )
    
    income_max: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum annual income in rupees (None means no limit)"
    )
    
    categories: Optional[List[str]] = Field(
        None,
        description="List of eligible categories: general, obc, sc, st (None means all)"
    )
    
    gender: Optional[str] = Field(
        None,
        description="Required gender: male, female, other (None means all)"
    )
    
    occupations: Optional[List[str]] = Field(
        None,
        description="List of eligible occupations (None means all)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "min_age": 18,
                "max_age": 35,
                "states": ["Karnataka", "Tamil Nadu"],
                "education_levels": ["graduate", "postgraduate"],
                "income_max": 300000,
                "categories": ["general", "obc"],
                "gender": None,
                "occupations": ["student", "unemployed"]
            }
        }


class Scheme(BaseModel):
    """
    Government welfare scheme with eligibility criteria and details.
    
    Validates: Requirements 6.1 (Knowledge Base Management)
    """
    
    id: str = Field(
        ...,
        description="Unique identifier for the scheme"
    )
    
    name: str = Field(
        ...,
        description="Scheme name in English"
    )
    
    name_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Scheme name translations (language_code: translated_name)"
    )
    
    description: str = Field(
        ...,
        description="Detailed description of the scheme"
    )
    
    description_translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Description translations (language_code: translated_description)"
    )
    
    eligibility: EligibilityCriteria = Field(
        ...,
        description="Eligibility criteria for the scheme"
    )
    
    benefits: str = Field(
        ...,
        description="Benefits provided by the scheme"
    )
    
    required_documents: List[str] = Field(
        default_factory=list,
        description="List of required documents for application"
    )
    
    application_process: str = Field(
        ...,
        description="Step-by-step application process"
    )
    
    application_url: Optional[str] = Field(
        None,
        description="Online application portal URL"
    )
    
    office_location: Optional[str] = Field(
        None,
        description="Physical office location for application"
    )
    
    deadline: Optional[datetime] = Field(
        None,
        description="Application deadline (if applicable)"
    )
    
    source_url: str = Field(
        ...,
        description="Source URL of official government document"
    )
    
    last_updated: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    
    embedding: Optional[List[float]] = Field(
        None,
        description="Vector embedding for semantic search"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "pmkvy-2023",
                "name": "Pradhan Mantri Kaushal Vikas Yojana",
                "name_translations": {
                    "hi": "प्रधानमंत्री कौशल विकास योजना"
                },
                "description": "Skill development scheme for youth",
                "description_translations": {
                    "hi": "युवाओं के लिए कौशल विकास योजना"
                },
                "eligibility": {
                    "min_age": 18,
                    "max_age": 35,
                    "states": None,
                    "education_levels": ["10th_pass", "12th_pass"],
                    "income_max": None,
                    "categories": None,
                    "gender": None,
                    "occupations": ["student", "unemployed"]
                },
                "benefits": "Free skill training and certification",
                "required_documents": ["Aadhar Card", "Educational Certificate"],
                "application_process": "1. Visit portal 2. Register 3. Select course",
                "application_url": "https://pmkvyofficial.org",
                "office_location": None,
                "deadline": None,
                "source_url": "https://pmkvyofficial.org",
                "last_updated": "2023-01-01T00:00:00"
            }
        }


class EligibilityResult(BaseModel):
    """
    Result of eligibility determination for a scheme.
    
    Validates: Requirements 3.1, 3.3, 4.1 (Eligibility and Explanation)
    """
    
    scheme: Scheme = Field(
        ...,
        description="The scheme being evaluated"
    )
    
    is_eligible: bool = Field(
        ...,
        description="Whether the user is eligible for this scheme"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    
    matching_criteria: List[str] = Field(
        default_factory=list,
        description="List of criteria that the user satisfies"
    )
    
    missing_criteria: List[str] = Field(
        default_factory=list,
        description="List of criteria that the user does not satisfy"
    )
    
    explanation: str = Field(
        default="",
        description="Human-readable explanation of eligibility determination"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "scheme": {
                    "id": "pmkvy-2023",
                    "name": "Pradhan Mantri Kaushal Vikas Yojana"
                },
                "is_eligible": True,
                "confidence": 0.95,
                "matching_criteria": [
                    "Age is within range (18-35)",
                    "Education level matches (12th_pass)",
                    "Occupation matches (student)"
                ],
                "missing_criteria": [],
                "explanation": "You are eligible because you are 25 years old, have completed 12th grade, and are a student."
            }
        }
