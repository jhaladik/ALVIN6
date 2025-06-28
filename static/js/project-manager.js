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
    
    // Setup the event listeners for project filtering and sorting
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
    }
    
    // Load projects from the server
    // static/js/project-manager.js - Updated loadProjects method
    async loadProjects() {
        try {
            document.getElementById('projects-loading').classList.remove('hidden');
            document.getElementById('projects-grid').classList.add('hidden');
            
            // Make the API call
            const response = await state.api.getProjects();
            
            // Debug the response
            console.log('Project response:', response);
            
            // Check if response exists and is properly structured
            if (!response) {
                throw new Error('Empty response from server');
            }
            
            // Handle different response formats - the API might return an array directly 
            // or an object with a projects property
            if (Array.isArray(response)) {
                this.projects = response;
            } else if (response.success && Array.isArray(response.projects)) {
                this.projects = response.projects;
            } else if (typeof response === 'object') {
                // Try to extract projects from the response object
                this.projects = response.projects || response.data || [];
            } else {
                this.projects = [];
            }
            
            console.log('Processed projects:', this.projects);
            
            // Even if we have no projects, we should update the UI
            this.filterAndSortProjects();
            
            document.getElementById('projects-loading').classList.add('hidden');
            document.getElementById('projects-grid').classList.remove('hidden');
            
        } catch (error) {
            console.error('Failed to load projects:', error);
            ui.showToast('Failed to load projects: ' + error.message, 'error');
            
            document.getElementById('projects-loading').classList.add('hidden');
            document.getElementById('projects-grid').innerHTML = `
                <div class="col-span-2 text-center py-8 text-gray-500">
                    <p>Failed to load projects: ${error.message}</p>
                    <button onclick="loadProjects()" class="mt-2 text-blue-500 hover:underline">Retry</button>
                </div>
            `;
            document.getElementById('projects-grid').classList.remove('hidden');
        }
    }
    
    // Filter and sort projects based on user preferences
    filterAndSortProjects() {
        // Filter projects
        if (this.currentFilter === 'all') {
            this.filteredProjects = [...this.projects];
        } else if (this.currentFilter === 'recent') {
            // Sort by date and take the 10 most recent
            this.filteredProjects = [...this.projects]
                .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
                .slice(0, 10);
        } else if (this.currentFilter === 'mine') {
            // Only show projects created by the current user
            this.filteredProjects = this.projects.filter(p => p.user_id === state.currentUser?.id);
        }
        
        // Apply search filter
        if (this.searchTerm) {
            this.filteredProjects = this.filteredProjects.filter(p => 
                p.title.toLowerCase().includes(this.searchTerm) || 
                (p.description && p.description.toLowerCase().includes(this.searchTerm))
            );
        }
        
        // Sort projects
        if (this.currentSort === 'title') {
            this.filteredProjects.sort((a, b) => a.title.localeCompare(b.title));
        } else if (this.currentSort === 'updated') {
            this.filteredProjects.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
        }
        
        this.renderProjects();
    }
    
    // Render the projects in the grid
    renderProjects() {
        const projectsGrid = document.getElementById('projects-grid');
        if (!projectsGrid) return;
        
        console.log('Rendering projects:', this.filteredProjects);
        
        if (!this.filteredProjects || this.filteredProjects.length === 0) {
            projectsGrid.innerHTML = `
                <div class="col-span-2 text-center py-8 text-gray-500">
                    <p>No projects found. Create a new project or change your filters.</p>
                    <div class="mt-4">
                        <button onclick="createNewProject()" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600">
                            ✨ Create New Project
                        </button>
                    </div>
                </div>
            `;
            return;
        }
        
        // Check if the projects have the expected structure
        const validProjects = this.filteredProjects.filter(p => p && typeof p === 'object');
        
        if (validProjects.length === 0) {
            projectsGrid.innerHTML = `
                <div class="col-span-2 text-center py-8 text-gray-500">
                    <p>Received invalid project data from server. Please try again or create a new project.</p>
                </div>
            `;
            return;
        }
        
        projectsGrid.innerHTML = validProjects.map(project => `
            <div class="bg-white rounded-lg shadow-md p-4 border border-gray-200 hover:border-blue-400 cursor-pointer transition-all"
                 onclick="selectProject('${project.id}')">
                <h3 class="font-bold text-gray-800 mb-1">${project.title || 'Untitled Project'}</h3>
                <p class="text-sm text-gray-600 mb-2 line-clamp-2">${project.description || 'No description'}</p>
                <div class="flex justify-between items-center text-xs text-gray-500">
                    <span>Scenes: ${project.scene_count || 0}</span>
                    <span>Genre: ${project.genre || 'Unknown'}</span>
                </div>
                <div class="mt-2 flex justify-between items-center">
                    <span class="text-xs text-gray-500">
                        Updated: ${this.formatDate(project.updated_at)}
                    </span>
                    <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                        ${project.current_phase || 'idea'}
                    </span>
                </div>
            </div>
        `).join('');
    }
        
    // Format date for display
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleDateString();
    }
    
    // Select a project
    async selectProject(id) {
        try {
            ui.showLoading('Loading project...');
            
            const response = await state.api.getProject(id);
            
            // Set the current project in the global state
            state.currentProject = response.project;
            
            // If we're in the expand phase, update the expand manager
            if (state.currentPhase === 'expand' && expandManager) {
                expandManager.currentProject = response.project;
                expandManager.scenes = response.scenes || [];
                expandManager.objects = response.objects || [];
                expandManager.renderScenes();
                expandManager.updateStats();
            }
            
            // Update the UI to reflect the selected project
            document.getElementById('current-project-title').textContent = response.project.title;
            
            // Update the project status bar
            updateProjectStatusBar();
            
            // Close the project selection modal
            this.closeProjectList();
            
            ui.hideLoading();
            ui.showToast(`Project "${response.project.title}" loaded`, 'success');
            
        } catch (error) {
            ui.hideLoading();
            ui.showToast('Failed to load project: ' + error.message, 'error');
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
    // Show the project list modal
    showProjectList() {
        document.getElementById('project-list-modal').classList.remove('hidden');
        this.loadProjects();
    }
    
    // Close the project list modal
    closeProjectList() {
        document.getElementById('project-list-modal').classList.add('hidden');
    }
}

// Global function to select a project
async function selectProject(id) {
    await projectManager.selectProject(id);
}

// Global function to show the project list
function showProjectList() {
    projectManager.showProjectList();
}

// Global function to close the project list
function closeProjectList() {
    projectManager.closeProjectList();
}