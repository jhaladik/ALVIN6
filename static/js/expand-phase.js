// static/js/expand-phase.js - Scene Management for Expand Phase
class ExpandPhaseManager {
    constructor() {
        this.currentProject = null;
        this.scenes = [];
        this.objects = [];
        this.currentScene = null;
        this.viewMode = 'timeline';
        this.isCollaborationEnabled = false;
        this.presenceUsers = [];
        
        this.setupEventListeners();
        this.initializeCollaboration();
    }
    
    setupEventListeners() {
        // Scene description input handlers
        document.addEventListener('input', (e) => {
            if (e.target && e.target.id === 'scene-description-input') {
                this.updateWordCount();
                this.debouncedAutoSave();
            }
        });
        
        // Intensity slider
        document.addEventListener('input', (e) => {
            if (e.target && e.target.id === 'intensity-slider') {
                const value = e.target.value;
                const valueEl = document.getElementById('intensity-value');
                if (valueEl) valueEl.textContent = value;
                this.updateIntensityIndicator(parseFloat(value));
            }
        });
        
        // Set up debounced autosave
        this.debouncedAutoSave = this.debounce(this.autoSaveScene.bind(this), 2000);
    }
    
    async loadProjectData(projectId) {
        try {
            ui.showLoading('Načítám data projektu...');
            
            const response = await state.api.getProject(projectId);
            this.currentProject = response.project;
            this.scenes = response.scenes || [];
            this.objects = response.objects || [];
            
            this.renderScenes();
            this.updateStats();
            this.loadCollaborators();
            
            ui.hideLoading();
            ui.showToast('Projekt načten', 'success');
            
        } catch (error) {
            ui.hideLoading();
            ui.showToast('Chyba při načítání projektu: ' + error.message, 'error');
        }
    }
    
    renderScenes() {
        this.renderTimelineView();
        this.renderKanbanView();
        this.updateViewMode();
    }
    
