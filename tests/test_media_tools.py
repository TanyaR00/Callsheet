import pytest
from unittest.mock import patch, MagicMock, mock_open
from src.tools.media_tools import generate_scene_storyboard, generate_executive_briefing_audio

@patch('src.tools.media_tools.genai.Client')
@patch('builtins.open', new_callable=mock_open)
@patch('os.makedirs')
def test_generate_scene_storyboard(mock_makedirs, mock_file, mock_genai_client):
    mock_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    
    mock_image = MagicMock()
    mock_image.image.image_bytes = b"fake_image_bytes"
    mock_response.generated_images = [mock_image]
    
    mock_instance.models.generate_images.return_value = mock_response
    
    output_path = generate_scene_storyboard("INT. CAFE - DAY", "They drink coffee.", "None")
    
    assert "storyboard_" in output_path
    assert output_path.endswith(".jpg")
    mock_file.assert_called_once_with(output_path, "wb")
    mock_file().write.assert_called_once_with(b"fake_image_bytes")

@patch('src.tools.media_tools.genai.Client')
@patch('builtins.open', new_callable=mock_open)
@patch('os.makedirs')
def test_generate_executive_briefing_audio(mock_makedirs, mock_file, mock_genai_client):
    mock_instance = mock_genai_client.return_value
    mock_response = MagicMock()
    
    mock_part = MagicMock()
    mock_part.inline_data.data = b"fake_audio_bytes"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    
    mock_instance.models.generate_content.return_value = mock_response
    
    risk_data = {"primary_cost_driver": "Explosions"}
    cost_comps = {"avg_cost": 50000, "p90_cost": 75000, "confidence": "LOW (High Variance)"}
    
    output_path = generate_executive_briefing_audio(risk_data, cost_comps)
    
    assert "briefing_" in output_path
    assert output_path.endswith(".mp3")
    mock_file.assert_called_once_with(output_path, "wb")
    mock_file().write.assert_called_once_with(b"fake_audio_bytes")
