import pytest
from unittest.mock import patch
from src.agent.orchestrator import run_callsheet_pipeline, build_callsheet_agent

@patch('src.agent.orchestrator.Agent')
def test_run_callsheet_pipeline(mock_agent_class):
    mock_agent_instance = mock_agent_class.return_value
    mock_agent_instance.query.return_value = {"output": "Final Executive Greenlight Report"}
    
    script_text = "INT. WAREHOUSE - NIGHT\n\nMassive explosions!"
    
    result = run_callsheet_pipeline(script_text)
    
    assert "Final Executive Greenlight Report" in result
    mock_agent_class.assert_called_once()
    mock_agent_instance.query.assert_called_once()

def test_build_callsheet_agent():
    agent = build_callsheet_agent()
    assert agent is not None
    assert len(agent.tools) == 5
    assert "Lead Production Intelligence Orchestrator" in agent.system_instruction
