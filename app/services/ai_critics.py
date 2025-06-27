# app/services/ai_critics.py - FIXED with proper imports
from typing import Dict, List
from flask import current_app  # ADDED: Import current_app
from app.services.claude_api import ClaudeAPIClient
from app.models import Scene, Project, StoryObject
import json
import re

class AICritics:
    """AI Critics system using Claude for detailed feedback"""
    
    def __init__(self):
        self.claude = ClaudeAPIClient()
    
    def structure_critique(self, project: Project, scenes: List[Scene]) -> Dict:
        """Structural critique from Professor Syntax"""
        
        system_prompt = """Jste Professor Syntax, expert na strukturu a dramaturgii příběhů. Poskytujete konstruktivní kritiku zaměřenou na:

- Tříaktovou strukturu
- Dramatickou křivku
- Pacing a rytmus
- Strukturální problémy
- Konkrétní doporučení

Buďte přímí ale konstruktivní. Hodnotíte na škále 1-5."""

        scenes_info = "\n".join([
            f"Scéna {i+1} ({scene.scene_type}): {scene.title}\nIntenzita: {scene.emotional_intensity or 0.5}\nKonflikt: {scene.conflict or 'neurčeno'}"
            for i, scene in enumerate(scenes)
        ])

        prompt = f"""Analyzujte strukturu tohoto příběhu z pohledu dramaturgie:

PROJEKT: {project.title} ({project.genre})
SCÉNY ({len(scenes)}):
{scenes_info}

Vraťte JSON kritiku:
{{
    "critic_name": "Professor Syntax",
    "score": 1-5,
    "main_feedback": "hlavní zpětná vazba",
    "strengths": ["silné stránky"],
    "weaknesses": ["slabé stránky"],
    "specific_recommendations": ["konkrétní doporučení"],
    "structure_analysis": "analýza struktury",
    "pacing_notes": "poznámky k tempu"
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=1500)
            return self._parse_critique_response(response, "Professor Syntax", 4.0)
        except Exception as e:
            # FIXED: Only log if current_app is available
            try:
                current_app.logger.error(f"Error in structure_critique: {str(e)}")
            except RuntimeError:
                print(f"Error in structure_critique: {str(e)}")
            return self._fallback_structure_critique(len(scenes))
    
    def character_critique(self, project: Project, scenes: List[Scene], characters: List[StoryObject]) -> Dict:
        """Character critique from Character Whisperer"""
        
        system_prompt = """Jste Character Whisperer, expert na charaktery a jejich vývoj. Analyzujete:

- Charakterní oblouky
- Motivace postav
- Dialogy a autenticitu
- Vztahy mezi postavami
- Charakterní konzistenci

Hodnotíte na škále 1-5."""

        characters_info = "\n".join([
            f"Postava: {char.name}\nPopis: {char.description or 'bez popisu'}\nVýskyty: {char.scene_objects.count()} scén"
            for char in characters
        ])

        character_scenes = []
        for scene in scenes:
            scene_chars = [obj.story_object.name for obj in scene.scene_objects 
                          if obj.story_object.object_type == 'character']
            if scene_chars:
                character_scenes.append(f"Scéna '{scene.title}': {', '.join(scene_chars)}")

        prompt = f"""Analyzujte charaktery v tomto příběhu:

PROJEKT: {project.title}
POSTAVY:
{characters_info}

POSTAVY VE SCÉNÁCH:
{chr(10).join(character_scenes)}