    renderTimelineView() {
        const timeline = document.getElementById('scene-timeline');
        const noScenesMsg = document.getElementById('no-scenes-message');
        
        if (!timeline || !noScenesMsg) {
            console.warn('Timeline elements not found in DOM');
            return;
        }
        
        if (this.scenes.length === 0) {
            timeline.innerHTML = '';
            noScenesMsg.classList.remove('hidden');
            return;
        }
        
        noScenesMsg.classList.add('hidden');
        
        timeline.innerHTML = this.scenes.map((scene, index) => `
            <div class="scene-node bg-white rounded-lg shadow-md p-4 border-l-4 ${this.getSceneTypeColor(scene.scene_type)}" 
                 data-scene-id="${scene.id}" onclick="expandManager.selectScene(${scene.id})">
                <div class="flex items-center justify-between mb-2">
                    <div class="text-sm text-gray-500">#${index + 1}</div>
                    <div class="text-xs px-2 py-1 rounded-full ${this.getSceneTypeBadge(scene.scene_type)}">
                        ${this.getSceneTypeLabel(scene.scene_type)}
                    </div>
                </div>
                
                <h4 class="font-semibold text-gray-800 mb-2 line-clamp-2">${scene.title}</h4>
                
                <p class="text-sm text-gray-600 mb-3 line-clamp-3">${scene.description || 'Bez popisu'}</p>
                
                <div class="space-y-2">
                    <div class="intensity-indicator ${this.getIntensityClass(scene.emotional_intensity)}" 
                         style="width: ${(scene.emotional_intensity || 0.5) * 100}%"></div>
                    
                    <div class="flex items-center justify-between text-xs text-gray-500">
                        <span>${scene.location || 'Bez lokace'}</span>
                        <span>${scene.word_count || 0} slov</span>
                    </div>
                    
                    ${scene.objects && scene.objects.length > 0 ? `
                        <div class="flex flex-wrap gap-1">
                            ${scene.objects.slice(0, 3).map(obj => `
                                <span class="text-xs px-2 py-1 bg-gray-100 rounded-full">${obj.name}</span>
                            `).join('')}
                            ${scene.objects.length > 3 ? `<span class="text-xs text-gray-500">+${scene.objects.length - 3}</span>` : ''}
                        </div>
                    ` : ''}
                </div>
                
                <!-- Collaboration indicators -->
                <div class="mt-2 flex items-center justify-between">
                    <div class="flex items-center space-x-1" id="scene-${scene.id}-presence">
                        <!-- Presence indicators will be added here -->
                    </div>
                    <div class="flex space-x-1">
                        <button onclick="event.stopPropagation(); expandManager.editScene(${scene.id})" 
                                class="text-blue-500 hover:text-blue-700 text-xs">✏️</button>
                        <button onclick="event.stopPropagation(); expandManager.deleteScene(${scene.id})" 
                                class="text-red-500 hover:text-red-700 text-xs">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    renderKanbanView() {
        const sceneTypes = ['opening', 'inciting', 'development', 'rising_action', 'climax', 'falling_action', 'resolution'];
        const typeMapping = {
            'opening': 'setup',
            'inciting': 'setup', 
            'development': 'development',
            'rising_action': 'development',
            'climax': 'climax',
            'falling_action': 'resolution',
            'resolution': 'resolution'
        };
        
        // Group scenes by type
        const groupedScenes = {
            setup: [],
            development: [],
            climax: [],
            resolution: []
        };
        
        this.scenes.forEach(scene => {
            const group = typeMapping[scene.scene_type] || 'development';
            groupedScenes[group].push(scene);
        });
        
        // Render each column
        Object.keys(groupedScenes).forEach(columnType => {
            const column = document.getElementById(`${columnType}-scenes`);
            const counter = document.getElementById(`${columnType}-count`);
            
            if (column && counter) {
                counter.textContent = `(${groupedScenes[columnType].length})`;
                
                column.innerHTML = groupedScenes[columnType].map(scene => `
                    <div class="kanban-scene bg-white rounded-lg shadow-sm p-3 border-l-4 ${this.getSceneTypeColor(scene.scene_type)} cursor-pointer"
                         data-scene-id="${scene.id}" onclick="expandManager.selectScene(${scene.id})">
                        <h5 class="font-medium text-gray-800 mb-1 text-sm">${scene.title}</h5>
                        <p class="text-xs text-gray-600 line-clamp-2">${scene.description || 'Bez popisu'}</p>
                        <div class="mt-2 flex items-center justify-between">
                            <span class="text-xs text-gray-500">${scene.word_count || 0} slov</span>
                            <div class="intensity-indicator ${this.getIntensityClass(scene.emotional_intensity)} w-8" 
                                 style="height: 3px;"></div>
                        </div>
                    </div>
                `).join('');
            }
        });
    }
    
    selectScene(sceneId) {
        this.currentScene = this.scenes.find(s => s.id === sceneId);
        if (this.currentScene) {
            this.showSceneDetails();
            this.highlightSelectedScene(sceneId);
            
            // Notify collaboration about scene selection
            if (this.isCollaborationEnabled) {
                this.notifySceneSelection(sceneId);
            }
        }
    }
    
    showSceneDetails() {
        const panel = document.getElementById('scene-details-panel');
        if (!panel) {
            console.warn('Scene details panel not found in DOM');
            return;
        }
        
        panel.classList.remove('hidden');
        
        // Populate form with scene data
        this.setSafeValue('scene-title-input', this.currentScene.title || '');
        this.setSafeValue('scene-type-select', this.currentScene.scene_type || 'development');
        this.setSafeValue('scene-location-input', this.currentScene.location || '');
        this.setSafeValue('scene-description-input', this.currentScene.description || '');
        this.setSafeValue('scene-conflict-input', this.currentScene.conflict || '');
        this.setSafeValue('scene-hook-input', this.currentScene.hook || '');
        
        const intensity = this.currentScene.emotional_intensity || 0.5;
        this.setSafeValue('intensity-slider', intensity);
        const valueEl = document.getElementById('intensity-value');
        if (valueEl) valueEl.textContent = intensity;
        
        this.updateWordCount();
        this.renderSceneObjects();
        this.updateIntensityIndicator(intensity);
        
        // Scroll to panel
        panel.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Helper method to safely set form values
    setSafeValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.value = value;
        } else {
            console.warn(`Element #${elementId} not found in DOM`);
        }
    }
    
    // Safely update intensity indicator
    updateIntensityIndicator(value) {
        const indicator = document.getElementById('intensity-indicator');
        if (indicator) {
            indicator.style.width = `${value * 100}%`;
            
            // Update color based on intensity
            indicator.className = 'h-2.5 rounded-full';
            if (value >= 0.7) {
                indicator.classList.add('bg-red-600');
            } else if (value >= 0.4) {
                indicator.classList.add('bg-orange-500');
            } else {
                indicator.classList.add('bg-blue-500');
            }
        }
    }
    
