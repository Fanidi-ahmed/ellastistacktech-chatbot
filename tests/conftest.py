"""Configuration partagée pour tous les tests"""
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """Fixture pour le client de test API"""
    from src.api.rest_api import app
    return TestClient(app)

@pytest.fixture
def sample_message():
    """Message de test"""
    return {
        "message": "Bonjour",
        "session_id": "test_session_123",
        "user_id": "test_user"
    }

@pytest.fixture
def mock_request():
    """Mock d'une requête HTTP avec metadata"""
    from fastapi import Request
    from starlette.datastructures import Headers, QueryParams
    
    class MockRequest:
        def __init__(self):
            self.method = "POST"
            self.url = "http://test/api/chat"
            self.headers = Headers({"content-type": "application/json"})
            self.query_params = QueryParams({})
            self.client = ("127.0.0.1", 8000)
            self.cookies = {}
            self.state = type('State', (), {})()
            self.state.metadata = {
                "timestamp": "2024-01-01T00:00:00",
                "version": "1.0.0",
                "client": "test"
            }
    
    return MockRequest()
