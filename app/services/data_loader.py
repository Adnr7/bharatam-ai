"""Data loader for government schemes."""

import json
from pathlib import Path
from typing import List
from app.models.scheme import Scheme


class SchemeDataLoader:
    """
    Loads and validates government scheme data from JSON files.
    
    Validates: Requirements 6.1 (Knowledge Base Management)
    """
    
    def __init__(self, data_path: str = "data/schemes.json"):
        """Initialize the data loader with path to schemes JSON file."""
        self.data_path = Path(data_path)
    
    def load_schemes(self) -> List[Scheme]:
        """
        Load schemes from JSON file and validate using Pydantic models.
        
        Returns:
            List of validated Scheme objects
            
        Raises:
            FileNotFoundError: If the data file doesn't exist
            ValueError: If the JSON is invalid or schemes don't validate
        """
        if not self.data_path.exists():
            raise FileNotFoundError(f"Scheme data file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            schemes_data = json.load(f)
        
        if not isinstance(schemes_data, list):
            raise ValueError("Schemes data must be a JSON array")
        
        schemes = []
        for idx, scheme_data in enumerate(schemes_data):
            try:
                scheme = Scheme(**scheme_data)
                schemes.append(scheme)
            except Exception as e:
                raise ValueError(f"Invalid scheme at index {idx}: {str(e)}")
        
        return schemes
    
    def validate_schemes(self, schemes: List[Scheme]) -> dict:
        """
        Validate loaded schemes and return statistics.
        
        Args:
            schemes: List of Scheme objects to validate
            
        Returns:
            Dictionary with validation statistics
        """
        stats = {
            "total_schemes": len(schemes),
            "schemes_with_translations": 0,
            "schemes_with_deadlines": 0,
            "schemes_with_age_restrictions": 0,
            "schemes_with_income_restrictions": 0,
            "schemes_with_category_restrictions": 0,
            "schemes_with_state_restrictions": 0,
            "unique_states": set(),
            "unique_categories": set(),
            "unique_occupations": set()
        }
        
        for scheme in schemes:
            # Check translations
            if scheme.name_translations or scheme.description_translations:
                stats["schemes_with_translations"] += 1
            
            # Check deadline
            if scheme.deadline:
                stats["schemes_with_deadlines"] += 1
            
            # Check eligibility criteria
            if scheme.eligibility.min_age or scheme.eligibility.max_age:
                stats["schemes_with_age_restrictions"] += 1
            
            if scheme.eligibility.income_max:
                stats["schemes_with_income_restrictions"] += 1
            
            if scheme.eligibility.categories:
                stats["schemes_with_category_restrictions"] += 1
                stats["unique_categories"].update(scheme.eligibility.categories)
            
            if scheme.eligibility.states:
                stats["schemes_with_state_restrictions"] += 1
                stats["unique_states"].update(scheme.eligibility.states)
            
            if scheme.eligibility.occupations:
                stats["unique_occupations"].update(scheme.eligibility.occupations)
        
        # Convert sets to lists for JSON serialization
        stats["unique_states"] = list(stats["unique_states"])
        stats["unique_categories"] = list(stats["unique_categories"])
        stats["unique_occupations"] = list(stats["unique_occupations"])
        
        return stats


def load_and_validate_schemes(data_path: str = "data/schemes.json") -> tuple[List[Scheme], dict]:
    """
    Convenience function to load and validate schemes in one call.
    
    Args:
        data_path: Path to schemes JSON file
        
    Returns:
        Tuple of (schemes list, validation statistics)
    """
    loader = SchemeDataLoader(data_path)
    schemes = loader.load_schemes()
    stats = loader.validate_schemes(schemes)
    return schemes, stats


if __name__ == "__main__":
    # Test the data loader
    try:
        schemes, stats = load_and_validate_schemes()
        print(f"✅ Successfully loaded {stats['total_schemes']} schemes")
        print(f"\nValidation Statistics:")
        print(f"  - Schemes with translations: {stats['schemes_with_translations']}")
        print(f"  - Schemes with deadlines: {stats['schemes_with_deadlines']}")
        print(f"  - Schemes with age restrictions: {stats['schemes_with_age_restrictions']}")
        print(f"  - Schemes with income restrictions: {stats['schemes_with_income_restrictions']}")
        print(f"  - Schemes with category restrictions: {stats['schemes_with_category_restrictions']}")
        print(f"  - Unique categories: {', '.join(stats['unique_categories']) if stats['unique_categories'] else 'None'}")
        print(f"  - Unique occupations: {', '.join(stats['unique_occupations']) if stats['unique_occupations'] else 'None'}")
        
        print(f"\n📋 Loaded Schemes:")
        for scheme in schemes:
            print(f"  - {scheme.name} (ID: {scheme.id})")
    except Exception as e:
        print(f"❌ Error loading schemes: {str(e)}")
