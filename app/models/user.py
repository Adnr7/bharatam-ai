"""User profile data model."""

from typing import Optional
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """
    User profile containing information collected during conversation.
    This data is session-only and not persisted beyond the active conversation.
    
    Validates: Requirements 7.1, 7.2 (Privacy and Data Protection)
    """
    
    age: Optional[int] = Field(
        None,
        ge=0,
        le=120,
        description="User's age in years"
    )
    
    state: Optional[str] = Field(
        None,
        description="User's state of residence (e.g., 'Maharashtra', 'Karnataka')"
    )
    
    education_level: Optional[str] = Field(
        None,
        description="User's education level: 'below_10th', '10th_pass', '12th_pass', 'graduate', 'postgraduate'"
    )
    
    income_range: Optional[str] = Field(
        None,
        description="User's annual income range: 'below_1lakh', '1-3lakh', '3-5lakh', '5-8lakh', 'above_8lakh'"
    )
    
    category: Optional[str] = Field(
        None,
        description="User's category: 'general', 'obc', 'sc', 'st'"
    )
    
    occupation: Optional[str] = Field(
        None,
        description="User's occupation: 'student', 'farmer', 'unemployed', 'employed', 'self_employed'"
    )
    
    gender: Optional[str] = Field(
        None,
        description="User's gender: 'male', 'female', 'other'"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "age": 25,
                "state": "Karnataka",
                "education_level": "graduate",
                "income_range": "1-3lakh",
                "category": "general",
                "occupation": "student",
                "gender": "female"
            }
        }
    
    def is_complete_for_eligibility(self) -> bool:
        """
        Check if the profile has minimum required information for eligibility determination.
        At minimum, we need age and state.
        """
        return self.age is not None and self.state is not None
    
    def get_missing_fields(self) -> list[str]:
        """Return list of fields that are None."""
        missing = []
        if self.age is None:
            missing.append("age")
        if self.state is None:
            missing.append("state")
        if self.education_level is None:
            missing.append("education_level")
        if self.income_range is None:
            missing.append("income_range")
        if self.category is None:
            missing.append("category")
        if self.occupation is None:
            missing.append("occupation")
        if self.gender is None:
            missing.append("gender")
        return missing
