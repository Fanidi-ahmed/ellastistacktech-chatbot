"""
Classification des intentions - Version robuste et simple
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from loguru import logger

try:
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    cosine_similarity = None
    SKLEARN_AVAILABLE = False

from src.core.config import Config
from src.core.models import ModelManager
from src.nlp.preprocessor import TextPreprocessor


class IntentClassifier:
    """Classifieur d'intentions simple avec fallback lexical."""

    DEFAULT_INTENTS: Dict[str, List[str]] = {
        "salutation": ["bonjour", "salut", "hello", "bonsoir"],
        "python": ["python"],
        "kubernetes": ["kubernetes", "k8s"],
        "docker": ["docker"],
        "terraform": ["terraform"],
        "aws": ["aws"],
        "contact": ["contact", "email", "mail"],
        "devis": ["devis", "tarif", "prix"],
    }

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.get_instance()
        self.model_manager = ModelManager(self.config)
        self.preprocessor = TextPreprocessor()

        self.intent_file = self._resolve_intent_file_path()
        self.intents: Dict[str, List[str]] = self._load_intents()

        self.intent_vectors: Optional[np.ndarray] = None
        self.intent_labels: List[str] = []
        self.intent_examples: List[str] = []

        self._prepare_intent_vectors()

        logger.info(f"IntentClassifier prêt avec {len(self.intents)} intentions")

    def _resolve_intent_file_path(self) -> Path:
        """Déterminer le chemin du fichier intents.json."""
        config_path = getattr(self.config, "INTENT_FILE_PATH", None)
        if config_path:
            return Path(config_path)

        return Path("data/intents.json")

    def _load_intents(self) -> Dict[str, List[str]]:
        """Charger les intentions depuis le fichier JSON ou utiliser les valeurs par défaut."""
        if self.intent_file.exists():
            try:
                with open(self.intent_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if self._is_valid_intents_payload(data):
                    return data

                logger.warning(
                    f"Format invalide pour {self.intent_file}. "
                    "Utilisation des intentions par défaut."
                )

            except Exception as e:
                logger.warning(f"Erreur chargement intents.json : {e}")

        return self.DEFAULT_INTENTS.copy()

    def _is_valid_intents_payload(self, data: Any) -> bool:
        """Vérifier que les données d'intentions sont valides."""
        if not isinstance(data, dict):
            return False

        for intent_name, examples in data.items():
            if not isinstance(intent_name, str):
                return False
            if not isinstance(examples, list):
                return False
            if not all(
                isinstance(example, str) and example.strip() for example in examples
            ):
                return False

        return True

    def _prepare_intent_vectors(self) -> None:
        """Préparer les embeddings des exemples d'intentions."""
        self.intent_labels = []
        self.intent_examples = []
        self.intent_vectors = None

        processed_examples: List[str] = []

        for intent, examples in self.intents.items():
            for example in examples:
                processed = self._preprocess_text(example)
                if not processed:
                    continue

                processed_examples.append(processed)
                self.intent_labels.append(intent)
                self.intent_examples.append(example)

        if not processed_examples:
            logger.warning(
                "Aucun exemple valide pour préparer les vecteurs d'intention"
            )
            return

        embeddings = self._generate_embeddings(processed_examples)
        if embeddings is None:
            logger.warning("Impossible de préparer les vecteurs d'intention")
            return

        try:
            self.intent_vectors = np.vstack(embeddings).astype(np.float32)
        except Exception as e:
            logger.warning(f"Erreur préparation matrice d'intentions : {e}")
            self.intent_vectors = None

    def classify(self, text: str, threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Classifier une intention.
        Retourne toujours un résultat.
        """
        threshold = threshold if threshold is not None else 0.35

        if not text or not text.strip():
            return {
                "intent": "general",
                "confidence": 0.0,
                "method": "empty_input",
            }

        processed = self._preprocess_text(text)
        if not processed:
            return {
                "intent": "general",
                "confidence": 0.0,
                "method": "preprocess_fallback",
            }

        vector_result = self._classify_with_vectors(processed, threshold)
        if vector_result is not None:
            return vector_result

        lexical_result = self._classify_with_keywords(processed)
        if lexical_result is not None:
            return lexical_result

        return {
            "intent": "general",
            "confidence": 0.5,
            "method": "fallback",
        }

    def _classify_with_vectors(
        self,
        processed_text: str,
        threshold: float,
    ) -> Optional[Dict[str, Any]]:
        """Classifier avec similarité vectorielle."""
        if self.intent_vectors is None or len(self.intent_vectors) == 0:
            return None

        text_embeddings = self._generate_embeddings([processed_text])
        if not text_embeddings:
            return None

        text_vector = text_embeddings[0]

        try:
            if SKLEARN_AVAILABLE and cosine_similarity is not None:
                similarities = cosine_similarity(
                    text_vector.reshape(1, -1), self.intent_vectors
                )[0]
            else:
                similarities = self._manual_cosine_similarity(
                    text_vector, self.intent_vectors
                )

            if similarities is None or len(similarities) == 0:
                return None

            best_idx = int(np.argmax(similarities))
            best_score = float(similarities[best_idx])
            best_intent = self.intent_labels[best_idx]

            if best_score < threshold:
                return None

            return {
                "intent": best_intent,
                "confidence": best_score,
                "method": "vector",
            }

        except Exception as e:
            logger.warning(f"Erreur similarité vectorielle : {e}")
            return None

    def _classify_with_keywords(self, processed_text: str) -> Optional[Dict[str, Any]]:
        """Fallback lexical simple basé sur les exemples connus."""
        text_tokens = set(processed_text.split())
        if not text_tokens:
            return None

        best_intent: Optional[str] = None
        best_score = 0.0

        for intent, examples in self.intents.items():
            for example in examples:
                processed_example = self._preprocess_text(example)
                if not processed_example:
                    continue

                example_tokens = set(processed_example.split())
                if not example_tokens:
                    continue

                overlap = len(text_tokens & example_tokens)
                if overlap == 0:
                    continue

                score = overlap / max(len(example_tokens), 1)

                if score > best_score:
                    best_score = score
                    best_intent = intent

        if best_intent is None:
            return None

        return {
            "intent": best_intent,
            "confidence": float(best_score),
            "method": "keyword",
        }

    def _generate_embeddings(self, texts: List[str]) -> Optional[List[np.ndarray]]:
        """Générer et normaliser une liste d'embeddings."""
        if not texts:
            return []

        try:
            embeddings = self.model_manager.get_embeddings(texts)

            if embeddings is None:
                logger.warning("ModelManager.get_embeddings a retourné None")
                return None

            if len(embeddings) != len(texts):
                logger.warning(
                    "Nombre d'embeddings incohérent : "
                    f"{len(embeddings)} reçu(s) pour {len(texts)} texte(s)"
                )
                return None

            normalized_embeddings: List[np.ndarray] = []

            for index, emb in enumerate(embeddings):
                arr = np.asarray(emb, dtype=np.float32)

                if arr.ndim != 1:
                    logger.warning(
                        f"Embedding invalide à l'index {index} : dimension attendue = 1"
                    )
                    return None

                norm = np.linalg.norm(arr)
                if norm == 0:
                    logger.warning(f"Embedding nul à l'index {index}")
                    return None

                normalized_embeddings.append(arr / norm)

            return normalized_embeddings

        except Exception as e:
            logger.warning(f"Erreur génération embeddings : {e}")
            return None

    def _manual_cosine_similarity(
        self,
        vector: np.ndarray,
        matrix: np.ndarray,
    ) -> Optional[np.ndarray]:
        """Calcul manuel de similarité cosinus."""
        try:
            vector = np.asarray(vector, dtype=np.float32)
            matrix = np.asarray(matrix, dtype=np.float32)

            if vector.ndim != 1 or matrix.ndim != 2:
                return None

            vector_norm = np.linalg.norm(vector)
            matrix_norms = np.linalg.norm(matrix, axis=1)

            if vector_norm == 0:
                return None

            denominator = (matrix_norms * vector_norm) + 1e-8
            similarities = np.dot(matrix, vector) / denominator
            return similarities

        except Exception as e:
            logger.warning(f"Erreur similarité manuelle : {e}")
            return None

    def _preprocess_text(self, text: str) -> str:
        """Prétraiter un texte de manière sûre."""
        try:
            processed = self.preprocessor.preprocess_pipeline(text, normalize=True)
            return processed.strip() if isinstance(processed, str) else ""
        except Exception as e:
            logger.warning(f"Erreur preprocessing : {e}")
            return ""

    def batch_classify(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Classifier plusieurs textes"""
        return [self.classify(text) for text in texts]
