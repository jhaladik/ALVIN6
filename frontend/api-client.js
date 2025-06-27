class StoryForgeAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.sessionToken = null;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            credentials: 'include', // Important for session cookies
            ...options,
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Authentication
    async login(email, password) {
        const result = await this.request('/auth/login', {
            method: 'POST',
            body: { email, password }
        });
        return result;
    }

    async register(username, email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: { username, email, password }
        });
    }

    async logout() {
        return this.request('/auth/logout', { method: 'POST' });
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    // Projects
    async getProjects() {
        return this.request('/projects');
    }

    async createProject(projectData) {
        return this.request('/projects', {
            method: 'POST',
            body: projectData
        });
    }

    async getProject(projectId) {
        return this.request(`/projects/${projectId}`);
    }

    // Scenes
    async createScene(sceneData) {
        return this.request('/scenes', {
            method: 'POST',
            body: sceneData
        });
    }

    async updateScene(sceneId, sceneData) {
        return this.request(`/scenes/${sceneId}`, {
            method: 'PUT',
            body: sceneData
        });
    }

    async deleteScene(sceneId) {
        return this.request(`/scenes/${sceneId}`, {
            method: 'DELETE'
        });
    }

    // AI Analysis
    async analyzeStructure(projectId) {
        return this.request(`/ai/projects/${projectId}/analyze-structure`, {
            method: 'POST'
        });
    }

    async suggestScenes(projectId) {
        return this.request(`/ai/projects/${projectId}/suggest-scenes`, {
            method: 'POST'
        });
    }
}

// Export pro použití v HTML
window.StoryForgeAPI = StoryForgeAPI;
