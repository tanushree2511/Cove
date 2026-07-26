# tests/test_engine.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# Mock the expensive ONNX Runtime so we don't need a GPU for logic tests
@patch('ai_engine.FaceAnalysis') 
def test_face_detection_logic(mock_face_analysis):
    from ai_engine import AIEngine
    
    # Setup Mock
    mock_app = MagicMock()
    # Simulate returning 1 face
    mock_face = MagicMock()
    mock_face.bbox = np.array([10, 10, 100, 100])
    mock_face.embedding = np.random.rand(512).astype('float32')
    mock_app.get.return_value = [mock_face]
    
    mock_face_analysis.return_value = mock_app

    # Run Code
    engine = AIEngine()
    faces = engine.get_faces(np.zeros((320, 320, 3), dtype='uint8'))

    # Assertions
    assert len(faces) == 1
    assert faces[0].embedding.shape == (512,)