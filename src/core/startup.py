"""
Nettoyage automatique au démarrage de l'API
"""
import os
import shutil
from pathlib import Path
from loguru import logger

def clean_caches():
    """Nettoie les caches au démarrage"""
    try:
        # Supprimer __pycache__
        for root, dirs, files in os.walk("."):
            if "__pycache__" in dirs:
                shutil.rmtree(os.path.join(root, "__pycache__"))
        
        # Supprimer model_cache
        if Path("model_cache").exists():
            shutil.rmtree("model_cache")
            logger.info("✅ model_cache nettoyé")
        
        # Supprimer .pytest_cache
        if Path(".pytest_cache").exists():
            shutil.rmtree(".pytest_cache")
        
        logger.info("✅ Caches nettoyés au démarrage")
    except Exception as e:
        logger.warning(f"Erreur nettoyage caches: {e}")

# Appel automatique
clean_caches()
