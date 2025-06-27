# tests/integration/test_workflows.py - Integration Tests
class TestCompleteWorkflow:
    """Test complete user workflows"""
    
    def test_idea_to_project_workflow(self, client, authenticated_user):
        """Test complete workflow from idea to project"""
        # 1. Analyze idea
        idea_response = client.post('/api/ai/analyze-idea', json={
            'idea_text': 'A young woman discovers her grandmother\'s secret diary',
            'story_intent': 'mystery'
        })
        
        assert idea_response.status_code == 200
        idea_data = idea_response.get_json()
        assert idea_data['success'] is True
        
        # 2. Create project from idea
        project_response = client.post('/api/ai/create-project-from-idea', json={
            'project_title': 'Grandmother\'s Secret',
            'project_description': 'A mystery about family secrets',
            'project_genre': 'mystery',
            'extracted_objects': idea_data['analysis']['extracted_objects'],
            'first_scene': idea_data['analysis']['first_scene_suggestion']
        })
        
        assert project_response.status_code == 200
        project_data = project_response.get_json()
        assert project_data['success'] is True
        
        project_id = project_data['project']['id']
        
        # 3. Add additional scene
        scene_response = client.post('/api/scenes', json={
            'title': 'Discovery Scene',
            'description': 'The protagonist finds the diary',
            'project_id': project_id,
            'scene_type': 'development'
        })
        
        assert scene_response.status_code == 200
        
        # 4. Analyze structure
        structure_response = client.post(f'/api/ai/projects/{project_id}/analyze-structure')
        
        assert structure_response.status_code == 200
        structure_data = structure_response.get_json()
        assert 'analysis' in structure_data