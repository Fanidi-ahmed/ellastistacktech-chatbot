import pytest

@pytest.fixture
def mock_vector_store():
    class MockVectorStore:
        def search(self, query):
            return [{"content": "Test response", "score": 0.95}]
    return MockVectorStore()

def test_vector_store(mock_vector_store):
    result = mock_vector_store.search("test")
    assert len(result) > 0
    assert "content" in result[0]
