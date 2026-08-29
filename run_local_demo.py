import os
from typing import Dict, Any

from src.agent.orchestrator import (
    run_callsheet_pipeline, 
    parse_script_tool, 
    score_scene_risk_tool, 
    query_scene_comps_tool, 
    generate_scene_storyboard_tool, 
    generate_executive_briefing_audio_tool
)

def print_table(scenes):
    print(f"\n{'-'*95}")
    print(f"{'SCENE ID':<10} | {'LOCATION':<20} | {'RISK':<5} | {'COMP COST':<15} | {'CONFIDENCE':<20}")
    print(f"{'-'*95}")
    for s in scenes:
        scene_id = f"Scene {s.get('scene_id', '?')}"
        location = s.get('location', 'Unknown')[:20]
        risk = s.get('risk_score', 0.0)
        cost = s.get('comp_avg_cost', 'N/A')
        if isinstance(cost, float) or isinstance(cost, int):
            cost = f"${cost:,.2f}"
        conf = s.get('comp_confidence', 'N/A')
        print(f"{scene_id:<10} | {location:<20} | {risk:<5} | {cost:<15} | {conf:<20}")
    print(f"{'-'*95}\n")

def run_demo():
    print("Loading sample script...")
    with open("fixtures/sample_script.fountain", "r") as f:
        script_text = f.read()

    os.makedirs("output", exist_ok=True)

    print("\n" + "="*50)
    print("--- CALLSHEET PIPELINE DEMO: AUTONOMOUS LOGS ---")
    print("="*50)
    
    print("\n[AGENT] Step 1: Parsing Script...")
    scenes = parse_script_tool(script_text)
    print(f"[AGENT] Parsed {len(scenes)} scenes.")
    
    scored_scenes = []
    
    for idx, scene in enumerate(scenes):
        print(f"\n[AGENT] Analyzing Scene {scene['scene_id']}: {scene['heading']}")
        
        # Risk Scoring
        risk_data = score_scene_risk_tool(scene)
        risk_score = risk_data['features']['risk_score']
        scene['risk_score'] = risk_score
        scene['primary_cost_driver'] = risk_data['rationale']['primary_cost_driver']
        
        print(f"        -> Risk Score: {risk_score}/10.0")
        
        if risk_score < 5.0:
            print("        -> Decision: Risk < 5.0. Skipping expensive comp lookup and media generation.")
            scene['comp_avg_cost'] = "Skipped"
            scene['comp_confidence'] = "Skipped"
        else:
            print("        -> Decision: Risk >= 5.0. Triggering ClickHouse comp search...")
            comp_data = query_scene_comps_tool(scene['action_text'], scene['int_ext'], len(scene['characters']))
            
            if 'error' in comp_data:
                print(f"        -> [WARNING] Comp Search Error: {comp_data['error']}")
                scene['comp_avg_cost'] = "Error"
                scene['comp_confidence'] = "Error"
            else:
                scene['comp_avg_cost'] = comp_data['avg_cost']
                scene['comp_confidence'] = comp_data['confidence']
                print(f"        -> Found Comps: Avg Cost ${comp_data['avg_cost']:,.2f} | Confidence: {comp_data['confidence']}")
                
                if "LOW" in comp_data['confidence'].upper():
                    print("        -> [FLAG] High variance detected. Flagging for executive summary.")
                    
        scored_scenes.append(scene)

    # Sort scenes by risk to find top 3
    sorted_scenes = sorted(scored_scenes, key=lambda x: x['risk_score'], reverse=True)
    top_3 = sorted_scenes[:3]
    
    print("\n[AGENT] Triggering Media Generation for high risk scenes...")
    
    highest_risk_scene = top_3[0] if top_3 else None
    
    for i, scene in enumerate(top_3):
        if scene['risk_score'] >= 5.0:
            print(f"[AGENT] Generating Storyboard for Scene {scene['scene_id']}...")
            try:
                sb_path = generate_scene_storyboard_tool(scene['heading'], scene['action_text'], scene['primary_cost_driver'], output_dir="output")
                print(f"        -> Storyboard saved to {sb_path}")
            except Exception as e:
                print(f"        -> Storyboard failed (Check API keys): {e}")

    if highest_risk_scene and highest_risk_scene['risk_score'] >= 5.0:
        print(f"\n[AGENT] Generating Executive Briefing Audio for highest risk scene (Scene {highest_risk_scene['scene_id']})...")
        try:
            risk_info = {"primary_cost_driver": highest_risk_scene['primary_cost_driver']}
            comp_info = {
                "avg_cost": highest_risk_scene.get('comp_avg_cost', 0.0) if isinstance(highest_risk_scene.get('comp_avg_cost'), (float, int)) else 100000.0,
                "p90_cost": 150000.0,
                "confidence": highest_risk_scene.get('comp_confidence', 'UNKNOWN')
            }
            audio_path = generate_executive_briefing_audio_tool(risk_info, comp_info, output_dir="output")
            print(f"        -> Audio saved to {audio_path}")
        except Exception as e:
            print(f"        -> Audio failed (Check API keys): {e}")

    print("\n" + "="*50)
    print("--- FINAL EXECUTIVE SUMMARY REPORT ---")
    print("="*50)
    print_table(scored_scenes)
    
    print("\n[AGENT] Attempting autonomous pipeline run via Orchestrator (vertexai.preview.reasoning_engines)...")
    try:
        report = run_callsheet_pipeline(script_text)
        print(f"Orchestrator output:\n{report}")
    except Exception as e:
        print(f"Orchestrator failed (expected if Vertex AI ADK is not configured): {e}")

if __name__ == '__main__':
    run_demo()
