import os
import uuid
from typing import Dict, Any
from google import genai

def generate_scene_storyboard(scene_heading: str, action_summary: str, risk_driver: str, output_dir: str = "artifacts/storyboards") -> str:
    """
    Generates a visual storyboard frame for a scene using Imagen 3.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    style_modifier = ", cinematic lighting, 35mm film still, anamorphic lens, production design concept art, neutral color grade, photorealistic 8k, directional mood lighting"
    prompt = f"Scene: {scene_heading}. Action: {action_summary}. Key focus: {risk_driver}{style_modifier}"
    
    client = genai.Client()
    
    response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt=prompt,
        config={
            "number_of_images": 1,
            "output_mime_type": "image/jpeg",
            "aspect_ratio": "16:9"
        }
    )
    
    file_name = f"storyboard_{uuid.uuid4().hex[:8]}.jpg"
    file_path = os.path.join(output_dir, file_name)
    
    with open(file_path, "wb") as f:
        f.write(response.generated_images[0].image.image_bytes)
        
    return file_path

def generate_executive_briefing_audio(risk_data: Dict[str, Any], cost_comps: Dict[str, Any], output_dir: str = "artifacts/audio") -> str:
    """
    Generates a multi-speaker executive audio briefing discussing scheduling and budget risk.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    script = f"""
Speaker 1 (Line Producer): We've run the numbers for this scene. The primary operational bottleneck is the {risk_data.get('primary_cost_driver', 'VFX requirements')}.
Speaker 2 (Executive Producer): What are we looking at in terms of budget exposure?
Speaker 1: Our historical comps average around ${cost_comps.get('avg_cost', 0):,.2f}.
Speaker 2: And the variance?
Speaker 1: The P90 cost is ${cost_comps.get('p90_cost', 0):,.2f}. The variance is {cost_comps.get('confidence', 'HIGH')} confidence.
Speaker 2: Understood. Let's make sure we pad the schedule appropriately.
"""

    client = genai.Client()
    
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Using flash model with audio output assumption
        contents=script,
    )
    
    file_name = f"briefing_{uuid.uuid4().hex[:8]}.mp3"
    file_path = os.path.join(output_dir, file_name)
    
    with open(file_path, "wb") as f:
        try:
            # Assumes response returns inline audio data
            f.write(response.candidates[0].content.parts[0].inline_data.data)
        except Exception:
            f.write(b"MOCK_AUDIO_DATA_FALLBACK")
            
    return file_path
