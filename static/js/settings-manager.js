// static/js/settings-manager.js - Settings Management
class SettingsManager {
    constructor() {
        this.currentTab = 'account';
        this.userSettings = {};
    }
    
    async loadSettings() {
        try {
            const response = await state.api.getCurrentUser();
            this.userSettings = response.user;
            
            // Populate form fields
            this.populateAccountSettings();
            this.loadBillingSettings();
            
        } catch (error) {
            ui.showToast('Chyba při načítání nastavení: ' + error.message, 'error');
        }
    }
    
    populateAccountSettings() {
        document.getElementById('username-input').value = this.userSettings.username || '';
        document.getElementById('email-input').value = this.userSettings.email || '';
    }
    
    async loadBillingSettings() {
        try {
            const response = await state.api.request('/billing/subscription');
            
            const currentPlan = document.getElementById('current-plan');
            if (response.subscription) {
                currentPlan.innerHTML = `
                    <h4 class="font-semibold mb-2">Současný plán: ${response.subscription.plan.display_name}</h4>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>Měsíční limit: ${response.subscription.plan.monthly_token_limit.toLocaleString()} tokenů</div>
                        <div>Využito: ${response.usage_analytics.total_used_lifetime.toLocaleString()} tokenů</div>
                        <div>Cena: $${response.subscription.plan.monthly_price}/měsíc</div>
                        <div>Status: ${response.subscription.status}</div>
                    </div>
                `;
            } else {
                currentPlan.innerHTML = `
                    <h4 class="font-semibold mb-2">Žádné aktivní předplatné</h4>
                    <p class="text-sm text-gray-600">Používáte bezplatný plán</p>
                `;
            }
            
        } catch (error) {
            console.error('Error loading billing settings:', error);
        }
    }
    
    showSettingsTab(tabName) {
        // Hide all content
        document.querySelectorAll('.settings-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        // Remove active class from all tabs
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Show selected content
        document.getElementById(`${tabName}-settings`).classList.remove('hidden');
        
        // Add active class to selected tab
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        this.currentTab = tabName;
    }
    
    async saveAccountSettings() {
        try {
            const updatedData = {
                username: document.getElementById('username-input').value,
                email: document.getElementById('email-input').value
            };
            
            const password = document.getElementById('password-input').value;
            if (password) {
                updatedData.password = password;
            }
            
            ui.showLoading('Ukládám nastavení...');
            
            const response = await state.api.request('/auth/update-profile', {
                method: 'PUT',
                body: updatedData
            });
            
            if (response.success) {
                ui.showToast('Nastavení uloženo', 'success');
                
                // Clear password field
                document.getElementById('password-input').value = '';
                
                // Update local user data
                Object.assign(state.currentUser, updatedData);
                document.getElementById('user-info').textContent = `${state.currentUser.username} (${state.currentUser.plan})`;
            }
            
        } catch (error) {
            ui.showToast('Chyba při ukládání: ' + error.message, 'error');
        } finally {
            ui.hideLoading();
        }
    }
    
    closeSettings() {
        document.getElementById('settings-modal').classList.add('hidden');
    }
}

// Enhanced expand phase functions
function addNewScene() {
    expandManager.addNewScene();
}

function saveSceneChanges() {
    expandManager.saveSceneChanges();
}

function deleteCurrentScene() {
    if (expandManager.currentScene) {
        expandManager.deleteScene(expandManager.currentScene.id);
    }
}

function closeScenePanel() {
    expandManager.closeScenePanel();
}

function analyzeStructure() {
    expandManager.analyzeStructure();
}

function suggestScenes() {
    expandManager.suggestScenes();
}

function closeStructureAnalysis() {
    expandManager.closeStructureAnalysis();
}

function closeAISuggestions() {
    expandManager.closeAISuggestions();
}

function toggleViewMode(mode) {
    expandManager.toggleViewMode(mode);
}

// Global function implementations
async function loadProjects() {
    await projectManager.loadProjects();
}

async function selectProject(id) {
    await projectManager.selectProject(id);
}

function createNewProject() {
    ui.showToast('Pro vytvoření projektu použijte fázi "Nápad"', 'info');
    setPhase('idea');
    if (document.getElementById('project-list-modal').classList.contains('hidden') === false) {
        projectManager.closeProjectList();
    }
}

function showProjectList() {
    document.getElementById('project-list-modal').classList.remove('hidden');
    projectManager.loadProjects();
}

function closeProjectList() {
    projectManager.closeProjectList();
}

function showSettings() {
    document.getElementById('settings-modal').classList.remove('hidden');
    settingsManager.loadSettings();
}

function closeSettings() {
    settingsManager.closeSettings();
}

function showSettingsTab(tabName) {
    settingsManager.showSettingsTab(tabName);
}

function saveAccountSettings() {
    settingsManager.saveAccountSettings();
}

function generateFinalStory() {
    storyManager.generateFinalStory();
}

function exportStory() {
    storyManager.exportStory();
}

function exportFormat(format) {
    storyManager.exportFormat(format);
}

function shareStory() {
    storyManager.shareStory();
}

function toggleEditMode() {
    storyManager.toggleEditMode();
}

function togglePreviewMode() {
    // Toggle between edit and preview
    ui.showToast('Preview mode bude implementován', 'info');
}

function toggleFullscreen() {
    const storyEditor = document.getElementById('story-editor');
    if (!document.fullscreenElement) {
        storyEditor.requestFullscreen().catch(err => {
            ui.showToast('Fullscreen není podporován', 'warning');
        });
    } else {
        document.exitFullscreen();
    }
}

async function upgradePlan() {
    try {
        const response = await state.api.request('/billing/plans');
        if (response.success) {
            // Show upgrade modal with available plans
            ui.showToast('Upgrade modální okno bude implementováno', 'info');
        }
    } catch (error) {
        ui.showToast('Chyba při načítání plánů: ' + error.message, 'error');
    }
}

async function buyTokens() {
    try {
        ui.showToast('Přesměrování na nákup tokenů...', 'info');
        // Implementation for token purchase
    } catch (error) {
        ui.showToast('Chyba při nákupu tokenů: ' + error.message, 'error');
    }
}

async function viewBillingHistory() {
    try {
        const response = await state.api.request('/billing/billing-history');
        if (response.success) {
            ui.showToast('Historie plateb modální okno bude implementováno', 'info');
        }
    } catch (error) {
        ui.showToast('Chyba při načítání historie: ' + error.message, 'error');
    }
}

// Collaboration functions
function inviteCollaborator() {
    if (!state.currentProject) {
        ui.showToast('Nejprve vyberte projekt', 'warning');
        return;
    }
    
    const email = prompt('Zadejte email collaboratora:');
    if (email) {
        inviteUserToProject(email);
    }
}

async function inviteUserToProject(email) {
    try {
        const response = await state.api.request(`/collaboration/projects/${state.currentProject.id}/invite`, {
            method: 'POST',
            body: {
                email: email,
                role: 'editor',
                permissions: {
                    edit_scenes: true,
                    add_comments: true,
                    view_collaborators: true
                }
            }
        });
        
        if (response.success) {
            ui.showToast(`Pozvánka odeslána na ${email}`, 'success');
        }
        
    } catch (error) {
        ui.showToast('Chyba při odesílání pozvánky: ' + error.message, 'error');
    }
}

function toggleCollaborationPanel() {
    const content = document.getElementById('collaboration-content');
    const toggle = document.getElementById('collaboration-toggle');
    
    content.classList.toggle('hidden');
    toggle.textContent = content.classList.contains('hidden') ? '▼' : '▲';
}

// Initialize managers
const storyManager = new StoryPhaseManager();
const projectManager = new ProjectManager();
const settingsManager = new SettingsManager();

// Enhanced phase management
function setPhase(phase) {
    state.currentPhase = phase;
    ui.setPhase(phase);
    
    // Phase-specific initialization
    switch (phase) {
        case 'expand':
            if (state.currentProject) {
                expandManager.loadProjectData(state.currentProject.id);
            }
            break;
        case 'story':
            // Initialize story phase if needed
            break;
    }
}

// Auto-save functionality for various forms
function setupAutoSave() {
    const autoSaveInputs = document.querySelectorAll('[data-autosave]');
    
    autoSaveInputs.forEach(input => {
        let timeout;
        input.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                saveFormData(input);
            }, 2000);
        });
    });
}

