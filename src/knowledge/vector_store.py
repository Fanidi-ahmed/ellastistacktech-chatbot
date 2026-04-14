"""
Stockage vectoriel simple sans FAISS
Version robuste avec scikit-learn
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

# Import sécurisé de scikit-learn
try:
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
    logger.warning("scikit-learn non disponible")

from src.core.config import Config
from src.core.models import ModelManager


@dataclass
class Document:
    """Représentation d'un document indexé"""

    id: str
    title: str
    content: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir le document en dictionnaire JSON-serializable"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], embedding: Optional[np.ndarray] = None
    ) -> "Document":
        """Créer un document depuis un dictionnaire"""
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            content=data.get("content", ""),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
            embedding=embedding,
        )


class SimpleVectorStore:
    """Stockage vectoriel simple basé sur numpy + cosine similarity"""

    DOCUMENTS_FILE = "documents.json"
    EMBEDDINGS_FILE = "embeddings.npy"

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config.get_instance()
        self.model_manager = ModelManager(self.config)

        self.store_path = Path(self.config.VECTOR_STORE_PATH)
        self.store_path.mkdir(parents=True, exist_ok=True)

        self.documents: List[Document] = []
        self.embeddings_matrix: Optional[np.ndarray] = None

        self.load()

        logger.info(f"SimpleVectorStore prêt - {len(self.documents)} documents")

    @property
    def documents_file(self) -> Path:
        return self.store_path / self.DOCUMENTS_FILE

    @property
    def embeddings_file(self) -> Path:
        return self.store_path / self.EMBEDDINGS_FILE

    def add_documents(self, documents: List[Document]) -> int:
        """Ajouter des documents à la base"""
        if not documents:
            return 0

        # Filtrer les documents uniques
        existing_ids = {doc.id for doc in self.documents}
        new_docs = [doc for doc in documents if doc.id not in existing_ids]

        if not new_docs:
            logger.info("Aucun nouveau document unique")
            return 0

        # Générer les embeddings pour les documents sans
        docs_to_embed = [doc for doc in new_docs if doc.embedding is None]
        if docs_to_embed:
            texts = [doc.content for doc in docs_to_embed]
            embeddings = self._generate_embeddings(texts)
            if embeddings is not None:
                for doc, emb in zip(docs_to_embed, embeddings):
                    doc.embedding = emb

        # Ajouter les documents
        self.documents.extend(new_docs)
        self._rebuild_embeddings_matrix()
        self.save()

        logger.info(f"{len(new_docs)} document(s) ajouté(s)")
        return len(new_docs)

    def search(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """Rechercher les documents les plus proches de la requête"""
        if not query or not query.strip():
            return []

        if not self.documents:
            logger.warning("Aucun document dans la base")
            return []

        if self.embeddings_matrix is None:
            logger.warning("Matrice d'embeddings indisponible")
            return []

        # Générer l'embedding de la requête
        query_emb = self._generate_embeddings([query])
        if query_emb is None or len(query_emb) == 0:
            return []

        query_vector = query_emb[0].reshape(1, -1)

        # Calculer les similarités
        try:
            if SKLEARN_OK:
                similarities = cosine_similarity(query_vector, self.embeddings_matrix)[
                    0
                ]
            else:
                # Similarité manuelle
                similarities = []
                for emb in self.embeddings_matrix:
                    sim = np.dot(query_vector[0], emb) / (
                        np.linalg.norm(query_vector[0]) * np.linalg.norm(emb) + 1e-8
                    )
                    similarities.append(sim)
                similarities = np.array(similarities)
        except Exception as e:
            logger.error(f"Erreur similarité: {e}")
            return []

        # Trier et retourner les meilleurs
        k = min(k, len(self.documents))
        top_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_indices:
            results.append((self.documents[idx], float(similarities[idx])))

        return results

    def search_with_threshold(
        self, query: str, threshold: float = 0.5, k: int = 10
    ) -> List[Tuple[Document, float]]:
        """Rechercher les documents dépassant un seuil"""
        results = self.search(query, k)
        return [(doc, score) for doc, score in results if score >= threshold]

    def get_document(self, doc_id: str) -> Optional[Document]:
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None

    def remove_document(self, doc_id: str) -> bool:
        before = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.id != doc_id]
        if len(self.documents) == before:
            return False
        self._rebuild_embeddings_matrix()
        self.save()
        logger.info(f"Document supprimé: {doc_id}")
        return True

    def clear(self) -> bool:
        """Vider complètement la base"""
        self.documents = []
        self.embeddings_matrix = None
        try:
            if self.documents_file.exists():
                self.documents_file.unlink()
            if self.embeddings_file.exists():
                self.embeddings_file.unlink()
            logger.info("Base vidée")
            return True
        except Exception as e:
            logger.error(f"Erreur vidage: {e}")
            return False

    def save(self) -> bool:
        """Sauvegarder sur disque"""
        try:
            docs_data = [doc.to_dict() for doc in self.documents]
            with open(self.documents_file, "w", encoding="utf-8") as f:
                json.dump(docs_data, f, indent=2, ensure_ascii=False)

            if self.embeddings_matrix is not None:
                np.save(self.embeddings_file, self.embeddings_matrix)

            logger.info("Base sauvegardée")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            return False

    def load(self) -> None:
        """Charger depuis le disque"""
        if not self.documents_file.exists():
            logger.info("Aucune base existante")
            return

        try:
            with open(self.documents_file, "r", encoding="utf-8") as f:
                docs_data = json.load(f)

            # Charger les embeddings si disponibles
            embeddings = None
            if self.embeddings_file.exists():
                try:
                    embeddings = np.load(self.embeddings_file)
                except Exception as e:
                    logger.warning(f"Erreur chargement embeddings: {e}")

            # Reconstruire les documents
            self.documents = []
            for i, data in enumerate(docs_data):
                emb = (
                    embeddings[i]
                    if embeddings is not None and i < len(embeddings)
                    else None
                )
                try:
                    doc = Document.from_dict(data, embedding=emb)
                    self.documents.append(doc)
                except Exception as e:
                    logger.warning(f"Document ignoré: {e}")

            self._rebuild_embeddings_matrix()
            logger.info(f"{len(self.documents)} documents chargés")

        except Exception as e:
            logger.error(f"Erreur chargement: {e}")

    def _generate_embeddings(self, texts: List[str]) -> Optional[List[np.ndarray]]:
        """Générer des embeddings pour une liste de textes"""
        if not texts:
            return []

        try:
            embeddings = self.model_manager.get_embeddings(texts)
            if embeddings is None:
                return None

            # Normaliser en liste de numpy arrays
            result = []
            for emb in embeddings:
                arr = np.asarray(emb, dtype=np.float32)
                if arr.ndim == 1:
                    result.append(arr)
                else:
                    result.append(arr.flatten())

            return result

        except Exception as e:
            logger.error(f"Erreur génération embeddings: {e}")
            return None

    def _rebuild_embeddings_matrix(self) -> None:
        """Reconstruire la matrice d'embeddings"""
        if not self.documents:
            self.embeddings_matrix = None
            return

        # Vérifier que tous les documents ont un embedding
        embeddings_list = []
        for i, doc in enumerate(self.documents):
            if doc.embedding is None:
                logger.warning(f"Document {doc.id} sans embedding, ignoré")
                continue
            emb = np.asarray(doc.embedding, dtype=np.float32)

            if emb.ndim == 1:
                embeddings_list.append(emb)
            else:
                logger.warning(f"Embedding du document {doc.id}: {emb.shape}")

                continue
        if embeddings_list:
            self.embeddings_matrix = None
            return
