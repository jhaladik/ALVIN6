# app/services/ai_analyzer.py - EXTENDED with Idea Analysis
import json
import re
from typing import Dict, List, Optional
from flask import current_app
from app.services.claude_api import ClaudeAPIClient
from app.models import StoryObject, Scene, Project

class AIAnalyzer:
    """AI Analyzer using Claude API for story analysis"""
    
    def __init__(self):
        self.claude = ClaudeAPIClient()
    
    def analyze_idea(self, idea_text: str, story_intent: str = None) -> Dict:
        """Analyze free-form idea text and extract story structure"""
        
        system_prompt = """Jste expert na analýzu a rozvoj příběhových nápadů. Umíte z volného textu extrahovat strukturované elementy příběhu a navrhnout další kroky.

Vaším úkolem je:
1. Analyzovat nápad a identifikovat klíčové elementy
2. Navrhnout žánr a tón příběhu  
3. Extrahovat objekty (postavy, lokace, objekty, konflikty)
4. Navrhnout první scénu
5. Poskytnout doporučení pro rozvoj

Odpovězte striktně ve formátu JSON bez dalšího textu."""

        intent_context = ""
        if story_intent:
            intent_context = f"\nUSER INTENT: Uživatel naznačil zájem o {story_intent}"

        prompt = f"""Analyzujte tento nápad a vytvořte strukturu příběhu:

NÁPAD:
{idea_text}
{intent_context}

Vraťte JSON ve formátu:
{{
    "story_assessment": {{
        "genre": "navržený žánr",
        "tone": "tón příběhu (dark/light/mysterious/comedic)",
        "target_audience": "cílová skupina",
        "estimated_scope": "rozsah (short-story/novella/novel)",
        "themes": ["hlavní témata"],
        "marketability": "komerční potenciál (1-5)"
    }},
    "extracted_objects": {{
        "characters": ["postava1", "postava2"],
        "locations": ["lokace1", "lokace2"], 
        "objects": ["objekt1", "objekt2"],
        "conflicts": ["konflikt1", "konflikt2"]
    }},
    "first_scene_suggestion": {{
        "title": "název první scény",
        "description": "detailní popis co se děje",
        "scene_type": "inciting/development/opening",
        "location": "kde se odehrává",
        "objects": ["objekty použité ve scéně"],
        "hook": "úvodní hook",
        "conflict": "konflikt ve scéně"
    }},
    "project_suggestions": {{
        "title": "navržený název projektu",
        "description": "popis projektu v 2-3 větách",
        "target_length": "cílová délka v slovech"
    }},
    "next_steps": {{
        "immediate_actions": ["co udělat hned"],
        "development_areas": ["oblasti k rozvoji"],
        "potential_subplots": ["možné vedlejší linky"]
    }}
}}

Buďte kreativní ale zůstaňte věrní původnímu nápadu."""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate and ensure all required fields exist
                self._validate_idea_analysis(result)
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            try:
                current_app.logger.error(f"Error in analyze_idea: {str(e)}")
            except RuntimeError:
                print(f"Error in analyze_idea: {str(e)}")
            
            # Fallback analysis
            return self._fallback_idea_analysis(idea_text, story_intent)
    
