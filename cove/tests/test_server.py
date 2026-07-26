import os
import sys
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import numpy as np

# Ensure we can import from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Patch the engines BEFORE importing server to avoid startup load
with patch('server.AIEnginePool'), \
    patch('server.SearchEngine'), \
    patch('server.VectorStorage'):
    from server import app

client = TestClient(app)

@pytest.fixture
def mock_engines():
    """Mocks the global engines in server.py"""
    with patch('server.ai_pool') as mock_pool, \
         patch('server.search_engine') as mock_search, \
         patch('server.storage') as mock_storage, \
         patch('server.search_storage') as mock_search_storage:
        
        # Configure AI Engine Mock
        mock_face = MagicMock()
        mock_face.bbox = [0, 0, 100, 100]
        # Create a valid embedding
        mock_face.embedding = np.random.rand(512).astype('float32')
        mock_engine = MagicMock()
        mock_engine.get_faces.return_value = [mock_face]
        mock_pool.borrow.return_value.__enter__.return_value = mock_engine
        
        # Configure Search Engine Mock
        mock_search.get_text_embedding.return_value = np.random.rand(512).astype('float32')
        
        # Configure Storage Mock
        mock_search_storage.search.return_value = [
            {"path": "test_images/test.jpg", "score": 0.95}
        ]
        
        yield mock_engine, mock_search, mock_storage, mock_search_storage

def test_startup():
    """Test that startup event initializes engines (mocked)"""
    with patch('server.AIEnginePool') as MockAI, \
         patch('server.SearchEngine') as MockSearch, \
         patch('server.VectorStorage') as MockStorage:
        
        with TestClient(app) as c:
            # Trigger startup
            pass
            
        assert MockAI.called
        assert MockSearch.called
        assert MockStorage.called

def test_search_endpoint(mock_engines):
    """Test /search/text endpoint"""
    response = client.post("/search/text", json={"text": "man in suit", "limit": 5})
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert data["results"][0]["path"] == "test_images/test.jpg"

@patch("cv2.imread")
@patch("os.path.exists")
def test_index_image_endpoint(mock_exists, mock_imread, mock_engines):
    """Test /index/image endpoint"""
    mock_engine, _, mock_storage, _ = mock_engines
    
    # Setup FS mocks
    mock_exists.return_value = True
    # Return a dummy image (H, W, C)
    mock_imread.return_value = np.zeros((320, 320, 3), dtype=np.uint8)
    
    response = client.post("/index/image", json={"file_path": "test_images/test_image.jpg"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "indexed"
    
    # Verify we called the engine and storage
    mock_engine.get_faces.assert_called_once()
    mock_storage.add.assert_called_once()
    mock_storage.save.assert_called_once()

@patch("os.path.exists")
def test_index_image_not_found(mock_exists, mock_engines):
    """Test 404 behavior"""
    mock_exists.return_value = False
    
    response = client.post("/index/image", json={"file_path": "test_images/nonexistent.jpg"})
    
    assert response.status_code == 404
