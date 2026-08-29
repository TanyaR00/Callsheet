import pytest
from src.parser import ScriptParser

def test_script_parser_basic_parsing():
    text = """
INT. COFFEE SHOP - DAY

SARAH (O.S.)
I can't believe this is happening.

JOHN
(sighs)
Believe it.

CUT TO:

EXT. STREET - CONTINUOUS

They walk out.

INT/EXT. CAR - NIGHT

They drive.

JOHN (V.O.)
It was a dark night.
    """
    parser = ScriptParser()
    scenes = parser.parse(text)
    
    assert len(scenes) == 3
    
    s1 = scenes[0]
    assert s1.scene_id == 1
    assert s1.int_ext == "INT"
    assert s1.location == "COFFEE SHOP"
    assert s1.time_of_day == "DAY"
    assert set(s1.characters) == {"SARAH", "JOHN"}
    assert "Believe it." in s1.action_text
    
    s2 = scenes[1]
    assert s2.scene_id == 2
    assert s2.int_ext == "EXT"
    assert s2.location == "STREET"
    assert s2.time_of_day == "CONTINUOUS"
    assert s2.characters == []
    
    s3 = scenes[2]
    assert s3.scene_id == 3
    assert s3.int_ext == "INT/EXT"
    assert s3.location == "CAR"
    assert s3.time_of_day == "NIGHT"
    assert s3.characters == ["JOHN"]

def test_script_parser_edge_cases():
    text = """
INT./EXT. SPACESHIP - UNKNOWN

ALIEN
Who goes there?

I/E. BUNKER - DUSK

SOLDIER
Nobody.
    """
    parser = ScriptParser()
    scenes = parser.parse(text)
    
    assert len(scenes) == 2
    
    s1 = scenes[0]
    assert s1.int_ext == "INT/EXT"
    assert s1.location == "SPACESHIP"
    assert s1.time_of_day == "UNKNOWN"
    assert s1.characters == ["ALIEN"]
    
    s2 = scenes[1]
    assert s2.int_ext == "INT/EXT"
    assert s2.location == "BUNKER"
    assert s2.time_of_day == "DUSK"
    assert s2.characters == ["SOLDIER"]
