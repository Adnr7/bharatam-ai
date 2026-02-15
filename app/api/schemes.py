"""
Schemes API endpoints.

Provides REST API for querying government schemes.

Requirements: 6.2
"""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from app.services.data_loader import load_and_validate_schemes
from app.services.knowledge_base import KnowledgeBase
from app.models.user import UserProfile
from app.services.eligibility import EligibilityEngine

# Initialize services
schemes_data, stats = load_and_validate_schemes()
kb = KnowledgeBase()
eligibility_engine = EligibilityEngine()

# Index schemes for semantic search (if model is available)
try:
    if schemes_data:
        kb.index_schemes(schemes_data)
        print(f"✓ Indexed {len(schemes_data)} schemes for semantic search")
except Exception as e:
    print(f"Warning: Could not index schemes for semantic search: {e}")
    print("Semantic search will not be available, but filtering will still work.")

# Create router
router = APIRouter()


# Response Models
class SchemeResponse(BaseModel):
    """Response model for a single scheme."""
    id: str
    name: str
    name_hi: str
    description: str
    description_hi: str
    category: str  # Derived from name/description
    benefits: str
    benefits_hi: str
    required_documents: List[str]
    application_process: str
    application_process_hi: str
    official_url: Optional[str] = None
    eligibility: Dict


class SchemesListResponse(BaseModel):
    """Response model for list of schemes."""
    total: int
    schemes: List[SchemeResponse]


class SearchSchemesRequest(BaseModel):
    """Request to search schemes by criteria."""
    query: Optional[str] = Field(None, description="Search query text")
    state: Optional[str] = Field(None, description="Filter by state")
    category: Optional[str] = Field(None, description="Filter by category")
    min_age: Optional[int] = Field(None, description="User's age")
    max_age: Optional[int] = Field(None, description="User's age")
    top_k: int = Field(default=10, description="Number of results to return")


class SearchSchemesResponse(BaseModel):
    """Response with search results."""
    total: int
    schemes: List[Dict]


class CheckEligibilityRequest(BaseModel):
    """Request to check eligibility for schemes."""
    age: Optional[int] = None
    state: Optional[str] = None
    education_level: Optional[str] = None
    income_range: Optional[str] = None
    category: Optional[str] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None


class EligibilityResultResponse(BaseModel):
    """Response with eligibility results."""
    total_eligible: int
    results: List[Dict]


# Helper function to extract category from scheme name/description
def _get_scheme_category(scheme) -> str:
    """
    Extract category from scheme name or description.
    This is a temporary solution until category field is added to the model.
    """
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


def _scheme_to_response(scheme) -> SchemeResponse:
    """Convert Scheme model to SchemeResponse with derived category."""
    # Get Hindi translations
    name_hi = scheme.name_translations.get("hi", scheme.name)
    desc_hi = scheme.description_translations.get("hi", scheme.description)
    benefits_hi = scheme.name_translations.get("hi", scheme.benefits)  # Fallback
    app_process_hi = scheme.description_translations.get("hi", scheme.application_process)  # Fallback
    
    return SchemeResponse(
        id=scheme.id,
        name=scheme.name,
        name_hi=name_hi,
        description=scheme.description,
        description_hi=desc_hi,
        category=_get_scheme_category(scheme),
        benefits=scheme.benefits,
        benefits_hi=benefits_hi,
        required_documents=scheme.required_documents,
        application_process=scheme.application_process,
        application_process_hi=app_process_hi,
        official_url=scheme.application_url or scheme.source_url,
        eligibility={
            "min_age": scheme.eligibility.min_age,
            "max_age": scheme.eligibility.max_age,
            "states": scheme.eligibility.states,
            "education_levels": scheme.eligibility.education_levels,
            "income_max": scheme.eligibility.income_max,
            "categories": scheme.eligibility.categories,
            "gender": scheme.eligibility.gender,
            "occupations": scheme.eligibility.occupations
        }
    )


