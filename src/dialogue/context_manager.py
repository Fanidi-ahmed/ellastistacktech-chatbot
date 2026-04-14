"""
Gestion du contexte de conversation - Version robuste
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class Message:
    """Représentation d'un message"""

    id: str
    role: str  # "user" ou "bot"
    content: str
    intent: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Conversation:
    """Représentation d'une conversation"""

    id: str
    user_id: Optional[str]
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def add_message(self, message: Message):
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_last_message(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None

    def get_context_summary(self) -> Dict[str, Any]:
        last_msg = self.get_last_message()
        last_intent = last_msg.intent if last_msg else None
        return {
            "conversation_id": self.id,
            "user_id": self.user_id,
            "message_count": len(self.messages),
            "last_intent": last_intent,
        }


class ContextManager:
    """Gestionnaire de contexte"""

    def __init__(self, storage_path: str = "data/conversations"):
        self.storage_path = Path(storage_path)
        self.active_conversations: Dict[str, Conversation] = {}

        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            logger.info("✅ ContextManager prêt")
        except Exception as e:
            logger.error(f"Erreur création dossier: {e}")

    def create_conversation(self, user_id: Optional[str] = None) -> Conversation:
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
        )
        self.active_conversations[conv_id] = conversation
        logger.info(f"Nouvelle conversation: {conv_id}")
        return conversation

    def get_conversation(self, conv_id: str) -> Optional[Conversation]:
        if conv_id in self.active_conversations:
            return self.active_conversations[conv_id]
        return self._load_conversation(conv_id)

    def add_message(
        self, conv_id: str, role: str, content: str, intent: Optional[str] = None
    ) -> Optional[Message]:
        conv = self.get_conversation(conv_id)
        if not conv:
            conv = self.create_conversation()
            conv_id = conv.id

        message = Message(
            id=str(uuid.uuid4()), role=role, content=content, intent=intent
        )
        conv.add_message(message)
        self._save_conversation(conv)
        return message

    def get_conversation_history(
        self, conv_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        conv = self.get_conversation(conv_id)
        if not conv:
            return []

        history = []
        for msg in conv.messages[-limit:]:
            history.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "intent": msg.intent,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                }
            )
        return history

    def _save_conversation(self, conversation: Conversation):
        try:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            filepath = self.storage_path / f"{conversation.id}.json"

            data = {
                "id": conversation.id,
                "user_id": conversation.user_id,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "intent": msg.intent,
                        "timestamp": (
                            msg.timestamp.isoformat() if msg.timestamp else None
                        ),
                    }
                    for msg in conversation.messages
                ],
                "context": conversation.context,
                "created_at": (
                    conversation.created_at.isoformat()
                    if conversation.created_at
                    else None
                ),
                "updated_at": (
                    conversation.updated_at.isoformat()
                    if conversation.updated_at
                    else None
                ),
                "metadata": conversation.metadata,
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Erreur sauvegarde: {e}")

    def _load_conversation(self, conv_id: str) -> Optional[Conversation]:
        filepath = self.storage_path / f"{conv_id}.json"
        if not filepath.exists():
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            messages = []
            for msg_data in data.get("messages", []):
                timestamp = None
                if msg_data.get("timestamp"):
                    timestamp = datetime.fromisoformat(msg_data["timestamp"])

                msg = Message(
                    id=msg_data["id"],
                    role=msg_data["role"],
                    content=msg_data["content"],
                    intent=msg_data.get("intent"),
                    timestamp=timestamp,
                )
                messages.append(msg)

            created_at = None
            if data.get("created_at"):
                created_at = datetime.fromisoformat(data["created_at"])

            updated_at = None
            if data.get("updated_at"):
                updated_at = datetime.fromisoformat(data["updated_at"])

            return Conversation(
                id=data["id"],
                user_id=data.get("user_id"),
                messages=messages,
                context=data.get("context", {}),
                created_at=created_at,
                updated_at=updated_at,
                metadata=data.get("metadata", {}),
            )
        except Exception as e:
            logger.warning(f"Erreur chargement: {e}")
            return None

    def clear_expired_conversations(self, max_age_hours: int = 24):
        """Nettoyer les conversations expirées"""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        expired = []
        for conv_id, conv in self.active_conversations.items():
            if conv.updated_at is not None and conv.updated_at < cutoff:
                expired.append(conv_id)

        for conv_id in expired:
            self._save_conversation(self.active_conversations[conv_id])
            del self.active_conversations[conv_id]

        if expired:
            logger.info(f"{len(expired)} conversations expirées nettoyées")


if __name__ == "__main__":
    cm = ContextManager()
    conv = cm.create_conversation()
    cm.add_message(conv.id, "user", "Bonjour")
    summary = conv.get_context_summary()
    print(f"✅ Test OK: {summary}")
