class StoryForgeAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.isOnline = false;
        this.retryCount = 0;
        this.maxRetries = 3;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            credentials: 'include',
            timeout: 10000,
            ...options,
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000);
                
                const response = await fetch(url, { ...config, signal: controller.signal });
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || `HTTP ${response.status}`);
                }

                const data = await response.json();
                this.isOnline = true;
                if(window.ui && typeof window.ui.updateConnectionStatus === 'function') {
                    window.ui.updateConnectionStatus(true);
                }
                return data;

            } catch (error) {
                console.error(`API Request failed (attempt ${attempt + 1}):`, error);
                if (attempt === this.maxRetries) {
                    this.isOnline = false;
                    if(window.ui && typeof window.ui.updateConnectionStatus === 'function') {
                        window.ui.updateConnectionStatus(false);
                    }
                    if (error.name === 'AbortError') throw new Error('Požadavek vypršel.');
                    if (error.message.includes('Failed to fetch')) throw new Error('Server není dostupný.');
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
            }
        }
    }

    async healthCheck() {
        try {
            const response = await fetch('/health', { method: 'GET', credentials: 'include' });
            return response.ok;
        } catch (error) {
            console.warn('Health check failed:', error.message);
            return false;
        }
    }

    // Auth methods
    async login(email, password) { return this.request('/auth/login', { method: 'POST', body: { email, password } }); }
    async logout() { return this.request('/auth/logout', { method: 'POST' }); }
    async getCurrentUser() { return this.request('/auth/me'); }

    // Project methods
    async getProjects() { return this.request('/projects'); }
    async createProject(data) { return this.request('/projects', { method: 'POST', body: data }); }
    async getProject(id) { return this.request(`/projects/${id}`); }

    // Scene methods
    async createScene(data) { return this.request('/scenes', { method: 'POST', body: data }); }
    async updateScene(id, data) { return this.request(`/scenes/${id}`, { method: 'PUT', body: data }); }
    async deleteScene(id) { return this.request(`/scenes/${id}`, { method: 'DELETE' }); }

    // AI methods
    async analyzeIdea(ideaText, storyIntent) { return this.request('/ai/analyze-idea', { method: 'POST', body: { idea_text: ideaText, story_intent: storyIntent } }); }
    async createProjectFromIdea(data) { return this.request('/ai/create-project-from-idea', { method: 'POST', body: data }); }
    async analyzeStructure(id) { return this.request(`/ai/projects/${id}/analyze-structure`, { method: 'POST' }); }
    async suggestScenes(id) { return this.request(`/ai/projects/${id}/suggest-scenes`, { method: 'POST' }); }
}