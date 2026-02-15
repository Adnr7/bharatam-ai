"""
Knowledge Base and RAG System for Bharatam AI

This module implements vector database functionality using FAISS for semantic search
over government schemes. It provides embedding generation, indexing, and retrieval
capabilities.

Requirements: 6.1, 6.2
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from app.models.scheme import Scheme


class KnowledgeBase:
    """
    Vector database for semantic search over government schemes.
    
    Uses FAISS for efficient similarity search and sentence-transformers
    for generating embeddings.
    
    Requirements: 6.1, 6.2
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-MiniLM-L3-v2",
        index_path: Optional[str] = None
    ):
        """
        Initialize the knowledge base.
        
        Args:
            model_name: Name of the sentence transformer model to use
                       Default is paraphrase-MiniLM-L3-v2 (small, fast, 61MB)
            index_path: Path to save/load the FAISS index
        """
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.schemes: List[Scheme] = []
        self.index_path = index_path or "data/faiss_index"
        
    def _create_searchable_text(self, scheme: Scheme) -> str:
        """
        Create searchable text from scheme data.
        
        Combines name, description, and benefits for better search.
        
        Args:
            scheme: Scheme object
            
        Returns:
            Combined text for embedding generation
        """
        parts = [
            scheme.name,
            scheme.description,
            f"Benefits: {scheme.benefits}"
        ]
        return " ".join(parts)

    def index_schemes(self, schemes: List[Scheme]) -> None:
        """
        Index schemes into the vector database.
        
        Generates embeddings for each scheme and adds them to the FAISS index.
        
        Args:
            schemes: List of Scheme objects to index
            
        Requirements: 6.1, 6.2
        """
        if not schemes:
            raise ValueError("Cannot index empty scheme list")
        
        # Store schemes
        self.schemes = schemes
        
        # Generate embeddings
        texts = [self._create_searchable_text(scheme) for scheme in schemes]
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        
        # Reset and populate index
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.index.add(embeddings.astype('float32'))
        
    def retrieve_schemes(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Tuple[Scheme, float]]:
        """
        Retrieve relevant schemes using semantic search.
        
        Args:
            query: User query text
            top_k: Number of results to return
            filters: Optional filters (e.g., {"state": "Maharashtra", "category": "education"})
            
        Returns:
            List of (Scheme, similarity_score) tuples, sorted by relevance
            
        Requirements: 6.2
        """
        if not self.schemes:
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)
        
        # Search in FAISS index
        distances, indices = self.index.search(
            query_embedding.astype('float32'),
            min(top_k * 2, len(self.schemes))  # Get more results for filtering
        )
        
        # Collect results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.schemes):
                scheme = self.schemes[idx]
                
                # Apply filters if provided
                if filters:
                    if not self._matches_filters(scheme, filters):
                        continue
                
                # Convert L2 distance to similarity score (lower distance = higher similarity)
                similarity = 1.0 / (1.0 + distance)
                results.append((scheme, float(similarity)))
                
                if len(results) >= top_k:
                    break
        
        return results

    def _matches_filters(self, scheme: Scheme, filters: Dict[str, str]) -> bool:
        """
        Check if a scheme matches the provided filters.
        
        Args:
            scheme: Scheme to check
            filters: Dictionary of filter criteria
            
        Returns:
            True if scheme matches all filters, False otherwise
        """
        for key, value in filters.items():
            if key == "state":
                # Check if scheme has state restriction
                if scheme.eligibility.states:
                    if value not in scheme.eligibility.states:
                        return False
            elif key == "category":
                # Category filtering is handled by the API layer
                # Skip here since Scheme model doesn't have category field
                pass
            elif key == "min_age":
                if scheme.eligibility.min_age and scheme.eligibility.min_age > int(value):
                    return False
            elif key == "max_age":
                if scheme.eligibility.max_age and scheme.eligibility.max_age < int(value):
                    return False
        
        return True
    
    def save_index(self) -> None:
        """
        Save the FAISS index and scheme data to disk.
        
        Requirements: 6.1
        """
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{self.index_path}.faiss")
        
        # Save schemes metadata
        with open(f"{self.index_path}.pkl", "wb") as f:
            pickle.dump(self.schemes, f)
    
    def load_index(self) -> bool:
        """
        Load the FAISS index and scheme data from disk.
        
        Returns:
            True if loaded successfully, False otherwise
            
        Requirements: 6.1
        """
        try:
            # Load FAISS index
            self.index = faiss.read_index(f"{self.index_path}.faiss")
            
            # Load schemes metadata
            with open(f"{self.index_path}.pkl", "rb") as f:
                self.schemes = pickle.load(f)
            
            return True
        except (FileNotFoundError, Exception):
            return False
    
    def get_scheme_by_id(self, scheme_id: str) -> Optional[Scheme]:
        """
        Get a specific scheme by ID.
        
        Args:
            scheme_id: Scheme identifier
            
        Returns:
            Scheme object if found, None otherwise
        """
        for scheme in self.schemes:
            if scheme.id == scheme_id:
                return scheme
        return None
    
    def get_all_schemes(self) -> List[Scheme]:
        """
        Get all indexed schemes.
        
        Returns:
            List of all Scheme objects
        """
        return self.schemes.copy()
    
    def get_stats(self) -> Dict[str, any]:
        """
        Get statistics about the knowledge base.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_schemes": len(self.schemes),
            "embedding_dimension": self.embedding_dim,
            "model_name": self.model._model_card_data.model_name if hasattr(self.model, '_model_card_data') else "unknown",
            "indexed": self.index.ntotal > 0
        }
