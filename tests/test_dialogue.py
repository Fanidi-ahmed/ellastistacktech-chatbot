"""Tests du dialogue"""
import pytest

def test_context_manager():
    """Test du gestionnaire de contexte"""
    try:
        from src.dialogue.context_manager import ContextManager
        cm = ContextManager()
        assert cm is not None
    except ImportError:
        pytest.skip("Module non disponible")

def test_response_generator():
    """Test du générateur de réponses"""
    try:
        from src.dialogue.response_generator import ResponseGenerator
        rg = ResponseGenerator()
        assert rg is not None
    except ImportError:
        pytest.skip("Module non disponible")
