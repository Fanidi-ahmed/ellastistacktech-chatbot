"""
Configuration globale du chatbot
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


@dataclass
class Config:
    """Configuration du chatbot"""

    # Modèles
    PRIMARY_MODEL: str = os.getenv("PRIMARY_MODEL", "camembert-base")
    FALLBACK_MODEL: str = os.getenv("FALLBACK_MODEL", "distilbert-base-uncased")
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8001"))
    API_DEBUG: bool = os.getenv("API_DEBUG", "False").lower() == "true"

    # Base de connaissances
    VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "models/vector_store")
    KNOWLEDGE_BASE_PATH: str = os.getenv("KNOWLEDGE_BASE_PATH", "data/knowledge_base")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # NLP
    MAX_LENGTH: int = int(os.getenv("MAX_LENGTH", "512"))
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))

    # Dialogue
    MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "10"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "150"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

    # Rate Limiting (NOUVEAU)
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    RATE_LIMIT_PER_DAY: int = int(os.getenv("RATE_LIMIT_PER_DAY", "500"))
    MAX_TOKENS_PER_RESPONSE: int = int(os.getenv("MAX_TOKENS_PER_RESPONSE", "150"))
    MAX_MESSAGES_PER_CONVERSATION: int = int(
        os.getenv("MAX_MESSAGES_PER_CONVERSATION", "20")
    )

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", "logs/chatbot.log")

    _instance = None

    @classmethod
    def get_instance(cls):
        """Pattern Singleton pour la configuration"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# Test rapide
if __name__ == "__main__":
    config = Config.get_instance()
    print(f"Configuration chargée : {config}")
    print(f"Rate limit: {config.RATE_LIMIT_PER_MINUTE} req/minute")
