const ui = {
    // DOM Element References
    connectionBanner: document.getElementById('connection-banner'),
    connectionIndicator: document.getElementById('connection-indicator'),
    loginModal: document.getElementById('login-modal'),
    serverHelpModal: document.getElementById('server-help-modal'),
    loadingOverlay: document.getElementById('loading-overlay'),
    loadingMessage: document.getElementById('loading-message'),
    toastContainer: document.getElementById('toast-container'),
    tokenMeter: document.getElementById('token-meter'),
    tokenCount: document.getElementById('token-count'),
    userInfo: document.getElementById('user-info'),
    mainAppContainer: document.getElementById('main-app-container'),

    // UI State Management
    updateConnectionStatus(isOnline) {
        if (isOnline) {
            this.connectionIndicator.textContent = '🟢 Online';
            this.connectionIndicator.className = 'text-green-100';
            this.connectionBanner.classList.add('hidden');
        } else {
            this.connectionIndicator.textContent = '🔴 Offline';
            this.connectionIndicator.className = 'text-red-100';
            this.connectionBanner.classList.remove('hidden');
        }
    },

    setLoginState(isAuthenticated, user = null) {
        this.loginModal.classList.toggle('hidden', isAuthenticated);
        this.mainAppContainer.style.display = isAuthenticated ? 'block' : 'none';
        
        const elementsToToggle = ['token-display', 'user-display', 'logout-button'];
        elementsToToggle.forEach(id => {
            const el = document.getElementById(id);
            if(el) el.style.display = isAuthenticated ? 'block' : 'none';
        });

        if (isAuthenticated && user) {
            this.userInfo.textContent = `${user.username} (${user.plan})`;
            this.updateTokenDisplay(user);
        }
    },

    showLoading(message = 'Načítám...') {
        this.loadingMessage.textContent = message;
        this.loadingOverlay.classList.remove('hidden');
    },

    hideLoading() {
        this.loadingOverlay.classList.add('hidden');
    },

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            warning: 'bg-yellow-500'
        }[type] || 'bg-blue-500';
        
        toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full`;
        toast.textContent = message;
        
        this.toastContainer.appendChild(toast);
        
        setTimeout(() => toast.classList.remove('translate-x-full'), 100);
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    updateTokenDisplay(user) {
        if (!user) return;
        const percentage = (user.tokens_used / user.tokens_limit) * 100;
        this.tokenMeter.style.width = `${percentage}%`;
        this.tokenCount.textContent = `${(user.tokens_used / 1000).toFixed(1)}k/${(user.tokens_limit / 1000).toFixed(0)}k`;

        let meterClass = 'bg-green-400';
        if (percentage > 90) meterClass = 'bg-red-400';
        else if (percentage > 75) meterClass = 'bg-yellow-400';
        this.tokenMeter.className = `h-full ${meterClass} transition-all`;
    },

    setPhase(phase) {
        document.querySelectorAll('.workflow-phase').forEach(el => el.classList.remove('active'));
        document.getElementById(`phase-${phase}`)?.classList.add('active');
        
        document.getElementById('idea-phase-content').classList.toggle('hidden', phase !== 'idea');
        document.getElementById('expand-phase-content').classList.toggle('hidden', phase !== 'expand');
        
        this.showToast(`Přepnuto na fázi: ${phase}`, 'info');
    },

    displayIdeaAnalysis(analysis) {
        const container = document.getElementById('idea-analysis-results');
        if (!container) return;
        
        container.innerHTML = `
            <div class="idea-analysis bg-white rounded-2xl shadow-lg p-6">
                <h3 class="text-xl font-bold mb-6 flex items-center gap-2">🧠 AI Analýza vašeho nápadu</h3>
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="space-y-4">
                        <div class="bg-blue-50 p-4 rounded-lg">
                            <h4 class="font-medium text-blue-800 mb-2">📊 Hodnocení</h4>
                            <div><strong>Žánr:</strong> ${analysis.story_assessment.genre}</div>
                            <div><strong>Tón:</strong> ${analysis.story_assessment.tone}</div>
                        </div>
                        <div class="bg-green-50 p-4 rounded-lg">
                            <h4 class="font-medium text-green-800 mb-2">🎯 Témata</h4>
                            <div class="flex flex-wrap gap-2">${analysis.story_assessment.themes.map(t => `<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">${t}</span>`).join('')}</div>
                        </div>
                    </div>
                    <div class="bg-yellow-50 p-4 rounded-lg">
                        <h4 class="font-medium text-yellow-800 mb-2">🔧 Objekty</h4>
                        ${Object.entries(analysis.extracted_objects).map(([type, items]) => `<div><strong class="text-xs uppercase">${type}:</strong><div class="flex flex-wrap gap-1 mt-1">${items.map(i => `<span class="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">${i}</span>`).join('')}</div></div>`).join('')}
                    </div>
                </div>
                <div class="mt-6 bg-purple-50 p-4 rounded-lg">
                    <h4 class="font-medium text-purple-800 mb-3">🎬 Navržená první scéna</h4>
                    <div class="bg-white p-4 rounded border-l-4 border-purple-500">
                        <h5 class="font-medium mb-2">${analysis.first_scene_suggestion.title}</h5>
                        <p class="text-sm text-gray-600">${analysis.first_scene_suggestion.description}</p>
                    </div>
                </div>
            </div>`;
        container.classList.remove('hidden');
    },

    prepareProjectCreation(analysis) {
        document.getElementById('project-title-input').value = analysis.project_suggestions.title;
        document.getElementById('project-description-input').value = analysis.project_suggestions.description;
        document.getElementById('project-genre-input').value = analysis.story_assessment.genre.toLowerCase();
        
        const totalObjects = Object.values(analysis.extracted_objects).reduce((sum, arr) => sum + arr.length, 0);
        document.getElementById('objects-to-create').textContent = totalObjects;
        
        document.getElementById('create-project-section').classList.remove('hidden');
    },

    updateCharCount() {
        const ideaText = document.getElementById('idea-text');
        const charCount = document.getElementById('idea-char-count');
        charCount.textContent = ideaText.value.length;
    },
    
    showServerHelp() {
        this.serverHelpModal.classList.remove('hidden');
    },

    hideServerHelp() {
        this.serverHelpModal.classList.add('hidden');
    }
};