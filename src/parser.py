import re
from typing import List, Optional
from pydantic import BaseModel

class Scene(BaseModel):
    scene_id: int
    heading: str
    int_ext: str
    location: str
    time_of_day: str
    characters: List[str]
    action_text: str

class ScriptParser:
    def __init__(self):
        # Matches slugs like: INT. HOUSE - DAY or INT/EXT. CAR - NIGHT
        self.slug_pattern = re.compile(r'^(INT\.|EXT\.|INT/EXT\.|I/E\.?|INT\./EXT\.)\s+(.+?)(?:\s*[-–—]\s*(.*))?$', re.IGNORECASE)
        # Matches common transitions
        self.transition_pattern = re.compile(r'^(?:[A-Z\s]+ TO:|FADE OUT\.|FADE IN:|MATCH CUT TO:|DISSOLVE TO:)$')
        # Matches character names like "JOHN" or "SARAH (O.S.)"
        self.character_pattern = re.compile(r'^([A-Z0-9][A-Z0-9\s\'\.]*[A-Z0-9])(?:\s*\(.*?\))?$')

    def parse(self, text: str) -> List[Scene]:
        scenes = []
        lines = text.split('\n')
        
        current_scene = None
        scene_counter = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_stripped = line.strip()
            
            if not line_stripped:
                if current_scene and current_scene['action_text']:
                    if not current_scene['action_text'].endswith('\n'):
                        current_scene['action_text'] += "\n"
                i += 1
                continue
                
            slug_match = self.slug_pattern.match(line_stripped)
            if slug_match:
                if current_scene:
                    current_scene['action_text'] = current_scene['action_text'].strip()
                    scenes.append(Scene(**current_scene))
                
                scene_counter += 1
                int_ext_raw = slug_match.group(1).upper()
                location = slug_match.group(2).strip().upper()
                time_of_day = slug_match.group(3).strip().upper() if slug_match.group(3) else ""
                
                # Normalize int_ext
                int_ext_raw = int_ext_raw.replace('.', '')
                if int_ext_raw in ["INT", "EXT"]:
                    int_ext = int_ext_raw
                else:
                    int_ext = "INT/EXT"
                    
                current_scene = {
                    "scene_id": scene_counter,
                    "heading": line_stripped,
                    "int_ext": int_ext,
                    "location": location,
                    "time_of_day": time_of_day,
                    "characters": [],
                    "action_text": ""
                }
            elif current_scene:
                char_match = self.character_pattern.match(line_stripped)
                is_transition = self.transition_pattern.match(line_stripped)
                
                if char_match and not is_transition:
                    # Look ahead for dialogue (non-empty line)
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if j < len(lines) and lines[j].strip() and not self.slug_pattern.match(lines[j].strip()):
                        char_name = char_match.group(1).strip()
                        if char_name not in current_scene["characters"] and char_name not in ["CONTINUED"]:
                            current_scene["characters"].append(char_name)
                
                if current_scene['action_text']:
                    if not current_scene['action_text'].endswith('\n'):
                        current_scene['action_text'] += "\n"
                    current_scene['action_text'] += line_stripped
                else:
                    current_scene['action_text'] = line_stripped
            
            i += 1
            
        if current_scene:
            current_scene['action_text'] = current_scene['action_text'].strip()
            scenes.append(Scene(**current_scene))
            
        return scenes
