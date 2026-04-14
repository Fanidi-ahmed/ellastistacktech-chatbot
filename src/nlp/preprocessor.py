"""
Prétraitement du texte pour le NLP
"""
import re
import unicodedata
from typing import List, Optional, Tuple
import logging
from loguru import logger

# Import conditionnel de spaCy avec gestion d'erreur
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spacy non disponible, utilisation du mode dégradé")

class TextPreprocessor:
    """Prétraitement avancé du texte"""
    
    def __init__(self, language: str = "fr"):
        self.language = language
        self.nlp = None
        
        # Charger le modèle Spacy si disponible
        if SPACY_AVAILABLE:
            try:
                if language == "fr":
                    self.nlp = spacy.load("fr_core_news_sm")
                else:
                    self.nlp = spacy.load("en_core_web_sm")
                logger.info(f"Modèle Spacy chargé pour la langue {language}")
            except Exception as e:
                logger.warning(f"Impossible de charger le modèle Spacy: {e}")
                self.nlp = None
        else:
            logger.info("Mode dégradé: utilisation des fonctions de base")
    
    def normalize_text(self, text: str) -> str:
        """Normalisation complète du texte"""
        if not text:
            return ""
        
        # Normalisation Unicode
        try:
            text = unicodedata.normalize('NFKD', text)
        except:
            pass
        
        # Mettre en minuscules
        text = text.lower()
        
        # Supprimer les caractères spéciaux (garder lettres, chiffres, espaces et ponctuation de base)
        text = re.sub(r'[^\w\s.,!?;:()\-]', '', text, flags=re.UNICODE)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenisation du texte"""
        if self.nlp:
            try:
                doc = self.nlp(text)
                return [token.text for token in doc]
            except:
                pass
        
        # Tokenisation simple de fallback
        return text.split()
    
    def lemmatize(self, text: str) -> str:
        """Lemmatisation du texte"""
        if self.nlp:
            try:
                doc = self.nlp(text)
                return ' '.join([token.lemma_ for token in doc])
            except:
                pass
        
        return text
    
    def remove_stopwords(self, text: str) -> str:
        """Suppression des mots vides"""
        if self.nlp:
            try:
                doc = self.nlp(text)
                return ' '.join([token.text for token in doc if not token.is_stop])
            except:
                pass
        
        return text
    
    def extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extraction des entités nommées"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            return entities
        except:
            return []
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """Extraction simple des mots-clés basée sur la fréquence"""
        words = self.tokenize(text.lower())
        
        # Mots vides simples en français/anglais
        stopwords = {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 
                     'donc', 'car', 'pour', 'dans', 'sur', 'avec', 'sans', 'par',
                     'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to'}
        
        # Compter les mots
        word_freq = {}
        for word in words:
            if word not in stopwords and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Trier par fréquence
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:top_n]]
        
        return keywords
    
    def split_sentences(self, text: str) -> List[str]:
        """Division en phrases"""
        if self.nlp:
            try:
                doc = self.nlp(text)
                return [sent.text.strip() for sent in doc.sents]
            except:
                pass
        
        # Fallback basé sur la ponctuation
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def preprocess_pipeline(self, text: str, 
                           normalize: bool = True,
                           remove_stopwords: bool = False,
                           lemmatize: bool = False) -> str:
        """Pipeline complet de prétraitement"""
        result = text
        
        if normalize:
            result = self.normalize_text(result)
        
        if lemmatize:
            result = self.lemmatize(result)
        
        if remove_stopwords:
            result = self.remove_stopwords(result)
        
        return result

# Test rapide
if __name__ == "__main__":
    preprocessor = TextPreprocessor(language="fr")
    
    test_texts = [
        "Bonjour! Je suis très intéressé par vos services.",
        "J'ai commandé un produit le 15 mars 2024."
    ]
    
    for text in test_texts:
        print(f"\nTexte original: {text}")
        
        # Test de normalisation
        normalized = preprocessor.normalize_text(text)
        print(f"Normalisé: {normalized}")
        
        # Test de tokenisation
        tokens = preprocessor.tokenize(text)
        print(f"Tokens: {tokens[:10]}")
        
        print("-" * 50)
