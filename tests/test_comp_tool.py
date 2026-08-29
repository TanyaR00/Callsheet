import pytest
from unittest.mock import patch, MagicMock
from src.tools.comp_tool import query_scene_comps

@patch('src.tools.comp_tool.genai.Client')
@patch('src.tools.comp_tool.clickhouse_connect.get_client')
def test_query_scene_comps_high_confidence(mock_ch_client, mock_genai_client):
    # Mock GenAI response
    mock_genai_instance = mock_genai_client.return_value
    mock_embed_response = MagicMock()
    mock_embed_response.embeddings = [MagicMock(values=[0.1]*768)]
    mock_genai_instance.models.embed_content.return_value = mock_embed_response
    
    # Mock ClickHouse response (low variance: 1000/11000 = 0.09 < 0.4)
    mock_ch_instance = mock_ch_client.return_value
    mock_ch_result = MagicMock()
    mock_ch_result.named_results.return_value = [{
        'p10_cost': 10000.0,
        'median_cost': 11000.0,
        'p90_cost': 12000.0,
        'avg_cost': 11000.0,
        'cost_stddev': 1000.0,
        'comp_count': 5
    }]
    mock_ch_instance.query.return_value = mock_ch_result
    
    result = query_scene_comps("A quiet dialogue in a cafe", "INT", 2)
    
    assert result['confidence'] == "HIGH"
    assert result['avg_cost'] == 11000.0
    assert result['cost_stddev'] == 1000.0

@patch('src.tools.comp_tool.genai.Client')
@patch('src.tools.comp_tool.clickhouse_connect.get_client')
def test_query_scene_comps_low_confidence(mock_ch_client, mock_genai_client):
    mock_genai_instance = mock_genai_client.return_value
    mock_embed_response = MagicMock()
    mock_embed_response.embeddings = [MagicMock(values=[0.1]*768)]
    mock_genai_instance.models.embed_content.return_value = mock_embed_response
    
    # Mock ClickHouse response (high variance: 5000/10000 = 0.5 > 0.4)
    mock_ch_instance = mock_ch_client.return_value
    mock_ch_result = MagicMock()
    mock_ch_result.named_results.return_value = [{
        'p10_cost': 5000.0,
        'median_cost': 10000.0,
        'p90_cost': 15000.0,
        'avg_cost': 10000.0,
        'cost_stddev': 5000.0,
        'comp_count': 5
    }]
    mock_ch_instance.query.return_value = mock_ch_result
    
    result = query_scene_comps("An explosive car chase", "EXT", 4)
    
    assert result['confidence'] == "LOW (High Variance)"
