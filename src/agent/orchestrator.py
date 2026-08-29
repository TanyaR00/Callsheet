import os
from typing import Dict, Any, List

try:
    from vertexai.preview.reasoning_engines import Agent
except ImportError:
    # Fallback for local testing if the full vertexai ADK is not installed
    class Agent:
        def __init__(self, model, tools, system_instruction):
            self.model = model
            self.tools = tools
            self.system_instruction = system_instruction
        def query(self, input: str, **kwargs) -> Dict[str, Any]:
            return {"output": "Mocked Executive Greenlight Report (ADK not installed)"}

from src.parser import ScriptParser, Scene
from src.scorer import SceneRiskScorer
from src.tools.comp_tool import query_scene_comps
from src.tools.media_tools import generate_scene_storyboard, generate_executive_briefing_audio

def parse_script_tool(script_text: str) -> List[Dict[str, Any]]:
    """Parses a raw screenplay text into structured scenes. Returns a list of scene dictionaries."""
    parser = ScriptParser()
    scenes = parser.parse(script_text)
    return [s.model_dump() for s in scenes]

def score_scene_risk_tool(scene_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates deterministic risk scores and generates a rationale for a scene."""
    scorer = SceneRiskScorer()
    scene = Scene(**scene_dict)
    features = scorer.extract_features(scene)
    rationale = scorer.get_tier2_rationale(features)
    
    return {
        "features": features,
        "rationale": rationale.model_dump()
    }

def query_scene_comps_tool(scene_description: str, int_ext: str, cast_count: int) -> Dict[str, Any]:
    """Finds historical scene cost comps using ClickHouse vector similarity."""
    return query_scene_comps(scene_description, int_ext, cast_count)

def generate_scene_storyboard_tool(scene_heading: str, action_summary: str, risk_driver: str) -> str:
    """Generates a visual storyboard frame for high-risk scenes. Returns the file path."""
    return generate_scene_storyboard(scene_heading, action_summary, risk_driver)

def generate_executive_briefing_audio_tool(risk_data: Dict[str, Any], cost_comps: Dict[str, Any]) -> str:
    """Generates a multi-speaker executive audio briefing discussing scheduling and budget risk. Returns the file path."""
    return generate_executive_briefing_audio(risk_data, cost_comps)

def build_callsheet_agent() -> Agent:
    """Initializes and returns the ADK Agent with strict autonomous reasoning instructions."""
    system_instruction = (
        "You are the Lead Production Intelligence Orchestrator (Callsheet AI). "
        "Your role is to autonomously orchestrate scene analysis, cost estimation, and media generation "
        "to provide a comprehensive executive greenlight report.\n\n"
        "REASONING GUIDELINES & AUTONOMOUS BRANCHING:\n"
        "1. First, use `parse_script_tool` to parse the provided screenplay.\n"
        "2. Use `score_scene_risk_tool` to evaluate the risk score for each parsed scene.\n"
        "3. BRANCHING DECISION: For any scene where risk_score < 5.0, immediately skip expensive comp searches and image generation to conserve production budget and compute.\n"
        "4. BRANCHING DECISION: For any scene where risk_score >= 5.0, trigger the ClickHouse comp search using `query_scene_comps_tool`.\n"
        "5. MEDIA GENERATION: Identify the top-3 highest risk scenes overall. For these top 3 scenes ONLY, generate storyboard frames using `generate_scene_storyboard_tool`.\n"
        "6. VARIANCE FLAGGING: If ANY high-risk scene returns a 'LOW (High Variance)' confidence or confidence containing 'LOW' from the comp search, EXPLICITLY flag it as a severe risk in your final executive summary.\n"
        "7. AUDIO BRIEFING: Generate a single executive briefing audio for the absolute highest risk scene using `generate_executive_briefing_audio_tool`.\n"
        "8. Finally, compile all findings into a structured executive greenlight report outlining budget exposure, flagged risks, and generated media paths."
    )

    tools = [
        parse_script_tool,
        score_scene_risk_tool,
        query_scene_comps_tool,
        generate_scene_storyboard_tool,
        generate_executive_briefing_audio_tool
    ]

    agent = Agent(
        model="gemini-2.5-pro",
        tools=tools,
        system_instruction=system_instruction
    )
    
    return agent

def run_callsheet_pipeline(script_text: str) -> str:
    """
    Entry point to run the entire autonomous agent loop over a script.
    """
    agent = build_callsheet_agent()
    
    prompt = (
        f"Please analyze the following screenplay snippet. Adhere strictly to the reasoning guidelines "
        f"for risk triage, branching, and media generation. Return the final executive greenlight report.\n\n"
        f"SCRIPT:\n{script_text}"
    )
    
    # Execute ADK Agent query
    response = agent.query(input=prompt)
    
    # Depending on ADK version, it might return a dict or an object
    if isinstance(response, dict):
        return response.get("output", str(response))
    else:
        # Fallback if the agent returns an object with text or output attributes
        return getattr(response, "output", getattr(response, "text", str(response)))
