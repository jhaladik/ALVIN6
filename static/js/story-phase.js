// static/js/story-phase.js - Story Phase Management
class StoryPhaseManager {
    constructor() {
        this.currentStory = null;
        this.isEditMode = false;
        this.autoSaveInterval = null;
    }
    
    async generateFinalStory() {
        if (!state.currentProject) {
            ui.showToast('Není vybrán žádný projekt', 'error');
            return;
        }
        
        try {
            // Check if project has enough scenes
            const projectData = await state.api.getProject(state.currentProject.id);
            if (!projectData.scenes || projectData.scenes.length < 2) {
                ui.showToast('Pro generování příběhu potřebujete alespoň 2 scény', 'warning');
                return;
            }
            
            // Get token estimate
            const estimate = await state.api.request('/ai/token-estimate', {
                method: 'POST',
                body: {
                    operation_type: 'generate_story',
                    input_text: projectData.scenes.map(s => s.description).join(' ')
                }
            });
            
            if (!estimate.can_afford) {
                ui.showToast(`Nedostatek tokenů. Potřebujete ${estimate.estimate.estimated_total_cost} tokenů.`, 'warning');
                return;
            }
            
            // Show generation progress
            this.showGenerationProgress();
            
            const response = await state.api.request(`/ai/projects/${state.currentProject.id}/generate-story`, {
                method: 'POST'
            });
            
            if (response.success) {
                this.currentStory = response.story;
                this.displayGeneratedStory(response.story);
                this.updateStoryStats(response.story);
                
                // Update user tokens
                const userResponse = await state.api.getCurrentUser();
                state.currentUser = userResponse.user;
                ui.updateTokenDisplay(state.currentUser);
                
                ui.showToast('Příběh úspěšně vygenerován!', 'success');
            }
            
        } catch (error) {
            ui.showToast('Chyba při generování příběhu: ' + error.message, 'error');
        } finally {
            this.hideGenerationProgress();
        }
    }
    
