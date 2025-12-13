"""
Service de validation d'emails.
"""

import re
from typing import List, Tuple


class EmailValidationService:
    """Service pour valider les adresses email."""
    
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def is_valid(email: str) -> bool:
        """
        Vérifie si une adresse email est valide.
        
        Args:
            email: L'adresse email à valider
            
        Returns:
            True si valide, False sinon
        """
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        return bool(EmailValidationService.EMAIL_REGEX.match(email))
    
    @staticmethod
    def validate_batch(emails: List[str]) -> Tuple[List[str], List[str]]:
        """
        Valide un lot d'adresses email.
        
        Args:
            emails: Liste d'adresses email
            
        Returns:
            Tuple (valides, invalides)
        """
        valid = []
        invalid = []
        
        for email in emails:
            if EmailValidationService.is_valid(email):
                valid.append(email.strip().lower())
            else:
                invalid.append(email)
        
        return valid, invalid
    
    @staticmethod
    def normalize(email: str) -> str:
        """
        Normalise une adresse email.
        
        Args:
            email: L'adresse email à normaliser
            
        Returns:
            L'adresse email normalisée
        """
        return email.strip().lower()
