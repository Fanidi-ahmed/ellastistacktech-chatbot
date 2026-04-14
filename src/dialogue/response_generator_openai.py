"""
Générateur de réponses - Version robuste avec OpenAI
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from loguru import logger
from dotenv import load_dotenv

from src.core.config import Config
from src.nlp.intent_classifier import IntentClassifier
from src.knowledge.vector_store import SimpleVectorStore

load_dotenv()


class ResponseGeneratorOpenAI:
    """Générateur de réponses - Version robuste"""

    DIRECT_RESPONSES = {
        "python": (
            "Python est un langage de programmation polyvalent, créé en 1991 par "
            "Guido van Rossum. Il est utilisé pour :\n\n"
            "• Développement web (Django, Flask)\n"
            "• Data science et IA (Pandas, TensorFlow, PyTorch)\n"
            "• Automatisation et scripts\n"
            "• Cloud computing (boto3 pour AWS)\n"
            "• DevOps et CI/CD\n\n"
            "C'est notre langage principal chez IntellistackTech !"
        ),
        "kubernetes": (
            "Kubernetes (K8s) est un orchestrateur de conteneurs open-source créé "
            "par Google. Il permet de :\n\n"
            "• Déployer des applications conteneurisées\n"
            "• Les scaler automatiquement\n"
            "• Gérer les mises à jour sans interruption\n"
            "• Assurer la haute disponibilité\n\n"
            "C'est la solution standard pour la gestion de conteneurs en production."
        ),
        "docker": (
            "Docker est une plateforme de conteneurisation qui permet d'empaqueter "
            "une application avec toutes ses dépendances. Avantages :\n\n"
            "• Portabilité (fonctionne partout)\n"
            "• Légèreté (moins de ressources qu'une VM)\n"
            "• Reproductibilité\n"
            "• Isolation des applications\n\n"
            "Docker est la base de Kubernetes !"
        ),
        "terraform": (
            "Terraform est un outil d'Infrastructure as Code (IaC) développé par "
            "HashiCorp. Il permet de :\n\n"
            "• Définir votre infrastructure cloud dans des fichiers\n"
            "• Versionner votre infrastructure comme du code\n"
            "• Déployer automatiquement sur AWS, Azure, GCP\n"
            "• Éviter les erreurs manuelles\n\n"
            "Chez IntellistackTech, nous utilisons Terraform quotidiennement."
        ),
        "aws": (
            "AWS (Amazon Web Services) est la plateforme cloud leader. Elle propose :\n\n"
            "• Calcul : EC2, Lambda\n"
            "• Stockage : S3, EBS\n"
            "• Base de données : RDS, DynamoDB\n"
            "• Réseau : VPC, CloudFront\n"
            "• IA : SageMaker, Rekognition\n"
            "• et +200 services !\n\n"
            "Nous sommes experts AWS certifiés."
        ),
    }

    DEFAULT_SUGGESTIONS = [
        "Python",
        "Kubernetes",
        "Docker",
        "Terraform",
        "AWS",
        "Devis",
    ]

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.get_instance()
        self.intent_classifier = IntentClassifier(self.config)
        self.vector_store = SimpleVectorStore(self.config)

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = False
        self.client = None
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        if self.api_key:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key)
                self.use_openai = True
                logger.info("✅ OpenAI disponible")
            except ImportError:
                logger.warning("OpenAI package non installé")
            except Exception as e:
                logger.warning(f"OpenAI non disponible : {e}")

        logger.info("✅ ResponseGenerator prêt")

    def generate_response(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Générer une réponse - TOUJOURS RÉPONDRE"""
        context = context or {}
        user_lower = user_input.lower().strip()

        # 1. Réponses directes pour questions simples / fréquentes
        direct_response = self._get_direct_response(user_lower)
        if direct_response:
            suggestions = self._get_suggestions(user_lower)
            return self._make_response(
                text=direct_response,
                intent="direct_answer",
                confidence=1.0,
                suggestions=suggestions,
                knowledge_used=False,
            )

        # 2. Classification
        try:
            intent_result = self.intent_classifier.classify(user_input)
            intent = intent_result.get("intent", "general")
            confidence = intent_result.get("confidence", 0.5)
        except Exception as e:
            logger.warning(f"Erreur classification : {e}")
            intent = "general"
            confidence = 0.5

        # 3. Recherche dans la base de connaissances
        try:
            knowledge_results = self.vector_store.search(user_input, k=2)
        except Exception as e:
            logger.warning(f"Erreur recherche vectorielle : {e}")
            knowledge_results = []

        # 4. Construction de la réponse
        knowledge_used = False

        if knowledge_results and len(knowledge_results) > 0:
            best_result = knowledge_results[0]

            if (
                isinstance(best_result, (list, tuple))
                and len(best_result) >= 2
                and best_result[1] > 0.4
            ):
                document = best_result[0]
                response = getattr(document, "content", None)

                if response:
                    knowledge_used = True
                else:
                    response = self._get_fallback_response()
            else:
                response = self._generate_with_fallback(user_input, context)
        else:
            response = self._generate_with_fallback(user_input, context)

        suggestions = self._get_suggestions(user_lower)

        return self._make_response(
            text=response,
            intent=intent,
            confidence=confidence,
            suggestions=suggestions,
            knowledge_used=knowledge_used,
        )

    def _get_direct_response(self, user_input: str) -> Optional[str]:
        """Retourne une réponse directe si la question est simple"""
        simple_patterns = [
            "c'est quoi",
            "que veut dire",
            "définition",
            "explique",
            "expliquer",
        ]

        for keyword, response in self.DIRECT_RESPONSES.items():
            if keyword in user_input:
                if len(user_input.split()) <= 6:
                    return response
                if any(pattern in user_input for pattern in simple_patterns):
                    return response

        return None

    def _generate_with_fallback(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Essaie OpenAI sinon fallback"""
        if self.use_openai and self.client:
            return self._call_openai(user_input, context)
        return self._get_fallback_response()

    def _make_response(
        self,
        text: str,
        intent: str,
        confidence: float,
        suggestions: Optional[List[str]] = None,
        knowledge_used: bool = False,
    ) -> Dict[str, Any]:
        """Construire la réponse standard"""
        return {
            "text": text,
            "intent": intent,
            "confidence": confidence,
            "suggestions": suggestions or self.DEFAULT_SUGGESTIONS,
            "knowledge_used": knowledge_used,
            "use_openai": self.use_openai,
            "timestamp": datetime.now().isoformat(),
        }

    def _call_openai(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Appel à OpenAI - Version sécurisée"""
        if not self.client:
            return self._get_fallback_response()

        context = context or {}

        try:
            system_prompt = (
                "Tu es un assistant technique spécialisé en IT, DevOps, Cloud et IA. "
                "Réponds en français, de façon claire, utile et concise."
            )

            if context:
                system_prompt += f"\n\nContexte supplémentaire : {context}"

            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                max_tokens=300,
                temperature=0.7,
            )

            if response and response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    return content.strip()

            return self._get_fallback_response()

        except Exception as e:
            logger.error(f"OpenAI error : {e}")
            return self._get_fallback_response()

    def _get_fallback_response(self) -> str:
        """Réponse de fallback"""
        return (
            "Je suis un assistant technique spécialisé en informatique. "
            "Je peux vous répondre sur :\n\n"
            "🐍 **Python** - Langage de programmation\n"
            "🐳 **Docker** - Conteneurisation\n"
            "☸️ **Kubernetes** - Orchestration\n"
            "🏗️ **Terraform** - Infrastructure as Code\n"
            "☁️ **AWS** - Cloud computing\n"
            "🤖 **IA/LLM** - Chatbots, modèles de langage\n"
            "🔧 **DevOps** - CI/CD, automatisation\n\n"
            "Posez-moi votre question !"
        )

    def _get_suggestions(self, user_input: str) -> List[str]:
        """Suggestions contextuelles"""
        if "python" in user_input:
            return ["Exemples Python", "Python AWS", "Formation Python", "Devis"]
        if "kubernetes" in user_input or "k8s" in user_input:
            return ["K8s vs Docker", "Architecture K8s", "Helm", "Devis"]
        if "docker" in user_input:
            return ["Dockerfile", "Docker Compose", "Docker vs VM", "K8s"]
        if "terraform" in user_input:
            return ["Modules Terraform", "Terraform AWS", "Best practices", "Devis"]
        if "aws" in user_input:
            return ["Services AWS", "Terraform sur AWS", "Optimisation coûts", "Devis"]

        return self.DEFAULT_SUGGESTIONS


if __name__ == "__main__":
    print("Testing ResponseGenerator...")
    rg = ResponseGeneratorOpenAI()
    result = rg.generate_response("que veut dire python")
    print(f"Intent: {result['intent']}")
    print(f"Réponse: {result['text'][:100]}...")
    print("✅ Test réussi")
