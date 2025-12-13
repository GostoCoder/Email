"""
Service de connexion et gestion de la base de données Supabase.
"""

from typing import Optional, List, Dict, Any
from supabase import create_client, Client
from app.core.config.settings import config
from app.core.utils.logger import app_logger

logger = app_logger


class DatabaseService:
    """Service pour gérer les connexions à Supabase."""
    
    _instance: Optional['DatabaseService'] = None
    _supabase_client: Optional[Client] = None
    
    def __new__(cls):
        """Singleton pattern pour une seule instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialise les connexions si nécessaire."""
        if self._supabase_client is None:
            self._init_supabase()
    
    def _init_supabase(self):
        """Initialise le client Supabase."""
        try:
            # Créer le client sans options supplémentaires pour éviter les problèmes de compatibilité
            self._supabase_client = create_client(
                supabase_url=config.supabase.url,
                supabase_key=config.supabase.key
            )
            logger.info(f"Client Supabase initialisé: {config.supabase.url}")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation du client Supabase: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Retourne le client Supabase."""
        if self._supabase_client is None:
            self._init_supabase()
        return self._supabase_client
    
    # =========================================================================
    # Méthodes utilitaires pour les opérations courantes
    # =========================================================================
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à la base de données.
        
        Returns:
            True si la connexion fonctionne, False sinon
        """
        try:
            # Test simple avec une requête sur une table qui devrait exister
            result = self.client.table('campaigns').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Test de connexion échoué: {e}")
            return False
    
    # =========================================================================
    # Méthodes pour les opérations sur les tables via Supabase REST API
    # =========================================================================
    
    def select(self, table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None):
        """
        Sélectionne des données d'une table via l'API Supabase.
        
        Args:
            table: Nom de la table
            columns: Colonnes à sélectionner (défaut: "*")
            filters: Filtres à appliquer (ex: {"status": "active"})
            
        Returns:
            Résultat de la requête
        """
        try:
            query = self.client.table(table).select(columns)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la sélection dans {table}: {e}")
            raise
    
    def insert(self, table: str, data: Dict[str, Any] | List[Dict[str, Any]]):
        """
        Insère des données dans une table.
        
        Args:
            table: Nom de la table
            data: Données à insérer (dict ou list de dict)
            
        Returns:
            Données insérées
        """
        try:
            response = self.client.table(table).insert(data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de l'insertion dans {table}: {e}")
            raise
    
    def update(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]):
        """
        Met à jour des données dans une table.
        
        Args:
            table: Nom de la table
            data: Nouvelles données
            filters: Conditions de mise à jour
            
        Returns:
            Données mises à jour
        """
        try:
            query = self.client.table(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour dans {table}: {e}")
            raise
    
    def delete(self, table: str, filters: Dict[str, Any]):
        """
        Supprime des données d'une table.
        
        Args:
            table: Nom de la table
            filters: Conditions de suppression
            
        Returns:
            Données supprimées
        """
        try:
            query = self.client.table(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Erreur lors de la suppression dans {table}: {e}")
            raise


# Instance globale du service
db = DatabaseService()


# Fonction helper pour obtenir le service
def get_db() -> DatabaseService:
    """Retourne l'instance du service de base de données."""
    return db
