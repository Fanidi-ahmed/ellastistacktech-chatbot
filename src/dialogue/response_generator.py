"""
Générateur de réponses - Version ultra simple
"""

import random
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any
from loguru import logger

from src.core.config import Config
from src.nlp.intent_classifier import IntentClassifier
from src.knowledge.vector_store import SimpleVectorStore


class ResponseGenerator:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.get_instance()
        self.intent_classifier = IntentClassifier(self.config)
        self.vector_store = SimpleVectorStore(self.config)
        self.templates = self._load_templates()
        self.use_openai = False
        logger.info("ResponseGenerator prêt")

    def _load_templates(self) -> Dict[str, List[str]]:
        template_file = Path("data/response_templates.json")
        if template_file.exists():
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Templates par défaut
        return {
            "salutation": ["Bonjour ! Je suis l'assistant d'IntellistackTech. Comment puis-je vous aider ?"],
            "python": ["Python est un langage de programmation polyvalent, utilisé pour le web, la data science, l'IA et l'automatisation."],
            "kubernetes": ["Kubernetes est un orchestrateur de conteneurs pour gérer des applications en production."],
            "docker": ["Docker permet de conteneuriser vos applications pour les rendre portables."],
            "terraform": ["Terraform est un outil d'Infrastructure as Code pour automatiser le cloud."],
            "aws": ["AWS est la plateforme cloud leader avec plus de 200 services."],
            "general": ["Je suis un assistant technique. Posez-moi des questions sur Python, Kubernetes, Docker, Terraform, AWS, DevOps ou l'IA."]
        }

    def generate_response(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Générer une réponse - TOUJOURS RÉPONDRE"""
        
        # Classification
        intent_result = self.intent_classifier.classify(user_input)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        # Recherche dans la base de connaissances
        knowledge = self.vector_store.search(user_input, k=1)
        
        # Construire la réponse
        if knowledge and knowledge[0][1] > 0.5:
            response = knowledge[0][0].content
        else:
            response = self._get_template(intent)
        
        return {
            "text": response,
            "intent": intent,
            "confidence": confidence,
            "suggestions": ["Python", "Kubernetes", "Docker", "Terraform", "AWS", "Devis"],
            "knowledge_used": len(knowledge) > 0,
            "use_openai": False,
            "timestamp": datetime.now().isoformat(),
        }

    def _get_template(self, intent: str) -> str:
        """Récupérer un template"""
        if intent in self.templates:
            return random.choice(self.templates[intent])
        return random.choice(self.templates.get("general", ["Je peux vous aider sur les technologies IT."]))
