// static/js/project-manager.js - Project Management
class ProjectManager {
    constructor() {
        this.projects = [];
        this.filteredProjects = [];
        this.currentFilter = 'all';
        this.currentSort = 'updated';
        this.searchTerm = '';
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const searchInput = document.getElementById('project-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchTerm = e.target.value.toLowerCase();
                this.filterAndSortProjects();
            });
        }
        
        const filterSelect = document.getElementById('project-filter');
        if (filterSelect) {
            filterSelect.addEventListener('change', (e) => {
                this.currentFilter = e.target.value;
                this.filterAndSortProjects();
            });
        }
        
        const sortSelect = document.getElementById('project-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.currentSort = e.target.value;
                this.filterAndSortProjects();
            });
        }
    }
    
    async loadProjects() {
        try {
            document.getElementById('projects-loading').classList.remove('hidden');
            document.getElementById('projects-grid').classList.add('hidden');
            
            const response = await state.api.getProjects();
            this.projects = response || [];
            
            this.filterAndSortProjects();
            this.renderProjects();
            
        } catch (error) {
            ui.showToast('Chyba při načítání projektů: ' + error.message, 'error');
        } finally {
            document.getElementById('projects-loading').classList.add('hidden');
            document.getElementById('projects-grid').classList.remove('hidden');
        }
    }
    
    filterAndSortProjects() {
        // Filter projects
        this.filteredProjects = this.projects.filter(project => {
            // Search filter
            if (this.searchTerm) {
                const searchable = `${project.title} ${project.description} ${project.genre}`.toLowerCase();
                if (!searchable.includes(this.searchTerm)) {
                    return false;
                }
            }
            
            // Phase filter
            if (this.currentFilter !== 'all') {
                if (this.currentFilter === 'active') {
                    return project.status === 'active';
                } else {
                    return project.current_phase === this.currentFilter;
                }
            }
            
            return true;
        });
        
        // Sort projects
        this.filteredProjects.sort((a, b) => {
            switch (this.currentSort) {
                case 'updated':
                    return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
                case 'created':
                    return new Date(b.created_at) - new Date(a.created_at);
                case 'title':
                    return a.title.localeCompare(b.title);
                case 'genre':
                    return (a.genre || '').localeCompare(b.genre || '');
                default:
                    return 0;
            }
        });
        
        this.renderProjects();
    }
    
    renderProjects() {
        const grid = document.getElementById('projects-grid');
        const noProjects = document.getElementById('no-projects');
        
        if (this.filteredProjects.length === 0) {
            grid.innerHTML = '';
            noProjects.classList.remove('hidden');
            return;
        }
        
        noProjects.classList.add('hidden');
        
        grid.innerHTML = this.filteredProjects.map(project => `
            <div class="project-card bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer" 
                 data-project-id="${project.id}" onclick="projectManager.selectProject('${project.id}')">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-3">
                        <div class="text-xs px-2 py-1 rounded-full ${this.getPhaseColor(project.current_phase)}">
                            ${this.getPhaseLabel(project.current_phase)}
                        </div>
                        <div class="text-xs text-gray-500">
                            ${this.formatDate(project.updated_at || project.created_at)}
                        </div>
                    </div>
                    
                    <h3 class="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">${project.title}</h3>
                    
                    <p class="text-sm text-gray-600 mb-4 line-clamp-3">${project.description || 'Bez popisu'}</p>
                    
                    <div class="flex items-center justify-between text-xs text-gray-500 mb-4">
                        <span>${project.genre || 'Bez žánru'}</span>
                        <span>${project.scene_count || 0} scén</span>
                    </div>
                    
                    <!-- Progress bar -->
                    <div class="mb-4">
                        <div class="flex items-center justify-between text-xs text-gray-500 mb-1">
                            <span>Progres</span>
                            <span>${this.calculateProgress(project)}%</span>
                        </div>
                        <div class="bg-gray-200 rounded-full h-2">
                            <div class="bg-blue-500 h-2 rounded-full transition-all" 
                                 style="width: ${this.calculateProgress(project)}%"></div>
                        </div>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-1">
                            ${project.current_word_count ? `
                                <span class="text-xs text-gray-500">${project.current_word_count.toLocaleString()} slov</span>
                            ` : ''}
                        </div>
                        <div class="flex space-x-1">
                            <button onclick="event.stopPropagation(); projectManager.editProject('${project.id}')" 
                                    class="text-blue-500 hover:text-blue-700 text-xs p-1">✏️</button>
                            <button onclick="event.stopPropagation(); projectManager.deleteProject('${project.id}')" 
                                    class="text-red-500 hover:text-red-700 text-xs p-1">🗑️</button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    async selectProject(projectId) {
        try {
            ui.showLoading('Načítám projekt...');
            
            const response = await state.api.getProject(projectId);
            state.currentProject = response.project;
            
            // Update UI
            document.getElementById('current-project-title').textContent = response.project.title;
            
            // Set appropriate phase
            setPhase(response.project.current_phase || 'idea');
            
            // Load project data based on phase
            if (response.project.current_phase === 'expand') {
                await expandManager.loadProjectData(projectId);
            }
            
            this.closeProjectList();
            ui.showToast('Projekt načten', 'success');
            
        } catch (error) {
            ui.showToast('Chyba při načítání projektu: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    async deleteProject(projectId) {
        const project = this.projects.find(p => p.id === projectId);
        if (!project) return;
        
        if (!confirm(`Opravdu chcete smazat projekt "${project.title}"?`)) return;
        
        try {
            ui.showLoading('Mažu projekt...');
            
            const response = await state.api.request(`/projects/${projectId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                // Remove from local array
                this.projects = this.projects.filter(p => p.id !== projectId);
                this.filterAndSortProjects();
                
                ui.showToast('Projekt smazán', 'success');
                
                // If this was current project, clear it
                if (state.currentProject && state.currentProject.id === projectId) {
                    state.currentProject = null;
                    document.getElementById('current-project-title').textContent = 'Vyberte projekt';
                }
            }
            
        } catch (error) {
            ui.showToast('Chyba při mazání projektu: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    closeProjectList() {
        document.getElementById('project-list-modal').classList.add('hidden');
    }
    
    getPhaseColor(phase) {
        const colors = {
            'idea': 'bg-yellow-100 text-yellow-800',
            'expand': 'bg-blue-100 text-blue-800',
            'story': 'bg-green-100 text-green-800'
        };
        return colors[phase] || 'bg-gray-100 text-gray-800';
    }
    
    getPhaseLabel(phase) {
        const labels = {
            'idea': 'Nápad',
            'expand': 'Expanze',
            'story': 'Příběh'
        };
        return labels[phase] || 'Neznámé';
    }
    
    calculateProgress(project) {
        let progress = 0;
        
        if (project.current_phase === 'expand') progress = 50;
        if (project.current_phase === 'story') progress = 100;
        
        // Add scene-based progress
        if (project.scene_count) {
            progress += Math.min(project.scene_count * 5, 30);
        }
        
        return Math.min(progress, 100);
    }
    
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) return 'Včera';
        if (diffDays <= 7) return `Před ${diffDays} dny`;
        
        return date.toLocaleDateString('cs-CZ');
    }
}