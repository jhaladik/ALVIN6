# app/services/enhanced_ai_critics.py - Comprehensive AI Critics System
from typing import Dict, List, Optional
from flask import current_app
from app.services.claude_api import ClaudeAPIClient
from app.models import Scene, Project, StoryObject, Comment
import json
import re

class EnhancedAICritics:
    """Comprehensive AI Critics system with specialized experts"""
    
    def __init__(self):
        self.claude = ClaudeAPIClient()
        
        # Define all critics and their specializations
        self.critics = {
            'structure': {
                'name': 'Professor Syntax',
                'specialty': 'Story structure and pacing',
                'persona': 'Academic expert with 20 years in creative writing',
                'focus': ['Three-act structure', 'Dramatic tension', 'Scene transitions', 'Plot progression']
            },
            'character': {
                'name': 'Character Whisperer',
                'specialty': 'Character development and psychology',
                'persona': 'Behavioral psychologist turned writing coach',
                'focus': ['Character arcs', 'Motivation consistency', 'Dialogue authenticity', 'Relationships']
            },
            'dialog': {
                'name': 'Dialog Master',
                'specialty': 'Dialogue and voice',
                'persona': 'Former screenwriter and dialogue coach',
                'focus': ['Natural speech patterns', 'Character voice distinction', 'Subtext', 'Dialogue mechanics']
            },
            'pacing': {
                'name': 'Tempo Conductor',
                'specialty': 'Narrative pacing and rhythm',
                'persona': 'Editor with expertise in pacing and flow',
                'focus': ['Scene rhythm', 'Information flow', 'Tension building', 'Reader engagement']
            },
            'genre': {
                'name': 'Genre Guru',
                'specialty': 'Genre conventions and expectations',
                'persona': 'Genre fiction expert and publisher',
                'focus': ['Genre tropes', 'Reader expectations', 'Market fit', 'Genre-specific techniques']
            },
            'plot_holes': {
                'name': 'Logic Detective',
                'specialty': 'Plot consistency and logic',
                'persona': 'Forensic analyst turned story consultant',
                'focus': ['Plot consistency', 'Logical gaps', 'Continuity errors', 'Cause-effect chains']
            },
            'conflict': {
                'name': 'Conflict Architect',
                'specialty': 'Conflict escalation and resolution',
                'persona': 'Drama therapist and conflict resolution expert',
                'focus': ['Conflict types', 'Escalation patterns', 'Resolution satisfaction', 'Stakes progression']
            },
            'world_building': {
                'name': 'World Weaver',
                'specialty': 'Setting and world consistency',
                'persona': 'Anthropologist and fantasy world consultant',
                'focus': ['Setting consistency', 'Cultural logic', 'Environmental details', 'World rules']
            }
        }
    
    def get_all_critiques(self, project: Project, scenes: List[Scene], 
                         objects: List[StoryObject], focus_areas: List[str] = None) -> Dict:
        """Get comprehensive critique from all relevant critics"""
        
        if focus_areas is None:
            focus_areas = list(self.critics.keys())
        
        critiques = {}
        
        for critic_type in focus_areas:
            if critic_type in self.critics:
                try:
                    critique = self._get_critic_analysis(critic_type, project, scenes, objects)
                    critiques[critic_type] = critique
                except Exception as e:
                    self._safe_log(f"Error getting {critic_type} critique: {str(e)}", 'error')
                    critiques[critic_type] = self._fallback_critique(critic_type)
        
        # Generate summary and recommendations
        overall_summary = self._generate_overall_summary(critiques)
        
        return {
            'individual_critiques': critiques,
            'overall_summary': overall_summary,
            'priority_recommendations': self._extract_priority_recommendations(critiques),
            'score_breakdown': self._calculate_score_breakdown(critiques),
            'focus_areas_analyzed': focus_areas
        }
    
    def dialog_critique(self, project: Project, scenes: List[Scene], 
                       characters: List[StoryObject]) -> Dict:
        """Specialized dialogue analysis"""
        
        critic_info = self.critics['dialog']
        system_prompt = f"""Jste {critic_info['name']}, {critic_info['persona']}. 

Specializujete se na: {', '.join(critic_info['focus'])}

Analyzujte dialogy v příběhu a poskytněte konstruktivní kritiku zaměřenou na:
- Přirozenost řeči postav
- Rozlišitelnost hlasů jednotlivých postav  
- Podtext a skryté významy
- Efektivitu dialogu pro rozvoj děje
- Dialogové tagy a mechaniky

Hodnotíte na škále 1-5 a poskytujete konkrétní příklady."""

        # Extract dialogue from scenes
        dialogue_examples = []
        for scene in scenes:
            if scene.description and ('"' in scene.description or "'" in scene.description):
                dialogue_examples.append(f"Scéna '{scene.title}': {scene.description[:300]}")
        
        character_info = "\n".join([
            f"Postava: {char.name} - {char.description or 'bez popisu'}"
            for char in characters
        ])

        prompt = f"""Analyzujte dialogy v tomto příběhu:

PROJEKT: {project.title} ({project.genre})
POSTAVY:
{character_info}

PŘÍKLADY DIALOGŮ ZE SCÉN:
{chr(10).join(dialogue_examples) if dialogue_examples else 'Žádné explicitní dialogy nebyly nalezeny.'}

Vraťte JSON kritiku:
{{
    "critic_name": "{critic_info['name']}",
    "score": 1-5,
    "main_feedback": "hlavní zpětná vazba o dialozích",
    "voice_distinction": "hodnocení rozlišitelnosti hlasů postav",
    "natural_flow": "přirozenost a plynulost dialogů", 
    "subtext_analysis": "analýza podtextu a skrytých významů",
    "dialogue_examples": [
        {{
            "scene": "název scény",
            "example": "příklad dialogu",
            "feedback": "specifická zpětná vazba"
        }}
    ],
    "specific_recommendations": ["konkrétní doporučení pro zlepšení"],
    "strengths": ["silné stránky dialogů"],
    "areas_for_improvement": ["oblasti k zlepšení"]
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            return self._parse_critique_response(response, critic_info['name'], 3.5)
        except Exception as e:
            self._safe_log(f"Error in dialog_critique: {str(e)}", 'error')
            return self._fallback_critique('dialog')

    def pacing_critique(self, project: Project, scenes: List[Scene]) -> Dict:
        """Analyze narrative pacing and rhythm"""
        
        critic_info = self.critics['pacing']
        system_prompt = f"""Jste {critic_info['name']}, {critic_info['persona']}.

