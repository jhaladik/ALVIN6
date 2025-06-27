# API_DOCUMENTATION.md

# StoryForge AI - API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
Most endpoints require authentication. Login returns a session cookie that should be included in subsequent requests.

### POST /auth/login
Login user and start session.

**Request:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        "plan": "pro",
        "tokens_used": 150,
        "tokens_limit": 10000
    }
}
```

### POST /auth/register
Register new user.

**Request:**
```json
{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "password123"
}
```

### POST /auth/logout
Logout current user.

## Projects

### GET /projects
Get all projects for authenticated user.

**Response:**
```json
[
    {
        "id": "uuid-here",
        "title": "My Story",
        "description": "A fascinating tale",
        "genre": "mystery",
        "current_phase": "expand",
        "word_count": 12000,
        "scene_count": 5,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-02T00:00:00"
    }
]
```

### POST /projects
Create new project.

**Request:**
```json
{
    "title": "New Story",
    "description": "Description here",
    "genre": "thriller"
}
```

### GET /projects/{project_id}
Get detailed project data including scenes and objects.

**Response:**
```json
{
    "project": {
        "id": "uuid-here",
        "title": "My Story",
        "description": "A fascinating tale",
        "genre": "mystery",
        "current_phase": "expand",
        "word_count": 12000
    },
    "scenes": [
        {
            "id": 1,
            "title": "Opening Scene",
            "description": "Scene description",
            "scene_type": "inciting",
            "order_index": 1,
            "emotional_intensity": 0.7,
            "location": "Library",
            "conflict": "Discovery of secret",
            "dialog_count": 5,
            "word_count": 800,
            "objects": [
                {
                    "id": 1,
                    "name": "Mysterious Letter",
                    "type": "prop",
                    "role": "central",
                    "transformation": "Is decoded"
                }
            ]
        }
    ],
    "objects": [
        {
            "id": 1,
            "name": "Mysterious Letter",
            "type": "prop",
            "description": "An encrypted message",
            "importance": "high",
            "status": "active",
            "scene_count": 3
        }
    ]
}
```

## Scenes

### POST /projects/{project_id}/scenes
Create new scene with AI object extraction.

**Request:**
```json
{
    "title": "New Scene",
    "description": "Sarah discovers a letter in the attic...",
    "scene_type": "development",
    "location": "Attic",
    "conflict": "Family secret revealed"
}
```

**Cost:** 5 tokens

### PUT /scenes/{scene_id}
Update existing scene.

### DELETE /scenes/{scene_id}
Delete scene.

## AI Analysis

### POST /projects/{project_id}/ai/analyze-structure
Analyze story structure and provide feedback.

**Cost:** 15 tokens

**Response:**
```json
{
    "success": true,
    "analysis": {
        "total_scenes": 5,
        "scene_types": {
            "inciting": 1,
            "development": 3,
            "climax": 1
        },
        "continuity_score": 0.85,
        "pacing_score": 0.72,
        "missing_elements": ["resolution"],
        "recommendations": [
            "Consider adding more development scenes",
            "Add resolution scene"
        ]
    },
    "feedback_id": 123
}
```

### POST /projects/{project_id}/ai/suggest-scenes
Get AI suggestions for next scenes based on unused objects.

**Cost:** 10 tokens

**Response:**
```json
{
    "success": true,
    "suggestions": [
        {
            "title": "Scene exploring Mysterious Letter",
            "description": "A scene that develops the role of Mysterious Letter in the story.",
            "suggested_objects": ["Mysterious Letter"],
            "scene_type": "development",
            "confidence": 0.85
        }
    ]
}
```

### POST /projects/{project_id}/ai/generate-story
Generate complete story from scenes.

**Cost:** 25 tokens

**Response:**
```json
{
    "success": true,
    "story": {
        "title": "My Story",
        "premise": "A story following Sarah through 5 key moments.",
        "theme": "Discovery and transformation",
        "characters": [
            {"name": "Sarah", "role": "protagonist"}
        ],
        "settings": ["Library", "Attic"],
        "conflicts": ["Family secret"],
        "structure": {
            "setup": [...],
            "development": [...],
            "climax": [...],
            "resolution": [...]
        },
        "estimated_word_count": 15000,
        "quality_score": 0.85
    }
}
```

## Objects

### POST /projects/{project_id}/objects
Create custom story object.

**Request:**
```json
{
    "name": "Magic Sword",
    "type": "prop",
    "description": "An ancient weapon",
    "importance": "high",
    "status": "active",
    "attributes": {
        "magical": true,
        "origin": "ancient"
    }
}
```

## Collaboration

### POST /projects/{project_id}/collaborate
Invite collaborator to project.

**Request:**
```json
{
    "email": "collaborator@example.com",
    "role": "editor",
    "permissions": {
        "can_edit_scenes": true,
        "can_delete_scenes": false,
        "can_invite_others": false
    }
}
```

## WebSocket Events

Connect to `/` namespace for real-time collaboration.

### Events to Send:
- `join_project` - Join project room
- `leave_project` - Leave project room
- `scene_update` - Notify others of scene changes
- `cursor_move` - Share cursor position

### Events to Listen:
- `user_joined` - Someone joined the project
- `user_left` - Someone left the project
- `scene_updated` - Scene was updated by another user
- `cursor_moved` - Another user's cursor moved

## Error Responses

All endpoints may return these error responses:

**401 Unauthorized:**
```json
{
    "error": "Authentication required"
}
```

**402 Payment Required:**
```json
{
    "error": "Insufficient tokens"
}
```

**403 Forbidden:**
```json
{
    "error": "Access denied"
}
```

**404 Not Found:**
```json
{
    "error": "Resource not found"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Server error"
}
```