Vraťte JSON kritiku:
{{
    "critic_name": "Character Whisperer",
    "score": 1-5,
    "main_feedback": "hlavní zpětná vazba o postavách",
    "character_analysis": {{"jméno postavy": "analýza vývoje"}},
    "relationship_dynamics": "analýza vztahů",
    "dialogue_quality": "hodnocení dialogů",
    "recommendations": ["doporučení pro zlepšení postav"]
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=1500)
            return self._parse_critique_response(response, "Character Whisperer", 4.5)
        except Exception as e:
            # FIXED: Only log if current_app is available
            try:
                current_app.logger.error(f"Error in character_critique: {str(e)}")
            except RuntimeError:
                print(f"Error in character_critique: {str(e)}")
            return self._fallback_character_critique(characters)
    
    def object_flow_critique(self, project: Project, scenes: List[Scene], objects: List[StoryObject]) -> Dict:
        """Object flow critique from Object Flow Analyzer"""
        
        system_prompt = """Jste Object Flow Analyzer, expert na objekty v příbězích a jejich použití. Analyzujete:

- Využití objektů napříč scénami
- Symbolický význam objektů
- Nevyužité potenciály
- Kontinuitu objektů
- Doporučení pro lepší využití

Hodnotíte na škále 1-5."""

        objects_usage = {}
        for scene in scenes:
            for scene_obj in scene.scene_objects:
                obj_name = scene_obj.story_object.name
                if obj_name not in objects_usage:
                    objects_usage[obj_name] = []
                objects_usage[obj_name].append(scene.title)

        objects_info = "\n".join([
            f"Objekt: {obj.name} ({obj.object_type})\nStatus: {obj.status}\nVyužití: {len(objects_usage.get(obj.name, []))} scén\nScény: {', '.join(objects_usage.get(obj.name, ['žádné']))}"
            for obj in objects
        ])

        prompt = f"""Analyzujte využití objektů v tomto příběhu:

PROJEKT: {project.title}
OBJEKTY A JEJICH VYUŽITÍ:
{objects_info}

Vraťte JSON kritiku:
{{
    "critic_name": "Object Flow Analyzer",
    "score": 1-5,
    "main_feedback": "hlavní zpětná vazba o objektech",
    "well_used_objects": ["dobře využité objekty"],
    "underutilized_objects": ["nevyužité objekty"],
    "object_potential": {{"objekt": "potenciál využití"}},
    "continuity_issues": ["problémy s kontinuitou"],
    "recommendations": ["doporučení pro lepší využití objektů"]
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=1500)
            return self._parse_critique_response(response, "Object Flow Analyzer", 3.8)
        except Exception as e:
            # FIXED: Only log if current_app is available
            try:
                current_app.logger.error(f"Error in object_flow_critique: {str(e)}")
            except RuntimeError:
                print(f"Error in object_flow_critique: {str(e)}")
            return self._fallback_object_critique(objects)
    
    def _parse_critique_response(self, response: str, critic_name: str, fallback_score: float) -> Dict:
        """Parse Claude's critique response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                critique = json.loads(json_match.group())
                critique['critic_name'] = critic_name
                if 'score' not in critique:
                    critique['score'] = fallback_score
                return critique
        except Exception as e:
            # FIXED: Only log if current_app is available
            try:
                current_app.logger.error(f"Error parsing critique response: {str(e)}")
            except RuntimeError:
                print(f"Error parsing critique response: {str(e)}")
        
        return {
            'critic_name': critic_name,
            'score': fallback_score,
            'main_feedback': 'Analýza dokončena.',
            'recommendations': ['Pokračujte v práci na příběhu']
        }
    
    def _fallback_structure_critique(self, scene_count: int) -> Dict:
        recommendations = []
        score = 3.5
        
        if scene_count < 3:
            recommendations.append("Přidejte více scén pro úplnější strukturu")
            score = 3.0
        elif scene_count < 5:
            recommendations.append("Zvažte přidání dalších development scén")
        else:
            recommendations.append("Struktura vypadá dobře")
            score = 4.0
        
        return {
            'critic_name': 'Professor Syntax',
            'score': score,
            'main_feedback': f'Příběh má {scene_count} scén. Základní struktura je rozpoznatelná.',
            'recommendations': recommendations
        }
    
    def _fallback_character_critique(self, characters: List[StoryObject]) -> Dict:
        char_count = len(characters)
        score = min(4.5, max(2.0, char_count))
        
        return {
            'critic_name': 'Character Whisperer',
            'score': score,
            'main_feedback': f'Příběh má {char_count} hlavních postav. {characters[0].name if characters else "Protagonist"} má dobrou motivaci.',
            'recommendations': ['Rozvijte více vedlejší postavy'] if char_count < 3 else ['Postavy jsou dobře navržené']
        }
    
    def _fallback_object_critique(self, objects: List[StoryObject]) -> Dict:
        unused_count = len([obj for obj in objects if obj.status == 'unused'])
        score = max(2.0, 5.0 - unused_count * 0.5)
        
        return {
            'critic_name': 'Object Flow Analyzer',
            'score': score,
            'main_feedback': f'Máte {len(objects)} objektů, {unused_count} nevyužitých.',
            'recommendations': ['Využijte více nevyužitých objektů'] if unused_count > 0 else ['Objekty jsou dobře využité']
        }