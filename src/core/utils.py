"""
Fonctions utilitaires pour le chatbot
"""
import logging
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger
import pickle

class LoggerSetup:
    """Configuration des logs"""
    
    @staticmethod
    def setup_logger(log_file: Optional[str] = None, level: str = "INFO"):
        """Configurer le logger"""
        # Supprimer les handlers par défaut
        logger.remove()
        
        # Ajouter un handler console
        logger.add(
            sink=lambda msg: print(msg),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True
        )
        
        # Ajouter un handler fichier si spécifié
        if log_file:
            logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                level=level,
                rotation="10 MB",
                retention="1 month"
            )
        
        return logger

class TextPreprocessor:
    """Prétraitement de texte"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Nettoyer le texte"""
        if not text:
            return ""
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les espaces multiples
        text = " ".join(text.split())
        
        # Supprimer les caractères spéciaux (garder lettres, chiffres, ponctuation de base)
        import re
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Diviser le texte en chunks"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks

class CacheManager:
    """Gestionnaire de cache"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, key: str) -> str:
        """Générer une clé de cache"""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Récupérer une valeur du cache"""
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return None
        return None
    
    def set(self, key: str, value: Any):
        """Sauvegarder dans le cache"""
        cache_file = self.cache_dir / f"{self._get_cache_key(key)}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(value, f)
    
    def clear(self):
        """Vider le cache"""
        for file in self.cache_dir.glob("*.pkl"):
            file.unlink()

class MetricsCollector:
    """Collecteur de métriques"""
    
    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_response_time": 0,
            "intent_distribution": {},
            "user_satisfaction": []
        }
    
    def record_query(self, intent: str, success: bool, response_time: float):
        """Enregistrer une requête"""
        self.metrics["total_queries"] += 1
        
        if success:
            self.metrics["successful_responses"] += 1
        else:
            self.metrics["failed_responses"] += 1
        
        # Mise à jour du temps moyen
        total = self.metrics["average_response_time"] * (self.metrics["total_queries"] - 1)
        self.metrics["average_response_time"] = (total + response_time) / self.metrics["total_queries"]
        
        # Distribution des intentions
        if intent:
            self.metrics["intent_distribution"][intent] = self.metrics["intent_distribution"].get(intent, 0) + 1
    
    def get_metrics(self) -> Dict:
        """Récupérer les métriques"""
        return self.metrics
    
    def save_metrics(self, filepath: str):
        """Sauvegarder les métriques"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)

# Test rapide
if __name__ == "__main__":
    # Test du préprocesseur
    preprocessor = TextPreprocessor()
    text = "  Bonjour!   Comment puis-je vous aider?   "
    cleaned = preprocessor.clean_text(text)
    print(f"Texte original: {text}")
    print(f"Texte nettoyé: {cleaned}")
    
    # Test du cache
    cache = CacheManager("test_cache")
    cache.set("test_key", {"data": "test_value"})
    cached = cache.get("test_key")
    print(f"Cache test: {cached}")
    
    # Test du collecteur de métriques
    metrics = MetricsCollector()
    metrics.record_query("salutation", True, 0.5)
    print(f"Métriques: {metrics.get_metrics()}")
    
    # Nettoyage
    cache.clear()
