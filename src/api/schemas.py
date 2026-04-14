"""
Schémas de données Pydantic pour l'API REST
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageRequest(BaseModel):
    """Requête pour envoyer un message"""
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Bonjour, j'ai besoin d'aide",
                "conversation_id": None,
                "user_id": "user_123"
            }
        }
    )


class FeedbackRequest(BaseModel):
    """Feedback utilisateur"""
    conversation_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "conversation_id": "abc-123",
                "rating": 5,
                "comment": "Très utile !"
            }
        }
    )


class MessageResponse(BaseModel):
    """Réponse du chatbot"""
    conversation_id: str
    response: str
    intent: str
    confidence: float
    suggestions: List[str] = []
    knowledge_used: bool = False
    use_openai: bool = False
    timestamp: str


class HealthResponse(BaseModel):
    """Statut de santé"""
    status: str
    version: str
    use_openai: bool
    timestamp: str


class MetricsResponse(BaseModel):
    """Métriques"""
    total_conversations: int
    use_openai: bool
    timestamp: str


class ConversationHistoryResponse(BaseModel):
    """Historique"""
    conversation_id: str
    messages: List[Dict[str, Any]]
    summary: Dict[str, Any]


class FeedbackResponse(BaseModel):
    """Confirmation feedback"""
    status: str
    conversation_id: str
    message: str = "Merci pour votre retour !"


class ErrorResponse(BaseModel):
    """Erreur"""
    detail: str
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
