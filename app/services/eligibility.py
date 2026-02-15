"""Eligibility determination engine for government schemes."""

from typing import List
from app.models.user import UserProfile
from app.models.scheme import Scheme, EligibilityResult


class EligibilityEngine:
    """
    Rule-based eligibility determination engine.
    
    Validates: Requirements 3.1, 3.2, 3.3, 4.1, 4.4 (Eligibility Determination and Explanation)
    """
    
    # Income range mappings (in rupees per year)
    INCOME_RANGES = {
        "below_1lakh": 100000,
        "1-3lakh": 300000,
        "3-5lakh": 500000,
        "5-8lakh": 800000,
        "above_8lakh": float('inf')
    }
    
    def check_single_scheme(self, user_profile: UserProfile, scheme: Scheme) -> EligibilityResult:
        """
        Check if a user is eligible for a single scheme.
        
        Args:
            user_profile: User's profile information
            scheme: Scheme to check eligibility for
            
        Returns:
            EligibilityResult with eligibility status and explanation
            
        Validates: Requirements 3.1, 3.2
        """
        eligibility = scheme.eligibility
        matching_criteria = []
        missing_criteria = []
        is_eligible = True
        
        # Check age criteria
        if eligibility.min_age is not None or eligibility.max_age is not None:
            if user_profile.age is None:
                missing_criteria.append("Age information required")
                is_eligible = False
            else:
                age_match = True
                if eligibility.min_age is not None and user_profile.age < eligibility.min_age:
                    missing_criteria.append(f"Minimum age requirement: {eligibility.min_age} years")
                    is_eligible = False
                    age_match = False
                if eligibility.max_age is not None and user_profile.age > eligibility.max_age:
                    missing_criteria.append(f"Maximum age requirement: {eligibility.max_age} years")
                    is_eligible = False
                    age_match = False
                
                if age_match:
                    age_range = f"{eligibility.min_age or 0}-{eligibility.max_age or '∞'}"
                    matching_criteria.append(f"Age is within range ({age_range} years)")
        
        # Check state criteria
        if eligibility.states is not None:
            if user_profile.state is None:
                missing_criteria.append("State information required")
                is_eligible = False
            elif user_profile.state not in eligibility.states:
                missing_criteria.append(f"Scheme only available in: {', '.join(eligibility.states)}")
                is_eligible = False
            else:
                matching_criteria.append(f"State matches ({user_profile.state})")
        
        # Check education criteria
        if eligibility.education_levels is not None:
            if user_profile.education_level is None:
                missing_criteria.append("Education level information required")
                is_eligible = False
            elif user_profile.education_level not in eligibility.education_levels:
                missing_criteria.append(f"Required education: {', '.join(eligibility.education_levels)}")
                is_eligible = False
            else:
                matching_criteria.append(f"Education level matches ({user_profile.education_level})")
        
        # Check income criteria
        if eligibility.income_max is not None:
            if user_profile.income_range is None:
                missing_criteria.append("Income information required")
                is_eligible = False
            else:
                user_income = self.INCOME_RANGES.get(user_profile.income_range, float('inf'))
                if user_income > eligibility.income_max:
                    missing_criteria.append(f"Maximum income requirement: Rs. {eligibility.income_max:,} per year")
                    is_eligible = False
                else:
                    matching_criteria.append(f"Income is within limit (Rs. {eligibility.income_max:,} per year)")
        
        # Check category criteria
        if eligibility.categories is not None:
            if user_profile.category is None:
                missing_criteria.append("Category information required")
                is_eligible = False
            elif user_profile.category not in eligibility.categories:
                missing_criteria.append(f"Scheme only for: {', '.join(eligibility.categories).upper()}")
                is_eligible = False
            else:
                matching_criteria.append(f"Category matches ({user_profile.category.upper()})")
        
        # Check gender criteria
        if eligibility.gender is not None:
            if user_profile.gender is None:
                missing_criteria.append("Gender information required")
                is_eligible = False
            elif user_profile.gender != eligibility.gender:
                missing_criteria.append(f"Scheme only for: {eligibility.gender}")
                is_eligible = False
            else:
                matching_criteria.append(f"Gender matches ({user_profile.gender})")
        
        # Check occupation criteria
        if eligibility.occupations is not None:
            if user_profile.occupation is None:
                missing_criteria.append("Occupation information required")
                is_eligible = False
            elif user_profile.occupation not in eligibility.occupations:
                missing_criteria.append(f"Scheme only for: {', '.join(eligibility.occupations)}")
                is_eligible = False
            else:
                matching_criteria.append(f"Occupation matches ({user_profile.occupation})")
        
        # Calculate confidence score (0.0 to 1.0)
        total_criteria = len(matching_criteria) + len(missing_criteria)
        confidence = len(matching_criteria) / total_criteria if total_criteria > 0 else 0.0
        
        # Generate explanation
        explanation = self.generate_eligibility_explanation(
            scheme, is_eligible, matching_criteria, missing_criteria
        )
        
        return EligibilityResult(
            scheme=scheme,
            is_eligible=is_eligible,
            confidence=confidence,
            matching_criteria=matching_criteria,
            missing_criteria=missing_criteria,
            explanation=explanation
        )
    
    def determine_eligibility(self, user_profile: UserProfile, schemes: List[Scheme]) -> List[EligibilityResult]:
        """
        Determine eligibility for all schemes and return eligible ones.
        
        Args:
            user_profile: User's profile information
            schemes: List of schemes to check
            
        Returns:
            List of EligibilityResult for eligible schemes, ranked by relevance
            
        Validates: Requirements 3.1, 3.2, 3.3
        """
        results = []
        
        for scheme in schemes:
            result = self.check_single_scheme(user_profile, scheme)
            if result.is_eligible:
                results.append(result)
        
        # Rank schemes by number of matching criteria (more matches = higher rank)
        results.sort(key=lambda r: len(r.matching_criteria), reverse=True)
        
        return results
    
    def generate_eligibility_explanation(
        self, 
        scheme: Scheme, 
        is_eligible: bool, 
        matching_criteria: List[str], 
        missing_criteria: List[str]
    ) -> str:
        """
        Generate a human-readable explanation of eligibility.
        
        Args:
            scheme: The scheme being evaluated
            is_eligible: Whether the user is eligible
            matching_criteria: List of criteria that matched
            missing_criteria: List of criteria that didn't match
            
        Returns:
            Human-readable explanation string
            
        Validates: Requirements 4.1, 4.4
        """
        if is_eligible:
            explanation = f"✅ You are eligible for {scheme.name}!\n\n"
            explanation += "You meet the following requirements:\n"
            for criterion in matching_criteria:
                explanation += f"  • {criterion}\n"
        else:
            explanation = f"❌ You are not eligible for {scheme.name}.\n\n"
            if missing_criteria:
                explanation += "Reasons:\n"
                for criterion in missing_criteria:
                    explanation += f"  • {criterion}\n"
        
        return explanation.strip()