# Endpoints
@router.get("/", response_model=SchemesListResponse)
async def list_schemes(
    category: Optional[str] = Query(None, description="Filter by category"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(10, ge=1, le=100, description="Number of schemes to return")
):
    """
    List all available schemes with optional filtering.
    
    Requirements: 6.2
    """
    try:
        filtered_schemes = schemes_data
        
        # Apply filters
        if category:
            filtered_schemes = [
                s for s in filtered_schemes
                if _get_scheme_category(s).lower() == category.lower()
            ]
        
        if state:
            filtered_schemes = [
                s for s in filtered_schemes
                if s.eligibility.states is None or state in (s.eligibility.states or [])
            ]
        
        # Limit results
        filtered_schemes = filtered_schemes[:limit]
        
        # Convert to response format
        schemes_response = [_scheme_to_response(s) for s in filtered_schemes]
        
        return SchemesListResponse(
            total=len(schemes_response),
            schemes=schemes_response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list schemes: {str(e)}"
        )


@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(scheme_id: str):
    """
    Get details of a specific scheme by ID.
    
    Requirements: 6.2
    """
    # Find scheme
    scheme = next((s for s in schemes_data if s.id == scheme_id), None)
    
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme with ID '{scheme_id}' not found"
        )
    
    return _scheme_to_response(scheme)


@router.post("/search", response_model=SearchSchemesResponse)
async def search_schemes(request: SearchSchemesRequest):
    """
    Search schemes using semantic search and filters.
    
    Uses the RAG system for intelligent scheme retrieval.
    
    Requirements: 6.2
    """
    try:
        # Build filters
        filters = {}
        if request.state:
            filters["state"] = request.state
        if request.category:
            filters["category"] = request.category
        if request.min_age:
            filters["min_age"] = request.min_age
        if request.max_age:
            filters["max_age"] = request.max_age
        
        # Perform search
        if request.query and kb.index.ntotal > 0:
            # Semantic search
            results = kb.retrieve_schemes(
                query=request.query,
                top_k=request.top_k,
                filters=filters if filters else None
            )
            
            schemes_response = [
                {
                    "id": scheme.id,
                    "name": scheme.name,
                    "name_hi": scheme.name_translations.get("hi", scheme.name),
                    "description": scheme.description,
                    "category": _get_scheme_category(scheme),
                    "similarity_score": float(score)
                }
                for scheme, score in results
            ]
        else:
            # Simple filtering
            filtered = schemes_data
            if request.state:
                filtered = [
                    s for s in filtered
                    if s.eligibility.states is None or request.state in (s.eligibility.states or [])
                ]
            if request.category:
                filtered = [s for s in filtered if _get_scheme_category(s).lower() == request.category.lower()]
            
            filtered = filtered[:request.top_k]
            
            schemes_response = [
                {
                    "id": s.id,
                    "name": s.name,
                    "name_hi": s.name_translations.get("hi", s.name),
                    "description": s.description,
                    "category": _get_scheme_category(s),
                    "similarity_score": 1.0
                }
                for s in filtered
            ]
        
        return SearchSchemesResponse(
            total=len(schemes_response),
            schemes=schemes_response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search schemes: {str(e)}"
        )


@router.post("/check-eligibility", response_model=EligibilityResultResponse)
async def check_eligibility(request: CheckEligibilityRequest):
    """
    Check eligibility for schemes based on user profile.
    
    Requirements: 3.1, 3.2, 3.3
    """
    try:
        # Create user profile
        user_profile = UserProfile(
            age=request.age,
            state=request.state,
            education_level=request.education_level,
            income_range=request.income_range,
            category=request.category,
            gender=request.gender,
            occupation=request.occupation
        )
        
        # Check eligibility
        results = eligibility_engine.determine_eligibility(user_profile, schemes_data)
        
        # Format results
        results_response = [
            {
                "scheme_id": result.scheme.id,
                "scheme_name": result.scheme.name,
                "scheme_name_hi": result.scheme.name_translations.get("hi", result.scheme.name),
                "category": _get_scheme_category(result.scheme),
                "is_eligible": result.is_eligible,
                "confidence": result.confidence,
                "explanation": result.explanation,
                "matching_criteria": result.matching_criteria
            }
            for result in results
        ]
        
        return EligibilityResultResponse(
            total_eligible=len(results),
            results=results_response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check eligibility: {str(e)}"
        )


@router.get("/stats/summary")
async def get_stats():
    """
    Get statistics about available schemes.
    
    Returns counts by category, state coverage, etc.
    """
    try:
        categories = {}
        states = set()
        
        for scheme in schemes_data:
            # Count by category
            category = _get_scheme_category(scheme)
            categories[category] = categories.get(category, 0) + 1
            
            # Collect states
            if scheme.eligibility.states:
                states.update(scheme.eligibility.states)
        
        return {
            "total_schemes": len(schemes_data),
            "categories": categories,
            "states_covered": list(states),
            "total_states": len(states)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