def _validate_idea_analysis(self, result: Dict) -> None:
    """Validate and fix idea analysis structure - ROBUST VERSION"""
    
    # --- Validace 'story_assessment' ---
    story_defaults = {
        'genre': 'drama',
        'tone': 'balanced',
        'target_audience': 'general',
        'estimated_scope': 'short-story',
        'themes': [],
        'marketability': 3
    }
    # Nejdříve zajisti, že 'story_assessment' existuje a je to slovník (dict)
    if 'story_assessment' not in result or not isinstance(result.get('story_assessment'), dict):
        result['story_assessment'] = {}
    # Až teď bezpečně doplň chybějící podklíče
    for key, default in story_defaults.items():
        result['story_assessment'].setdefault(key, default)

    # --- Validace 'extracted_objects' ---
    object_defaults = {
        'characters': [],
        'locations': [],
        'objects': [],
        'conflicts': []
    }
    if 'extracted_objects' not in result or not isinstance(result.get('extracted_objects'), dict):
        result['extracted_objects'] = {}
    for key, default in object_defaults.items():
        result['extracted_objects'].setdefault(key, default)
        # Dodatečná kontrola, zda je hodnota seznam (list)
        if not isinstance(result['extracted_objects'][key], list):
            result['extracted_objects'][key] = []
    
    # --- Validace 'first_scene_suggestion' ---
    scene_defaults = {
        'title': 'Úvodní scéna',
        'description': 'Úvodní scéna příběhu',
        'scene_type': 'opening',
        'location': '',
        'objects': [],
        'hook': '',
        'conflict': ''
    }
    if 'first_scene_suggestion' not in result or not isinstance(result.get('first_scene_suggestion'), dict):
        result['first_scene_suggestion'] = {}
    for key, default in scene_defaults.items():
        result['first_scene_suggestion'].setdefault(key, default)

    # --- Validace 'project_suggestions' ---
    project_defaults = {
        'title': 'Nový projekt',
        'description': 'Příběh vytvořený z nápadu',
        'target_length': '10000'
    }
    if 'project_suggestions' not in result or not isinstance(result.get('project_suggestions'), dict):
        result['project_suggestions'] = {}
    for key, default in project_defaults.items():
        result['project_suggestions'].setdefault(key, default)
        
    # --- Validace 'next_steps' ---
    steps_defaults = {
        'immediate_actions': [],
        'development_areas': [],
        'potential_subplots': []
    }
    if 'next_steps' not in result or not isinstance(result.get('next_steps'), dict):
        result['next_steps'] = {}
    for key, default in steps_defaults.items():
        result['next_steps'].setdefault(key, default)
        if not isinstance(result['next_steps'][key], list):
            result['next_steps'][key] = []
    
    def _fallback_idea_analysis(self, idea_text: str, story_intent: str = None) -> Dict:
        """Fallback idea analysis using simple text processing"""
        
        idea_lower = idea_text.lower()
        
        # Simple genre detection
        genre = 'drama'  # default
        if any(word in idea_lower for word in ['tajemství', 'záhada', 'dopis', 'šifra']):
            genre = 'mystery'
        elif any(word in idea_lower for word in ['sci-fi', 'budoucnost', 'robot', 'vesmír']):
            genre = 'sci-fi'
        elif any(word in idea_lower for word in ['láska', 'romance', 'srdce']):
            genre = 'romance'
        elif any(word in idea_lower for word in ['fantasy', 'magie', 'elf', 'trpaslík']):
            genre = 'fantasy'
        
        # Simple character extraction
        characters = []
        for name in ['sarah', 'pavel', 'anna', 'marie', 'tom', 'petr']:
            if name in idea_lower:
                characters.append(name.capitalize())
        
        # Simple location extraction  
        locations = []
        for loc in ['knihovna', 'dům', 'město', 'vesnice', 'škola', 'archiv']:
            if loc in idea_lower:
                locations.append(loc.capitalize())
        
        # Simple object extraction
        objects = []
        for obj in ['dopis', 'kniha', 'fotografie', 'klíč', 'telefon', 'auto']:
            if obj in idea_lower:
                objects.append(obj.capitalize())
        
        return {
            'story_assessment': {
                'genre': genre,
                'tone': 'mysterious' if genre == 'mystery' else 'balanced',
                'target_audience': 'general',
                'estimated_scope': 'short-story',
                'themes': ['family', 'secrets'] if 'tajemství' in idea_lower else ['adventure'],
                'marketability': 3
            },
            'extracted_objects': {
                'characters': characters or ['Protagonist'],
                'locations': locations or ['Unknown location'],
                'objects': objects,
                'conflicts': ['Internal struggle']
            },
            'first_scene_suggestion': {
                'title': 'Úvodní situace',
                'description': f'Příběh začíná když protagonista... {idea_text[:100]}',
                'scene_type': 'opening',
                'location': locations[0] if locations else '',
                'objects': objects[:2],
                'hook': 'Co se stane když...',
                'conflict': 'Protagonista čelí neočekávané situaci'
            },
            'project_suggestions': {
                'title': 'Nový příběh',
                'description': f'Příběh o {characters[0] if characters else "protagonistovi"} a jejich dobrodružství.',
                'target_length': '15000'
            },
            'next_steps': {
                'immediate_actions': ['Vytvořit projekt', 'Napsat první scénu'],
                'development_areas': ['Charakterizace postav', 'Rozvoj světa'],
                'potential_subplots': ['Vedlejší postavy', 'Romantická linka']
            }
        }

    def analyze_scene_objects(self, scene_description: str, project_context: str = "") -> Dict[str, List[str]]:
        """Extract objects from scene description using Claude"""
        
        system_prompt = """Jste expert na analýzu literárních textů. Vaším úkolem je analyzovat popis scény a extrahovat klíčové objekty.

Kategorie objektů:
- characters: Postavy (jména, role jako "matka", "knihovník")
- locations: Místa a lokace
- objects: Fyzické objekty, předměty, rekvizity
- conflicts: Konflikty, napětí, problémy

Odpovězte ve formátu JSON bez dalšího textu."""

        prompt = f"""Analyzujte tuto scénu a extrahujte objekty do kategorií:

POPIS SCÉNY:
{scene_description}

KONTEXT PROJEKTU:
{project_context}

Vraťte JSON ve formátu:
{{
    "characters": ["jméno1", "jméno2"],
    "locations": ["místo1", "místo2"],
    "objects": ["objekt1", "objekt2"],
    "conflicts": ["konflikt1", "konflikt2"]
}}

Buďte precizní a extrahujte pouze objekty explicitně zmíněné v textu."""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=1000)
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Validate structure
                expected_keys = ['characters', 'locations', 'objects', 'conflicts']
                for key in expected_keys:
                    if key not in result:
                        result[key] = []
                    if not isinstance(result[key], list):
                        result[key] = []
                
                return result
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            try:
                current_app.logger.error(f"Error in analyze_scene_objects: {str(e)}")
            except RuntimeError:
                print(f"Error in analyze_scene_objects: {str(e)}")
            
            # Fallback to simple keyword extraction
            return self._fallback_object_extraction(scene_description)
    
    def _fallback_object_extraction(self, description: str) -> Dict[str, List[str]]:
        """Fallback object extraction using keywords"""
        keywords = {
            'characters': [],
            'locations': [],
            'objects': [],
            'conflicts': []
        }
        
        description_lower = description.lower()
        
        # Character detection
        if 'sarah' in description_lower:
            keywords['characters'].append('Sarah')
        if 'pavel' in description_lower:
            keywords['characters'].append('Pavel')
        if 'matka' in description_lower or 'máma' in description_lower:
            keywords['characters'].append('Matka')
        if 'babička' in description_lower:
            keywords['characters'].append('Babička Anna')
        
        # Location detection
        locations = ['knihovna', 'pokoj', 'kavárna', 'dům', 'archiv', 'kancelář']
        for loc in locations:
            if loc in description_lower:
                keywords['locations'].append(loc.capitalize())
        
        # Object detection
        objects = ['dopis', 'fotografie', 'kniha', 'dokument', 'klíče', 'telefon']
        for obj in objects:
            if obj in description_lower:
                keywords['objects'].append(obj.capitalize())
        
        return keywords
    
    def analyze_story_structure(self, scenes: List[Scene], project: Project) -> Dict:
        """Analyze overall story structure using Claude"""
        
        system_prompt = """Jste expert na dramaturgii a strukturu příběhů. Analyzujete strukturu příběhu na základě scén a poskytnete detailní hodnocení.

Zaměřte se na:
- Dramatickou křivku a rozložení napětí
- Kontinuitu příběhu
- Vyvážení typů scén
- Chybějící elementy
- Konkrétní doporučení pro zlepšení"""

        scenes_text = "\n".join([
            f"Scéna {i+1} ({scene.scene_type}): {scene.title}\n{scene.description}\nLokace: {scene.location or 'neurčeno'}\nKonflikt: {scene.conflict or 'neurčeno'}"
            for i, scene in enumerate(scenes)
        ])

        prompt = f"""Analyzujte strukturu tohoto příběhu:

PROJEKT: {project.title}
ŽÁNR: {project.genre or 'neurčeno'}
POPIS: {project.description or 'bez popisu'}

SCÉNY:
{scenes_text}

Vraťte JSON analýzu ve formátu:
{{
    "total_scenes": {len(scenes)},
    "continuity_score": 0.0-1.0,
    "pacing_score": 0.0-1.0,
    "tension_curve": "popis dramatické křivky",
    "scene_types": {{"inciting": počet, "development": počet, ...}},
    "missing_elements": ["seznam chybějících elementů"],
    "recommendations": ["konkrétní doporučení"],
    "strengths": ["silné stránky"],
    "character_development": "hodnocení vývoje postav",
    "plot_coherence": "hodnocení soudržnosti děje"
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                
                # Ensure required fields
                defaults = {
                    "total_scenes": len(scenes),
                    "continuity_score": 0.75,
                    "pacing_score": 0.7,
                    "scene_types": {},
                    "missing_elements": [],
                    "recommendations": [],
                    "strengths": []
                }
                
                for key, default_value in defaults.items():
                    if key not in analysis:
                        analysis[key] = default_value
                
                return analysis
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            try:
                current_app.logger.error(f"Error in analyze_story_structure: {str(e)}")
            except RuntimeError:
                print(f"Error in analyze_story_structure: {str(e)}")
            return self._fallback_structure_analysis(scenes)
    
    def _fallback_structure_analysis(self, scenes: List[Scene]) -> Dict:
        """Fallback structure analysis"""
        scene_types = {}
        for scene in scenes:
            scene_type = scene.scene_type or 'development'
            scene_types[scene_type] = scene_types.get(scene_type, 0) + 1
        
        missing_elements = []
        if 'inciting' not in scene_types:
            missing_elements.append('inciting_incident')
        if 'climax' not in scene_types:
            missing_elements.append('climax')
        if 'resolution' not in scene_types:
            missing_elements.append('resolution')
        
        recommendations = []
        if len(scenes) < 5:
            recommendations.append('Zvažte přidání více scén pro plnější rozvoj příběhu')
        if scene_types.get('development', 0) < 2:
            recommendations.append('Přidejte více development scén pro budování napětí')
        
        return {
            "total_scenes": len(scenes),
            "continuity_score": 0.75,
            "pacing_score": 0.7,
            "scene_types": scene_types,
            "missing_elements": missing_elements,
            "recommendations": recommendations,
            "strengths": ["Základní struktura je na místě"]
        }
    
    def suggest_next_scenes(self, project_id: str, scenes: List[Scene], objects: List[StoryObject]) -> List[Dict]:
        """Suggest next scenes using Claude"""
        
        system_prompt = """Jste kreativní asistent pro tvorbu příběhů. Na základě existujících scén a objektů navrhněte nové scény, které logicky navazují a posouvají příběh vpřed.

