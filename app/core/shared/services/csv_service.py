"""
Service de lecture de fichiers CSV.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any
from app.core.utils.logger import app_logger


class CSVService:
    """Service pour lire et manipuler les fichiers CSV."""
    
    @staticmethod
    def read_file(file_path: Path, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
        """
        Lit un fichier CSV et retourne les données.
        
        Args:
            file_path: Chemin vers le fichier CSV
            encoding: Encodage du fichier
            
        Returns:
            Liste de dictionnaires représentant les lignes
        """
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            app_logger.error(f"Erreur lecture CSV {file_path}: {e}")
            raise
    
    @staticmethod
    def extract_emails(data: List[Dict[str, Any]], email_column: str = 'email') -> List[str]:
        """
        Extrait les emails d'un dataset CSV.
        
        Args:
            data: Données CSV
            email_column: Nom de la colonne contenant les emails
            
        Returns:
            Liste des adresses email
        """
        emails = []
        for row in data:
            if email_column in row and row[email_column]:
                emails.append(row[email_column].strip())
        return emails
    
    @staticmethod
    def write_file(file_path: Path, data: List[Dict[str, Any]], encoding: str = 'utf-8'):
        """
        Écrit des données dans un fichier CSV.
        
        Args:
            file_path: Chemin vers le fichier CSV
            data: Données à écrire
            encoding: Encodage du fichier
        """
        if not data:
            return
        
        try:
            with open(file_path, 'w', encoding=encoding, newline='') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            app_logger.error(f"Erreur écriture CSV {file_path}: {e}")
            raise