function saveFormData(input) {
    const formType = input.dataset.autosave;
    const formData = new FormData(input.closest('form'));
    
    // Save to localStorage as backup
    localStorage.setItem(`autosave_${formType}`, JSON.stringify(Object.fromEntries(formData)));
}

// Keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + S - Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            
            if (state.currentPhase === 'expand' && expandManager.currentScene) {
                expandManager.saveSceneChanges();
            } else if (state.currentPhase === 'story' && storyManager.isEditMode) {
                storyManager.toggleEditMode(); // Save and exit edit mode
            }
        }
        
        // Ctrl/Cmd + N - New scene (in expand phase)
        if ((e.ctrlKey || e.metaKey) && e.key === 'n' && state.currentPhase === 'expand') {
            e.preventDefault();
            expandManager.addNewScene();
        }
        
        // Escape - Close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal:not(.hidden), .fixed:not(.hidden)');
            if (openModals.length > 0) {
                const lastModal = openModals[openModals.length - 1];
                
                if (lastModal.id === 'project-list-modal') {
                    closeProjectList();
                } else if (lastModal.id === 'settings-modal') {
                    closeSettings();
                } else if (lastModal.id === 'scene-details-panel') {
                    closeScenePanel();
                }
            }
        }
    });
}

// Enhanced UI feedback
function showTokenUsageWarning(remaining) {
    if (remaining < 100) {
        const warning = document.createElement('div');
        warning.className = 'fixed top-4 right-4 bg-yellow-500 text-white p-4 rounded-lg shadow-lg z-50';
        warning.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>⚠️</span>
                <div>
                    <div class="font-semibold">Málo tokenů</div>
                    <div class="text-sm">Zbývá ${remaining} tokenů</div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-yellow-200">✕</button>
            </div>
        `;
        
        document.body.appendChild(warning);
        
        setTimeout(() => {
            if (warning.parentElement) {
                warning.remove();
            }
        }, 10000);
    }
}

// Performance monitoring
function trackPerformance(operation, startTime) {
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    console.log(`Operation ${operation} took ${duration.toFixed(2)}ms`);
    
    // Track slow operations
    if (duration > 1000) {
        console.warn(`Slow operation detected: ${operation} (${duration.toFixed(2)}ms)`);
    }
}

// Error boundary
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    
    ui.showToast('Došlo k neočekávané chybě. Obnovte stránku.', 'error');
    
    // Report error to logging service
    // reportError(event.error);
});

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    setupAutoSave();
    setupKeyboardShortcuts();
    
    // Check for saved form data
    const savedData = localStorage.getItem('autosave_scene');
    if (savedData) {
        console.log('Found saved form data');
        // Could restore autosaved data
    }
});