Analyzujete tempo a rytmus příběhu. Zaměřujte se na:
- Rychlost odhalování informací
- Střídání rychlých a pomalých scén
- Budování a uvolňování napětí
- Angažovanost čtenáře
- Optimální délku scén

Hodnotíte na škále 1-5."""

        # Analyze scene progression
        scene_analysis = []
        for i, scene in enumerate(scenes):
            intensity = scene.emotional_intensity or 0.5
            word_estimate = len(scene.description.split()) * 4 if scene.description else 100
            
            scene_analysis.append(
                f"Scéna {i+1}: '{scene.title}' ({scene.scene_type})\n"
                f"  Intenzita: {intensity}/1.0\n"
                f"  Odhad délky: ~{word_estimate} slov\n"
                f"  Konflikt: {scene.conflict or 'neurčeno'}"
            )

        prompt = f"""Analyzujte tempo tohoto příběhu:

PROJEKT: {project.title}
CELKEM SCÉN: {len(scenes)}

DETAILNÍ ANALÝZA SCÉN:
{chr(10).join(scene_analysis)}

Vraťte JSON kritiku:
{{
    "critic_name": "{critic_info['name']}",
    "score": 1-5,
    "main_feedback": "hlavní zpětná vazba o tempu",
    "pacing_rhythm": "analýza rytmu příběhu",
    "tension_curve": "hodnocení křivky napětí",
    "scene_transitions": "kvalita přechodů mezi scénami",
    "information_flow": "tok informací pro čtenáře",
    "slow_spots": ["identifikované pomalé úseky"],
    "rushed_areas": ["příliš rychlé části"],
    "pacing_recommendations": ["doporučení pro zlepšení tempa"],
    "optimal_scene_adjustments": [
        {{
            "scene": "název scény",
            "current_pace": "současné tempo",
            "suggested_change": "navržená změna"
        }}
    ]
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            return self._parse_critique_response(response, critic_info['name'], 3.8)
        except Exception as e:
            self._safe_log(f"Error in pacing_critique: {str(e)}", 'error')
            return self._fallback_critique('pacing')

    def genre_expert_critique(self, project: Project, scenes: List[Scene]) -> Dict:
        """Genre-specific analysis and recommendations"""
        
        critic_info = self.critics['genre']
        genre = project.genre or 'general'
        
        # Genre-specific expectations and tropes
        genre_guidelines = {
            'mystery': ['Red herrings', 'Clue placement', 'Detective progression', 'Resolution satisfaction'],
            'romance': ['Character chemistry', 'Relationship progression', 'Emotional beats', 'Satisfying conclusion'],
            'sci-fi': ['Scientific plausibility', 'Technology consistency', 'World-building logic', 'Social implications'],
            'fantasy': ['Magic system consistency', 'World rules', 'Mythology coherence', 'Character powers'],
            'thriller': ['Suspense building', 'Stakes escalation', 'Plot twists', 'Pace maintenance'],
            'horror': ['Atmosphere building', 'Fear escalation', 'Supernatural rules', 'Character vulnerability'],
            'drama': ['Emotional authenticity', 'Character depth', 'Realistic conflicts', 'Human truth']
        }
        
        system_prompt = f"""Jste {critic_info['name']}, expert na žánr {genre}.

Analyzujete dodržování žánrových konvencí a očekávání čtenářů. Pro žánr {genre} se zaměřujte na:
{', '.join(genre_guidelines.get(genre, ['General storytelling principles']))}

Poskytněte analýzu z pohledu žánrové vhodnosti a komerčního potenciálu."""

        scenes_context = "\n".join([
            f"Scéna {i+1}: {scene.title} ({scene.scene_type})\n{scene.description[:200]}"
            for i, scene in enumerate(scenes)
        ])

        prompt = f"""Analyzujte tento příběh z pohledu žánru {genre}:

PROJEKT: {project.title}
ŽÁNR: {genre}
POPIS: {project.description or 'bez popisu'}

SCÉNY:
{scenes_context}

Vraťte JSON kritiku:
{{
    "critic_name": "{critic_info['name']}",
    "score": 1-5,
    "genre": "{genre}",
    "main_feedback": "hlavní zpětná vazba o žánrové vhodnosti",
    "genre_adherence": "dodržování žánrových konvencí",
    "reader_expectations": "splnění očekávání čtenářů",
    "market_potential": "komerční potenciál v žánru",
    "genre_specific_elements": [
        {{
            "element": "žánrový prvek",
            "present": true/false,
            "effectiveness": "hodnocení efektivity",
            "recommendation": "doporučení"
        }}
    ],
    "missing_genre_elements": ["chybějící žánrové prvky"],
    "genre_innovation": "inovativní prvky v rámci žánru",
    "competitive_analysis": "porovnání s podobnými díly v žánru"
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2000)
            return self._parse_critique_response(response, critic_info['name'], 4.0)
        except Exception as e:
            self._safe_log(f"Error in genre_expert_critique: {str(e)}", 'error')
            return self._fallback_critique('genre')

    def plot_hole_detection(self, project: Project, scenes: List[Scene], 
                           objects: List[StoryObject]) -> Dict:
        """Detect logical inconsistencies and plot holes"""
        
        critic_info = self.critics['plot_holes']
        system_prompt = f"""Jste {critic_info['name']}, {critic_info['persona']}.

Analyzujete logickou konzistenci příběhu a hledáte:
- Logické nesrovnalosti
- Kontinuitní chyby
- Nevyřešené problémy
- Nerealistické prvky
- Porušení vlastních pravidel příběhu

Buďte pečliví a systematičtí jako forenzní analytik."""

        # Build timeline and object usage
        timeline = []
        object_usage = {}
        
        for i, scene in enumerate(scenes):
            timeline.append(f"Bod {i+1}: {scene.title} - {scene.description}")
            
            for scene_obj in scene.scene_objects:
                obj_name = scene_obj.story_object.name
                if obj_name not in object_usage:
                    object_usage[obj_name] = []
                object_usage[obj_name].append(f"Scéna {i+1}: {scene.title}")

        prompt = f"""Analyzujte logickou konzistenci tohoto příběhu:

PROJEKT: {project.title}
ŽÁNR: {project.genre or 'neurčeno'}

CHRONOLOGICKÁ POSLOUPNOST:
{chr(10).join(timeline)}

OBJEKTY A JEJICH POUŽITÍ:
{chr(10).join([f"{obj}: {', '.join(usage)}" for obj, usage in object_usage.items()])}

Vraťte JSON analýzu:
{{
    "critic_name": "{critic_info['name']}",
    "score": 1-5,
    "main_feedback": "hlavní zpětná vazba o logické konzistenci",
    "plot_holes": [
        {{
            "type": "typ problému",
            "description": "popis problému",
            "scenes_affected": ["dotčené scény"],
            "severity": "nízká/střední/vysoká",
            "suggested_fix": "navržené řešení"
        }}
    ],
    "continuity_issues": [
        {{
            "issue": "popis problému kontinuity",
            "location": "kde se vyskytuje",
            "fix": "navržené řešení"
        }}
    ],
    "logical_gaps": ["identifikované logické mezery"],
    "character_behavior_issues": ["problémy s chováním postav"],
    "world_rule_violations": ["porušení pravidel světa"],
    "overall_consistency": "celkové hodnocení konzistence"
}}"""

        try:
            response = self.claude._make_request(prompt, system_prompt, max_tokens=2500)
            return self._parse_critique_response(response, critic_info['name'], 4.2)
        except Exception as e:
            self._safe_log(f"Error in plot_hole_detection: {str(e)}", 'error')
            return self._fallback_critique('plot_holes')

    def _get_critic_analysis(self, critic_type: str, project: Project, 
                           scenes: List[Scene], objects: List[StoryObject]) -> Dict:
        """Route to appropriate critic analysis"""
        
        if critic_type == 'dialog':
            characters = [obj for obj in objects if obj.object_type == 'character']
            return self.dialog_critique(project, scenes, characters)
        elif critic_type == 'pacing':
            return self.pacing_critique(project, scenes)
        elif critic_type == 'genre':
            return self.genre_expert_critique(project, scenes)
        elif critic_type == 'plot_holes':
            return self.plot_hole_detection(project, scenes, objects)
        elif critic_type == 'structure':
            return self.structure_critique(project, scenes)
        elif critic_type == 'character':
            characters = [obj for obj in objects if obj.object_type == 'character']
            return self.character_critique(project, scenes, characters)
        else:
            return self._fallback_critique(critic_type)

    def _generate_overall_summary(self, critiques: Dict) -> Dict:
        """Generate overall summary from all critiques"""
        
        total_score = 0
        critic_count = 0
        all_recommendations = []
        major_issues = []
        strengths = []
        
        for critic_type, critique in critiques.items():
            if 'score' in critique:
                total_score += critique['score']
                critic_count += 1
            
            if 'specific_recommendations' in critique:
                all_recommendations.extend(critique['specific_recommendations'])
            if 'recommendations' in critique:
                all_recommendations.extend(critique['recommendations'])
            
            if 'plot_holes' in critique and critique['plot_holes']:
                major_issues.extend([ph['description'] for ph in critique['plot_holes']])
            
            if 'strengths' in critique:
                strengths.extend(critique['strengths'])
        
        average_score = total_score / critic_count if critic_count > 0 else 3.0
        
        return {
            'overall_score': round(average_score, 2),
            'total_critics': critic_count,
            'top_recommendations': all_recommendations[:5],  # Top 5 recommendations
            'major_issues': major_issues[:3],  # Top 3 issues
            'key_strengths': strengths[:3],  # Top 3 strengths
            'overall_assessment': self._get_assessment_text(average_score)
        }

    def _get_assessment_text(self, score: float) -> str:
        """Get text assessment based on score"""
        if score >= 4.5:
            return "Vynikající práce! Příběh je velmi dobře zpracovaný."
        elif score >= 4.0:
            return "Dobrá práce s několika oblastmi pro zlepšení."
        elif score >= 3.5:
            return "Solidní základ s potřebou dalšího rozvoje."
        elif score >= 3.0:
            return "Slušný začátek, ale vyžaduje významné úpravy."
        else:
            return "Příběh potřebuje zásadní přepracování."

    def _extract_priority_recommendations(self, critiques: Dict) -> List[Dict]:
        """Extract and prioritize recommendations"""
        
        priority_map = {
            'plot_holes': 1,  # Highest priority
            'structure': 2,
            'character': 3,
            'pacing': 4,
            'dialog': 5,
            'genre': 6
        }
        
        all_recommendations = []
        
        for critic_type, critique in critiques.items():
            priority = priority_map.get(critic_type, 7)
            score = critique.get('score', 3.0)
            
            # Get recommendations from various fields
            recommendations = []
            if 'specific_recommendations' in critique:
                recommendations.extend(critique['specific_recommendations'])
            if 'recommendations' in critique:
                recommendations.extend(critique['recommendations'])
            
            for rec in recommendations:
                all_recommendations.append({
                    'recommendation': rec,
                    'critic': critique.get('critic_name', critic_type),
                    'priority': priority,
                    'urgency': 'high' if score < 3.0 else 'medium' if score < 4.0 else 'low'
                })
        
        # Sort by priority and urgency
        return sorted(all_recommendations, key=lambda x: (x['priority'], x['urgency'] == 'low'))[:10]

    def _calculate_score_breakdown(self, critiques: Dict) -> Dict:
        """Calculate detailed score breakdown"""
        
        scores = {}
        for critic_type, critique in critiques.items():
            if 'score' in critique:
                scores[critic_type] = {
                    'score': critique['score'],
                    'critic': critique.get('critic_name', critic_type),
                    'weight': 1.0  # Could be adjusted based on critic importance
                }
        
        return scores

    def _safe_log(self, message: str, level: str = 'error'):
        """Safe logging for Flask context"""
        try:
            getattr(current_app.logger, level)(message)
        except RuntimeError:
            print(f"[{level.upper()}] {message}")

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
            self._safe_log(f"Error parsing critique response: {str(e)}", 'error')
        
        return self._fallback_critique_for_critic(critic_name, fallback_score)

    def _fallback_critique(self, critic_type: str) -> Dict:
        """Fallback critique when AI fails"""
        critic_info = self.critics.get(critic_type, {'name': 'AI Critic'})
        return self._fallback_critique_for_critic(critic_info['name'], 3.5)

    def _fallback_critique_for_critic(self, critic_name: str, score: float) -> Dict:
        """Generate fallback critique"""
        return {
            'critic_name': critic_name,
            'score': score,
            'main_feedback': 'Analýza byla dokončena. Pokračujte v práci na příběhu.',
            'recommendations': ['Pokračujte v rozvoji příběhu'],
            'strengths': ['Základní struktura je rozpoznatelná'],
            'areas_for_improvement': ['Obecné zlepšení kvality']
        }

    # Keep original methods for backwards compatibility
    def structure_critique(self, project: Project, scenes: List[Scene]) -> Dict:
        return self._get_critic_analysis('structure', project, scenes, [])
    
    def character_critique(self, project: Project, scenes: List[Scene], characters: List[StoryObject]) -> Dict:
        return self._get_critic_analysis('character', project, scenes, characters)