    renderSceneObjects() {
        const container = document.getElementById('scene-objects');
        if (!container) {
            console.warn('Scene objects container not found');
            return;
        }
        
        if (!this.currentScene || !this.currentScene.objects || this.currentScene.objects.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">Žádné objekty ve scéně</p>';
            return;
        }
        
        container.innerHTML = `
            <div class="flex flex-wrap gap-2">
                ${this.currentScene.objects.map(obj => `
                    <div class="flex items-center bg-gray-100 px-3 py-1 rounded-full">
                        <span class="text-sm">${obj.name}</span>
                        <button class="ml-2 text-gray-500 hover:text-red-500 text-xs" 
                                onclick="expandManager.removeObjectFromScene(${obj.id})">×</button>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    async addNewScene() {
        try {
            // Check if user has permission
            if (!this.canEditScenes()) {
                ui.showToast('Nemáte oprávnění k vytváření scén', 'error');
                return;
            }
            
            const newSceneData = {
                title: 'Nová scéna',
                description: '',
                scene_type: 'development',
                project_id: this.currentProject?.id,
                location: '',
                emotional_intensity: 0.5
            };
            
            ui.showLoading('Vytvářím novou scénu...');
            
            const response = await state.api.createScene(newSceneData);
            
            if (response.success) {
                // Add to local scenes array
                this.scenes.push(response.scene);
                this.renderScenes();
                this.updateStats();
                
                // Auto-select the new scene for editing
                this.selectScene(response.scene.id);
                
                ui.showToast('Nová scéna vytvořena', 'success');
                
                // Notify collaborators
                if (this.isCollaborationEnabled) {
                    this.notifySceneCreated(response.scene);
                }
            }
            
        } catch (error) {
            ui.showToast('Chyba při vytváření scény: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    async saveSceneChanges() {
        if (!this.currentScene) return;
        
        try {
            const titleInput = document.getElementById('scene-title-input');
            const descInput = document.getElementById('scene-description-input');
            const typeSelect = document.getElementById('scene-type-select');
            const locationInput = document.getElementById('scene-location-input');
            const conflictInput = document.getElementById('scene-conflict-input');
            const hookInput = document.getElementById('scene-hook-input');
            const intensitySlider = document.getElementById('intensity-slider');
            
            // Make sure all required elements exist
            if (!titleInput || !descInput || !typeSelect) {
                ui.showToast('Některé vstupní prvky nebyly nalezeny', 'error');
                return;
            }
            
            const updatedData = {
                title: titleInput.value,
                description: descInput.value,
                scene_type: typeSelect.value,
                location: locationInput?.value || '',
                conflict: conflictInput?.value || '',
                hook: hookInput?.value || '',
                emotional_intensity: parseFloat(intensitySlider?.value || 0.5)
            };
            
            ui.showLoading('Ukládám změny...');
            
            const response = await state.api.updateScene(this.currentScene.id, updatedData);
            
            if (response.success) {
                // Update local scene data
                Object.assign(this.currentScene, updatedData);
                
                // Re-render scenes
                this.renderScenes();
                this.updateStats();
                
                ui.showToast('Scéna uložena', 'success');
                
                // Notify collaborators
                if (this.isCollaborationEnabled) {
                    this.notifySceneChanged(this.currentScene.id, updatedData);
                }
            }
            
        } catch (error) {
            ui.showToast('Chyba při ukládání: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    async deleteScene(sceneId) {
        if (!confirm('Opravdu chcete smazat tuto scénu?')) return;
        
        try {
            ui.showLoading('Mažu scénu...');
            
            const response = await state.api.deleteScene(sceneId);
            
            if (response.success) {
                // Remove from local array
                this.scenes = this.scenes.filter(s => s.id !== sceneId);
                
                // Close details panel if this scene was selected
                if (this.currentScene && this.currentScene.id === sceneId) {
                    this.closeScenePanel();
                }
                
                this.renderScenes();
                this.updateStats();
                
                ui.showToast('Scéna smazána', 'success');
            }
            
        } catch (error) {
            ui.showToast('Chyba při mazání: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    async analyzeStructure() {
        if (!this.scenes || this.scenes.length < 2) {
            ui.showToast('Pro analýzu struktury potřebujete alespoň 2 scény', 'warning');
            return;
        }
        
        try {
            // Get token estimate first
            const estimate = await state.api.request('/ai/token-estimate', {
                method: 'POST',
                body: {
                    operation_type: 'analyze_structure',
                    input_text: this.scenes.map(s => s.description).join(' ')
                }
            });
            
            if (!estimate.can_afford) {
                ui.showToast(`Nedostatek tokenů. Potřebujete ${estimate.estimate.estimated_total_cost} tokenů.`, 'warning');
                return;
            }
            
            // Show panel before API call to indicate activity
            this.toggleElementVisibility('structure-analysis-panel', true);
            ui.showLoading('AI analyzuje strukturu příběhu...');
            
            const response = await state.api.analyzeStructure(this.currentProject.id);
            
            if (response.success) {
                this.renderStructureAnalysis(response.analysis);
                ui.showToast('Strukturální analýza dokončena', 'success');
            }
            
        } catch (error) {
            ui.showToast('Chyba při analýze: ' + error.message, 'error');
            this.closeStructureAnalysis();
        } finally {
            ui.hideLoading();
        }
    }
    
    async suggestScenes() {
        try {
            const focusTypeElement = document.getElementById('suggestion-focus-select');
            const focusType = focusTypeElement?.value || 'any';
            
            ui.showLoading('AI generuje návrhy scén...');
            
            // Safely show the panel
            this.toggleElementVisibility('ai-suggestions-panel', true);
            
            const response = await state.api.suggestScenes(this.currentProject.id);
            
            if (response.success) {
                this.renderAISuggestions(response.suggestions);
                ui.showToast('AI návrhy připraveny', 'success');
            }
            
        } catch (error) {
            ui.showToast('Chyba při generování návrhů: ' + error.message, 'error');
            this.closeAISuggestions();
        } finally {
            ui.hideLoading();
        }
    }
    
    renderStructureAnalysis(analysis) {
        const content = document.getElementById('structure-analysis-content');
        if (!content) {
            console.warn('Structure analysis content container not found');
            return;
        }
        
        content.innerHTML = `
            <div class="space-y-6">
                <!-- Overall Score -->
                <div class="text-center">
                    <div class="text-4xl font-bold ${this.getScoreColor(analysis.overall_summary.overall_score)} mb-2">
                        ${analysis.overall_summary.overall_score}/5.0
                    </div>
                    <p class="text-gray-600">${analysis.overall_summary.overall_assessment}</p>
                </div>
                
                <!-- Score Breakdown -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    ${Object.entries(analysis.score_breakdown || {}).map(([type, data]) => `
                        <div class="text-center p-4 bg-gray-50 rounded-lg">
                            <div class="text-2xl font-bold ${this.getScoreColor(data.score)}">${data.score}</div>
                            <div class="text-sm text-gray-600">${data.critic}</div>
                        </div>
                    `).join('')}
                </div>
                
                <!-- Priority Recommendations -->
                <div>
                    <h4 class="text-lg font-semibold mb-3">🎯 Prioritní doporučení</h4>
                    <div class="space-y-2">
                        ${(analysis.priority_recommendations || []).slice(0, 5).map(rec => `
                            <div class="flex items-start space-x-3 p-3 ${this.getUrgencyBg(rec.urgency)} rounded-lg">
                                <span class="text-lg">${this.getUrgencyIcon(rec.urgency)}</span>
                                <div>
                                    <p class="text-sm">${rec.recommendation}</p>
                                    <p class="text-xs text-gray-500">od ${rec.critic}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <!-- Key Strengths -->
                ${(analysis.overall_summary.key_strengths || []).length > 0 ? `
                    <div>
                        <h4 class="text-lg font-semibold mb-3">💪 Silné stránky</h4>
                        <div class="space-y-1">
                            ${analysis.overall_summary.key_strengths.map(strength => `
                                <div class="flex items-center space-x-2">
                                    <span class="text-green-500">✓</span>
                                    <span class="text-sm">${strength}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Major Issues -->
                ${(analysis.overall_summary.major_issues || []).length > 0 ? `
                    <div>
                        <h4 class="text-lg font-semibold mb-3">⚠️ Hlavní problémy</h4>
                        <div class="space-y-1">
                            ${analysis.overall_summary.major_issues.map(issue => `
                                <div class="flex items-center space-x-2">
                                    <span class="text-red-500">⚠</span>
                                    <span class="text-sm">${issue}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    renderAISuggestions(suggestions) {
        const list = document.getElementById('ai-suggestions-list');
        if (!list) {
            console.warn('AI suggestions list container not found');
            return;
        }
        
        if (!suggestions || suggestions.length === 0) {
            list.innerHTML = '<div class="text-center text-gray-500">Žádné návrhy nebyly vygenerovány</div>';
            return;
        }
        
        list.innerHTML = suggestions.map((suggestion, index) => `
            <div class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border-l-4 border-blue-400">
                <div class="flex items-center justify-between mb-2">
                    <h5 class="font-semibold text-gray-800">${suggestion.title}</h5>
                    <div class="flex items-center space-x-2">
                        <span class="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                            ${this.getSceneTypeLabel(suggestion.scene_type)}
                        </span>
                        <span class="text-xs text-gray-500">
                            ${Math.round((suggestion.confidence || 0.8) * 100)}% jistota
                        </span>
                    </div>
                </div>
                
                <p class="text-sm text-gray-600 mb-3">${suggestion.description}</p>
                
                ${suggestion.suggested_objects && suggestion.suggested_objects.length > 0 ? `
                    <div class="mb-3">
                        <div class="text-xs text-gray-500 mb-1">Navrhované objekty:</div>
                        <div class="flex flex-wrap gap-1">
                            ${suggestion.suggested_objects.map(obj => `
                                <span class="text-xs px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full">${obj}</span>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="flex space-x-2">
                    <button onclick="expandManager.acceptSuggestion(${index})" 
                            class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                        ✓ Přijmout
                    </button>
                    <button onclick="expandManager.modifySuggestion(${index})" 
                            class="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600">
                        ✏️ Upravit
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    acceptSuggestion(index) {
        // Implement suggestion acceptance logic
        ui.showToast('Funkce bude implementována', 'info');
    }
    
    modifySuggestion(index) {
        // Implement suggestion modification logic
        ui.showToast('Funkce bude implementována', 'info');
    }
    
    // Utility methods
    getSceneTypeColor(type) {
        const colors = {
            'opening': 'border-blue-400',
            'inciting': 'border-green-400',
            'development': 'border-yellow-400',
            'rising_action': 'border-orange-400',
            'climax': 'border-red-400',
            'falling_action': 'border-purple-400',
            'resolution': 'border-indigo-400'
        };
        return colors[type] || 'border-gray-400';
    }
    
    getSceneTypeBadge(type) {
        const badges = {
            'opening': 'bg-blue-100 text-blue-800',
            'inciting': 'bg-green-100 text-green-800',
            'development': 'bg-yellow-100 text-yellow-800',
            'rising_action': 'bg-orange-100 text-orange-800',
            'climax': 'bg-red-100 text-red-800',
            'falling_action': 'bg-purple-100 text-purple-800',
            'resolution': 'bg-indigo-100 text-indigo-800'
        };
        return badges[type] || 'bg-gray-100 text-gray-800';
    }
    
    getSceneTypeLabel(type) {
        const labels = {
            'opening': 'Úvod',
            'inciting': 'Spouštěč',
            'development': 'Rozvoj',
            'rising_action': 'Stoupání',
            'climax': 'Vrchol',
            'falling_action': 'Klesání',
            'resolution': 'Rozuzlení'
        };
        return labels[type] || 'Rozvoj';
    }
    
    getIntensityClass(intensity) {
        const level = intensity || 0.5;
        if (level >= 0.7) return 'high-intensity';
        if (level >= 0.4) return 'medium-intensity';
        return 'low-intensity';
    }
    
    getScoreColor(score) {
        const scoreNum = parseFloat(score) || 0;
        if (scoreNum >= 4.0) return 'text-green-600';
        if (scoreNum >= 3.0) return 'text-blue-600';
        if (scoreNum >= 2.0) return 'text-orange-500';
        return 'text-red-600';
    }
    
    getUrgencyBg(urgency) {
        if (urgency === 'high') return 'bg-red-50';
        if (urgency === 'medium') return 'bg-orange-50';
        return 'bg-blue-50';
    }
    
    getUrgencyIcon(urgency) {
        if (urgency === 'high') return '🔴';
        if (urgency === 'medium') return '🟠';
        return '🔵';
    }
    
    updateStats() {
        const totalScenesEl = document.getElementById('total-scenes');
        const totalObjectsEl = document.getElementById('total-objects');
        const wordCountEl = document.getElementById('word-count');
        const completionPercentageEl = document.getElementById('completion-percentage');
        
        if (totalScenesEl) totalScenesEl.textContent = this.scenes.length;
        if (totalObjectsEl) totalObjectsEl.textContent = this.objects.length;
        
        const totalWords = this.scenes.reduce((sum, scene) => sum + (scene.word_count || 0), 0);
        if (wordCountEl) wordCountEl.textContent = totalWords.toLocaleString();
        
        // Calculate completion percentage based on scene types
        const hasOpening = this.scenes.some(s => s.scene_type === 'opening');
        const hasClimax = this.scenes.some(s => s.scene_type === 'climax');
        const hasResolution = this.scenes.some(s => s.scene_type === 'resolution');
        const developmentScenes = this.scenes.filter(s => s.scene_type === 'development').length;
        
        let completion = 0;
        if (hasOpening) completion += 20;
        if (developmentScenes >= 2) completion += 40;
        if (hasClimax) completion += 20;
        if (hasResolution) completion += 20;
        
        if (completionPercentageEl) completionPercentageEl.textContent = `${completion}%`;
    }
    
    updateWordCount() {
        const description = document.getElementById('scene-description-input')?.value || '';
        const charCount = description.length;
        const wordCount = description.trim() ? description.trim().split(/\s+/).length : 0;
        
        const charCountEl = document.getElementById('description-char-count');
        const wordCountEl = document.getElementById('description-word-count');
        
        if (charCountEl) charCountEl.textContent = charCount;
        if (wordCountEl) wordCountEl.textContent = wordCount;
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Auto-save functionality
    async autoSaveScene() {
        if (this.currentScene && this.canEditScenes()) {
            // Silently save without showing loading/success messages
            try {
                const descriptionEl = document.getElementById('scene-description-input');
                const titleEl = document.getElementById('scene-title-input');
                
                if (!descriptionEl || !titleEl) return;
                
                const updatedData = {
                    description: descriptionEl.value,
                    title: titleEl.value
                };
                
                await state.api.updateScene(this.currentScene.id, updatedData);
                
                // Update local data
                Object.assign(this.currentScene, updatedData);
                
                // Show subtle indication of auto-save
                const saveBtn = document.getElementById('save-scene-btn');
                if (saveBtn) {
                    saveBtn.textContent = '✓ Uloženo';
                    setTimeout(() => {
                        saveBtn.textContent = '💾 Uložit';
                    }, 2000);
                }
                
            } catch (error) {
                console.warn('Auto-save failed:', error);
            }
        }
    }
    
    canEditScenes() {
        // Check if user has edit permissions
        return true; // Simplified for now
    }
    
    // Collaboration methods
    initializeCollaboration() {
        if (typeof io !== 'undefined' && state.currentProject) {
            this.socket = io();
            this.isCollaborationEnabled = true;
            
            // Join project room
            this.socket.emit('join_project', {
                project_id: state.currentProject.id
            });
            
            // Listen for collaboration events
            this.setupCollaborationListeners();
        }
    }
    
    setupCollaborationListeners() {
        if (!this.socket) return;
        
        this.socket.on('user_joined', (data) => {
            this.handleUserJoined(data);
        });
        
        this.socket.on('scene_updated', (data) => {
            this.handleSceneUpdated(data);
        });
        
        this.socket.on('user_typing', (data) => {
            this.handleUserTyping(data);
        });
    }
    
    handleUserJoined(data) {
        // Implement user joined handling
        ui.showToast(`${data.username || 'Uživatel'} se připojil k projektu`, 'info');
    }
    
    handleSceneUpdated(data) {
        // Update scene if someone else edited it
        if (data.user_id !== state.currentUser?.id) {
            const sceneIndex = this.scenes.findIndex(s => s.id === data.scene_id);
            if (sceneIndex >= 0) {
                this.scenes[sceneIndex] = {...this.scenes[sceneIndex], ...data.changes};
                this.renderScenes();
                
                // Update current scene if it's the one being edited
                if (this.currentScene && this.currentScene.id === data.scene_id) {
                    this.currentScene = {...this.currentScene, ...data.changes};
                    this.showSceneDetails();
                }
                
                ui.showToast(`Scéna "${data.changes.title || 'Bez názvu'}" byla aktualizována`, 'info');
            }
        }
    }
    
    handleUserTyping(data) {
        // Show typing indicator for scene
        if (data.user_id !== state.currentUser?.id) {
            const scenePresence = document.getElementById(`scene-${data.scene_id}-presence`);
            if (scenePresence && data.is_typing) {
                const typingIndicator = document.createElement('div');
                typingIndicator.className = 'typing-indicator text-xs text-blue-500';
                typingIndicator.textContent = '✍️';
                typingIndicator.setAttribute('data-user', data.user_id);
                
                // Remove existing indicator for this user
                const existing = scenePresence.querySelector(`[data-user="${data.user_id}"]`);
                if (existing) {
                    existing.remove();
                }
                
                scenePresence.appendChild(typingIndicator);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {
                    if (typingIndicator.parentNode) {
                        typingIndicator.remove();
                    }
                }, 5000);
            }
        }
    }
    
    loadCollaborators() {
        // Implement collaborator loading
        console.log("Collaborator loading would happen here");
    }
    
    notifySceneSelection(sceneId) {
        // Notify others about scene selection
        if (this.socket) {
            this.socket.emit('scene_editing', {
                project_id: this.currentProject.id,
                scene_id: sceneId
            });
        }
    }
    
    notifySceneCreated(scene) {
        // Notify others about new scene
        if (this.socket) {
            this.socket.emit('scene_created', {
                project_id: this.currentProject.id,
                scene: scene
            });
        }
    }
    
    notifySceneChanged(sceneId, changes) {
        // Notify others about scene changes
        if (this.socket) {
            this.socket.emit('scene_changes', {
                project_id: this.currentProject.id,
                scene_id: sceneId,
                changes: changes
            });
        }
    }
    
    highlightSelectedScene(sceneId) {
        // Remove highlight from all scenes
        document.querySelectorAll('.scene-node, .kanban-scene').forEach(node => {
            node.classList.remove('active');
        });
        
        // Add highlight to selected scene
        document.querySelectorAll(`[data-scene-id="${sceneId}"]`).forEach(node => {
            node.classList.add('active');
        });
    }
    
    clearSceneHighlight() {
        document.querySelectorAll('.scene-node, .kanban-scene').forEach(node => {
            node.classList.remove('active');
        });
    }
    
    closeScenePanel() {
        const panel = document.getElementById('scene-details-panel');
        if (panel) {
            panel.classList.add('hidden');
            this.currentScene = null;
            this.clearSceneHighlight();
        } else {
            console.warn('Element #scene-details-panel not found in the DOM');
            this.currentScene = null;
        }
    }
    
    closeStructureAnalysis() {
        const panel = document.getElementById('structure-analysis-panel');
        if (panel) {
            panel.classList.add('hidden');
        } else {
            console.warn('Element #structure-analysis-panel not found in the DOM');
        }
    }
    
    closeAISuggestions() {
        const panel = document.getElementById('ai-suggestions-panel');
        if (panel) {
            panel.classList.add('hidden');
        } else {
            console.warn('Element #ai-suggestions-panel not found in the DOM');
        }
    }
    
    toggleViewMode(mode) {
        this.viewMode = mode;
        this.updateViewMode();
    }
    
    updateViewMode() {
        // Hide all views
        const viewIds = ['timeline-view', 'kanban-view', 'graph-view'];
        const btnIds = ['timeline-view-btn', 'kanban-view-btn', 'graph-view-btn'];
        
        viewIds.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.classList.add('hidden');
            }
        });
        
        // Show selected view
        const selectedView = document.getElementById(`${this.viewMode}-view`);
        if (selectedView) {
            selectedView.classList.remove('hidden');
        }
        
        // Update button states
        btnIds.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.classList.remove('bg-blue-500', 'text-white');
            }
        });
        
        const activeBtn = document.getElementById(`${this.viewMode}-view-btn`);
        if (activeBtn) {
            activeBtn.classList.add('bg-blue-500', 'text-white');
        }
    }
    
    // Helper method to safely toggle element visibility
    toggleElementVisibility(elementId, show = true) {
        const element = document.getElementById(elementId);
        if (element) {
            if (show) {
                element.classList.remove('hidden');
            } else {
                element.classList.add('hidden');
            }
            return true;
        } else {
            console.warn(`Element #${elementId} not found in the DOM`);
            return false;
        }
    }
    
    removeObjectFromScene(objectId) {
        // Implement object removal from scene
        ui.showToast('Funkce bude implementována', 'info');
    }
}

// Initialize expand phase manager
const expandManager = new ExpandPhaseManager();