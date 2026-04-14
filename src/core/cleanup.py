"""
Nettoyage automatique des caches au démarrage
"""

import os
import shutil
from pathlib import Path
from loguru import logger


def clean_all_caches():
    """Nettoie tous les caches automatiquement"""
    
    caches_to_clean = [
        "model_cache",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "logs/*.log",
        "data/conversations/*.json"  # Optionnel : garder les 10 dernières
    ]
    
    logger.info("🧹 Nettoyage automatique des caches...")
    
    # 1. Supprimer model_cache
    if Path("model_cache").exists():
        shutil.rmtree("model_cache")
        logger.info("✅ model_cache supprimé")
    
    # 2. Supprimer tous les __pycache__
    for pycache in Path(".").rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)
    logger.info("✅ __pycache__ supprimés")
    
    # 3. Supprimer les logs vieux de plus de 7 jours
    log_dir = Path("logs")
    if log_dir.exists():
        for log_file in log_dir.glob("*.log"):
            if log_file.stat().st_mtime < (Path().stat().st_mtime - 7*24*3600):
                log_file.unlink()
        logger.info("✅ Logs anciens nettoyés")
    
    # 4. Garder seulement les 10 dernières conversations
    conv_dir = Path("data/conversations")
    if conv_dir.exists():
        conv_files = sorted(conv_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        for old_file in conv_files[10:]:  # Garde les 10 plus récentes
            old_file.unlink()
        logger.info(f"✅ Conversations nettoyées ({len(conv_files)} → {min(10, len(conv_files))})")
    
    logger.info("✅ Nettoyage terminé")


def clean_on_startup():
    """Nettoie au démarrage si l'option est activée"""
    from src.core.config import Config
    config = Config.get_instance()
    
    # Vérifier si le nettoyage auto est activé
    auto_clean = os.getenv("AUTO_CLEAN_CACHE", "true").lower() == "true"
    
    if auto_clean:
        clean_all_caches()
    else:
        logger.info("Nettoyage auto désactivé (AUTO_CLEAN_CACHE=false)")