Zaměřte se na:
- Logickou návaznost na existující scény
- Využití nevyužitých objektů
- Rozvoj konfliktů a napětí
- Charakterní vývoj
- Dramaturgickou správnost"""

        scenes_context = "\n".join([
            f"Scéna {i+1}: {scene.title} ({scene.scene_type})\n{scene.description}"
            for i, scene in enumerate(scenes)
        ])
        
        objects_context = "\n".join([
            f"- {obj.name} ({obj.object_type}): {obj.status} - {obj.description or 'bez popisu'}"
            for obj in objects
        ])

        prompt = f"""Na základě tohoto příběhu navrhněte 2-3 další scény:

EXISTUJÍCÍ SCÉNY:
{scenes_context}

DOSTUPNÉ OBJEKTY:
{objects_context}

Vraťte JSON seznam návrhů ve formátu:
[
    {{
        "title": "název scény",
        "description": "detailní popis co se děje",
        "scene_type": "inciting/development/rising_action/climax/resolution",
        "suggested_objects": ["objekty které se využijí"],
        "new_objects": ["nové objekty které se představí"],
        "character_focus": "na kterou postavu se zaměřuje",
        "conflict_development": "jak rozvíjí konflikt",
        "confidence": 0.0-1.0
    }}
]

Návrhů by mělo být 2-3, seřazené podle důležitosti."""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            
            # Extract JSON array
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                
                # Validate each suggestion
                for suggestion in suggestions:
                    if 'title' not in suggestion:
                        suggestion['title'] = 'Navržená scéna'
                    if 'description' not in suggestion:
                        suggestion['description'] = 'Popis scény'
                    if 'scene_type' not in suggestion:
                        suggestion['scene_type'] = 'development'
                    if 'confidence' not in suggestion:
                        suggestion['confidence'] = 0.8
                
                return suggestions[:3]  # Limit to 3 suggestions
            else:
                raise ValueError("No JSON array found in response")
                
        except Exception as e:
            try:
                current_app.logger.error(f"Error in suggest_next_scenes: {str(e)}")
            except RuntimeError:
                print(f"Error in suggest_next_scenes: {str(e)}")
            return self._fallback_scene_suggestions(objects)
    
    def _fallback_scene_suggestions(self, objects: List[StoryObject]) -> List[Dict]:
        """Fallback scene suggestions"""
        unused_objects = [obj for obj in objects if obj.status == 'unused']
        
        suggestions = []
        for obj in unused_objects[:2]:
            suggestions.append({
                'title': f'Scéna s objektem {obj.name}',
                'description': f'Scéna která rozvíjí roli objektu {obj.name} v příběhu.',
                'scene_type': 'development',
                'suggested_objects': [obj.name],
                'confidence': 0.7
            })
        
        if not suggestions:
            suggestions = [
                {
                    'title': 'Rozvoj postavy',
                    'description': 'Scéna zaměřená na charakterní vývoj hlavní postavy.',
                    'scene_type': 'development',
                    'suggested_objects': [],
                    'confidence': 0.75
                }
            ]
        
        return suggestions
    
    def generate_story_from_scenes(self, project: Project, scenes: List[Scene], objects: List[StoryObject]) -> Dict:
        """Generate complete story summary from scenes using Claude"""
        
        system_prompt = """Jste expert na literární analýzu a storytelling. Z poskytnutých scén vytvoříte koherentní souhrn příběhu s analýzou klíčových elementů.

