import re
from typing import Dict, Set
from pydantic import BaseModel, Field
from src.parser import Scene
from google import genai

class RiskRationale(BaseModel):
    risk_level: str = Field(description="'LOW', 'MEDIUM', or 'HIGH'")
    primary_cost_driver: str = Field(description="Primary operational bottleneck identified")
    rationale: str = Field(description="Strict 1-sentence explanation based purely on provided metrics")

class SceneRiskScorer:
    def __init__(self, api_key: str = None):
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
        self.seen_locations: Set[str] = set()
        self.vfx_keywords = [
            r"explode", r"explosion", r"crash", r"fire", r"flood", r"cgi", 
            r"green screen", r"wirework", r"creature", r"laser", r"blast", r"destruction"
        ]
        self.vfx_pattern = re.compile(r'\b(?:' + '|'.join(self.vfx_keywords) + r')\b', re.IGNORECASE)

    def extract_features(self, scene: Scene) -> Dict[str, float]:
        text = scene.action_text
        # Rough word count
        word_count = max(len(text.split()), 1)
        vfx_matches = self.vfx_pattern.findall(text)
        
        # Calculate density as a percentage
        vfx_density = (len(vfx_matches) / word_count) * 100
        
        cast_count = len(scene.characters)
        
        is_night_ext = 1 if scene.int_ext == 'EXT' and scene.time_of_day == 'NIGHT' else 0
        
        self.seen_locations.add(scene.location)
        location_novelty = len(self.seen_locations)
        
        # Weighted formula
        raw_score = (vfx_density * 3.5) + (cast_count * 0.4) + (is_night_ext * 2.5) + (min(location_novelty, 5) * 0.3)
        risk_score = min(10.0, round(raw_score, 2))
        
        return {
            "vfx_density": round(vfx_density, 2),
            "cast_count": cast_count,
            "is_night_ext": is_night_ext,
            "location_novelty": location_novelty,
            "risk_score": risk_score
        }

    def get_tier2_rationale(self, features: Dict[str, float]) -> RiskRationale:
        prompt = f"""
        Analyze the following scene risk metrics and provide a strict 1-sentence rationale based purely on these numbers. 
        Do not invent production details or hallucinate.
        
        Metrics:
        - VFX Keyword Density: {features['vfx_density']}%
        - Cast Count: {features['cast_count']}
        - Is Night Exterior: {features['is_night_ext']}
        - Location Novelty: {features['location_novelty']}
        - Overall Risk Score: {features['risk_score']} / 10.0
        """
        
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': RiskRationale,
                }
            )
            return RiskRationale.model_validate_json(response.text)
        except Exception as e:
            print(f"        -> [WARNING] Gemini API error ({e}). Using fallback rationale.")
            level = "HIGH" if features['risk_score'] >= 5.0 else ("MEDIUM" if features['risk_score'] >= 3.0 else "LOW")
            return RiskRationale(
                risk_level=level,
                primary_cost_driver="Unspecified (API Overloaded)",
                rationale="Fallback rationale generated due to temporary upstream API unavailability."
            )