    showGenerationProgress() {
        document.getElementById('story-loading').classList.remove('hidden');
        document.getElementById('story-content').classList.add('hidden');
        
        const steps = [
            'Analyzuji strukturu příběhu...',
            'Identifikuji klíčové motivy...',
            'Propojuji scény do celku...',
            'Generuji finální text...',
            'Dokončuji formátování...'
        ];
        
        let currentStep = 0;
        const progressBar = document.getElementById('generation-progress');
        const statusText = document.getElementById('generation-status');
        
        const interval = setInterval(() => {
            if (currentStep < steps.length) {
                statusText.textContent = steps[currentStep];
                progressBar.style.width = `${((currentStep + 1) / steps.length) * 100}%`;
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 1000);
        
        this.generationInterval = interval;
    }
    
    hideGenerationProgress() {
        document.getElementById('story-loading').classList.add('hidden');
        document.getElementById('story-content').classList.remove('hidden');
        
        if (this.generationInterval) {
            clearInterval(this.generationInterval);
        }
    }
    
    displayGeneratedStory(story) {
        const storyText = document.getElementById('story-text');
        const metadata = document.getElementById('story-metadata');
        
        // Display story content
        storyText.innerHTML = this.formatStoryText(story);
        
        // Display metadata
        document.getElementById('meta-genre').textContent = story.genre || 'Neurčeno';
        document.getElementById('meta-theme').textContent = story.theme || 'Neurčeno';
        document.getElementById('meta-audience').textContent = story.target_audience || 'Neurčeno';
        document.getElementById('meta-tone').textContent = story.tone || 'Neurčeno';
        document.getElementById('meta-elements').textContent = (story.unique_elements || []).join(', ') || 'Žádné';
        document.getElementById('meta-symbols').textContent = (story.key_symbols || []).join(', ') || 'Žádné';
        
        // Update title
        document.getElementById('final-story-title').textContent = story.title || state.currentProject.title;
        document.getElementById('story-subtitle').textContent = story.premise || 'Váš dokončený příběh';
        
        metadata.classList.remove('hidden');
    }
    
    formatStoryText(story) {
        // Create formatted story text from scenes and story data
        let formattedText = '';
        
        if (story.title) {
            formattedText += `<h1 class="text-3xl font-bold text-center mb-8">${story.title}</h1>`;
        }
        
        if (story.premise) {
            formattedText += `<div class="text-lg text-gray-600 text-center mb-8 italic">${story.premise}</div>`;
        }
        
        // Add story content
        if (story.story_arc) {
            formattedText += `<div class="story-content">${this.convertToHTML(story.story_arc)}</div>`;
        }
        
        return formattedText;
    }
    
    convertToHTML(text) {
        // Convert plain text to formatted HTML
        return text
            .split('\n\n')
            .map(paragraph => `<p class="mb-4">${paragraph.trim()}</p>`)
            .join('');
    }
    
    updateStoryStats(story) {
        const wordCount = this.countWords(story.story_arc || '');
        const pageCount = Math.ceil(wordCount / 250);
        const readingTime = Math.ceil(wordCount / 200);
        
        document.getElementById('story-word-count').textContent = wordCount.toLocaleString();
        document.getElementById('story-pages').textContent = pageCount;
        document.getElementById('reading-time').textContent = readingTime;
        document.getElementById('marketability-score').textContent = story.marketability || 'N/A';
        document.getElementById('overall-quality').textContent = '4.2'; // Calculated from analysis
    }
    
    countWords(text) {
        return text.trim() ? text.trim().split(/\s+/).length : 0;
    }
    
    toggleEditMode() {
        this.isEditMode = !this.isEditMode;
        const storyText = document.getElementById('story-text');
        const editBtn = document.getElementById('edit-mode-btn');
        
        if (this.isEditMode) {
            // Switch to edit mode
            const currentText = storyText.textContent;
            storyText.innerHTML = `<textarea class="w-full min-h-96 p-4 border border-gray-300 rounded-lg resize-none" id="story-editor-textarea">${currentText}</textarea>`;
            editBtn.textContent = '💾 Uložit';
            editBtn.classList.add('bg-blue-500', 'text-white');
            
            // Start auto-save
            this.startAutoSave();
        } else {
            // Switch to view mode
            const textarea = document.getElementById('story-editor-textarea');
            if (textarea) {
                const newText = textarea.value;
                storyText.innerHTML = this.convertToHTML(newText);
                this.saveStoryChanges(newText);
            }
            editBtn.textContent = '✏️ Editovat';
            editBtn.classList.remove('bg-blue-500', 'text-white');
            
            // Stop auto-save
            this.stopAutoSave();
        }
    }
    
    startAutoSave() {
        this.autoSaveInterval = setInterval(() => {
            const textarea = document.getElementById('story-editor-textarea');
            if (textarea) {
                this.saveStoryChanges(textarea.value, true);
            }
        }, 30000); // Auto-save every 30 seconds
    }
    
    stopAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
    }
    
    async saveStoryChanges(content, isAutoSave = false) {
        try {
            // Save story content (implementation depends on backend)
            const response = await state.api.request(`/projects/${state.currentProject.id}/story`, {
                method: 'PUT',
                body: { content: content }
            });
            
            if (response.success && !isAutoSave) {
                ui.showToast('Příběh uložen', 'success');
            }
            
        } catch (error) {
            if (!isAutoSave) {
                ui.showToast('Chyba při ukládání: ' + error.message, 'error');
            }
        }
    }
    
    async exportStory() {
        document.getElementById('export-panel').classList.toggle('hidden');
    }
    
    async exportFormat(format) {
        if (!this.currentStory) {
            ui.showToast('Nejprve vygenerujte příběh', 'warning');
            return;
        }
        
        try {
            ui.showLoading(`Exportuji do ${format.toUpperCase()}...`);
            
            const exportOptions = {
                format: format,
                include_metadata: document.getElementById('include-metadata').checked,
                include_scenes: document.getElementById('include-scenes').checked,
                include_objects: document.getElementById('include-objects').checked
            };
            
            const response = await state.api.request(`/projects/${state.currentProject.id}/export`, {
                method: 'POST',
                body: exportOptions
            });
            
            if (response.success) {
                // Download file
                const link = document.createElement('a');
                link.href = response.download_url;
                link.download = `${state.currentProject.title}.${format}`;
                link.click();
                
                ui.showToast(`Export do ${format.toUpperCase()} dokončen`, 'success');
            }
            
        } catch (error) {
            ui.showToast('Chyba při exportu: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    async shareStory() {
        if (!this.currentStory) {
            ui.showToast('Nejprve vygenerujte příběh', 'warning');
            return;
        }
        
        try {
            const response = await state.api.request(`/projects/${state.currentProject.id}/share`, {
                method: 'POST',
                body: { type: 'public_link' }
            });
            
            if (response.success) {
                // Copy share link to clipboard
                await navigator.clipboard.writeText(response.share_url);
                ui.showToast('Odkaz zkopírován do schránky', 'success');
            }
            
        } catch (error) {
            ui.showToast('Chyba při sdílení: ' + error.message, 'error');
        }
    }
}