Zaměřte se na:
- Hlavní téma a poselství
- Charakterní oblouky
- Klíčové konflikty
- Symboliku a motivy
- Celkovou strukturu"""

        scenes_text = "\n".join([
            f"Scéna {i+1} ({scene.scene_type}): {scene.title}\n{scene.description}"
            for i, scene in enumerate(scenes)
        ])
        
        objects_text = "\n".join([
            f"- {obj.name} ({obj.object_type}): {obj.description or 'klíčový prvek příběhu'}"
            for obj in objects
        ])

        prompt = f"""Vytvořte ucelený souhrn tohoto příběhu:

PROJEKT: {project.title}
ŽÁNR: {project.genre or 'neurčeno'}

SCÉNY:
{scenes_text}

KLÍČOVÉ OBJEKTY:
{objects_text}

Vraťte JSON ve formátu:
{{
    "title": "finální název",
    "premise": "premise v 1-2 větách",
    "theme": "hlavní téma",
    "protagonist": "hlavní postava a její oblouk",
    "antagonist": "antagonistické síly",
    "central_conflict": "ústřední konflikt",
    "story_arc": "popis příběhového oblouku",
    "key_symbols": ["symboly a motivy"],
    "tone": "tón příběhu",
    "target_audience": "cílová skupina",
    "estimated_length": "odhad délky v slovech",
    "marketability": "komerční potenciál",
    "unique_elements": ["unikátní prvky příběhu"]
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                story = json.loads(json_match.group())
                
                # Add computed statistics
                story['scene_count'] = len(scenes)
                story['object_count'] = len(objects)
                story['characters'] = list(set([
                    obj.name for obj in objects if obj.object_type == 'character'
                ]))
                
                return story
            else:
                raise ValueError("No JSON found in response")
                
        except Exception as e:
            try:
                current_app.logger.error(f"Error in generate_story_from_scenes: {str(e)}")
            except RuntimeError:
                print(f"Error in generate_story_from_scenes: {str(e)}")
            return self._fallback_story_generation(project, scenes, objects)
    
    def _fallback_story_generation(self, project: Project, scenes: List[Scene], objects: List[StoryObject]) -> Dict:
        """Fallback story generation"""
        characters = [obj.name for obj in objects if obj.object_type == 'character']
        
        return {
            "title": project.title,
            "premise": f"Příběh sleduje {characters[0] if characters else 'protagonistu'} skrze {len(scenes)} klíčových momentů.",
            "theme": "Hledání pravdy a osobní růst",
            "scene_count": len(scenes),
            "object_count": len(objects),
            "characters": characters,
            "estimated_length": len(scenes) * 2000,
            "tone": "mystery" if project.genre == "mystery" else "drama"
        }