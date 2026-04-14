"""
API REST simplifiée
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
from datetime import datetime
from loguru import logger

from src.core.config import Config
from src.dialogue.response_generator import ResponseGenerator
from src.dialogue.context_manager import ContextManager
from src.core.cleanup import clean_on_startup

# Nettoyer les caches au démarrage
clean_on_startup()

# ==================== INITIALISATION ====================

app = FastAPI(
    title="IntellistackTech Chatbot", description="Assistant technique", version="1.0.0"
)

# CORS - Autoriser tout le monde
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Services
config = Config.get_instance()
response_generator = ResponseGenerator(config)
context_manager = ContextManager()


# ==================== ROUTES ====================


@app.get("/")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/chat")
async def chat(request: Dict[str, Any]):
    """Envoyer un message"""
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message requis")

        # Gérer la conversation
        conv_id = request.get("conversation_id")
        if not conv_id or not context_manager.get_conversation(conv_id):
            conv = context_manager.create_conversation()
            conv_id = conv.id

        # Ajouter le message
        context_manager.add_message(conv_id, "user", message)

        # Générer la réponse
        response = response_generator.generate_response(message)

        # Ajouter la réponse
        context_manager.add_message(conv_id, "bot", response["text"])

        return {
            "conversation_id": conv_id,
            "response": response["text"],
            "intent": response["intent"],
            "confidence": response["confidence"],
            "suggestions": response["suggestions"],
            "timestamp": response["timestamp"],
        }

    except Exception as e:
        logger.error(f"Erreur: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    return {
        "conversations": len(context_manager.active_conversations),
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api.rest_api:app", host="0.0.0.0", port=8001, reload=True)
