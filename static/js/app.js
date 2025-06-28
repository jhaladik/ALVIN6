// --- STATE MANAGEMENT ---
const state = {
    api: new StoryForgeAPI(),
    currentUser: null,
    currentProject: null,
    currentPhase: 'idea',
    selectedStoryIntent: '',
    ideaAnalysisResults: null,
    isAuthenticated: false,
};

// --- DOM ELEMENTS ---
const loginForm = document.getElementById('login-form');
const ideaTextArea = document.getElementById('idea-text');
const analyzeIdeaBtn = document.getElementById('analyze-idea-btn');


// --- CORE LOGIC ---
async function checkAuthStatus() {
    try {
        const response = await state.api.getCurrentUser();
        state.currentUser = response.user;
        state.isAuthenticated = true;
        ui.setLoginState(true, state.currentUser);
        document.querySelectorAll('#new-project-btn, #show-projects-btn, #analyze-idea-btn, #idea-text').forEach(el => el.disabled = false);
        await loadProjects();
    } catch (error) {
        state.isAuthenticated = false;
        ui.setLoginState(false);
        document.getElementById('current-project-title').textContent = 'Přihlaste se pro pokračování';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const loginButton = document.getElementById('login-button');
    
    loginButton.disabled = true;
    loginButton.textContent = 'Přihlašuji...';
    
    try {
        const response = await state.api.login(email, password);
        state.currentUser = response.user;
        state.isAuthenticated = true;
        ui.setLoginState(true, state.currentUser);
        ui.showToast('Úspěšně přihlášen!', 'success');
        document.querySelectorAll('#new-project-btn, #show-projects-btn, #analyze-idea-btn, #idea-text').forEach(el => el.disabled = false);
        await loadProjects();
    } catch (error) {
        ui.showToast('Chyba při přihlášení: ' + error.message, 'error');
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = 'Přihlásit se';
    }
}

async function logout() {
    try {
        await state.api.logout();
        state.currentUser = null;
        state.isAuthenticated = false;
        ui.setLoginState(false);
        ui.showToast('Odhlášen', 'info');
    } catch (error) {
        ui.showToast('Chyba při odhlášení', 'error');
    }
}

// Add to your setPhase function in ui.js or app.js
function setPhase(phase) {
    state.currentPhase = phase;
    ui.setPhase(phase);
    
    // Show/hide the no project selected message
    const noProjectMsg = document.getElementById('no-project-selected-message');
    if (noProjectMsg) {
        if (phase === 'expand' && (!state.currentProject || !state.currentProject.id)) {
            noProjectMsg.classList.remove('hidden');
        } else {
            noProjectMsg.classList.add('hidden');
        }
    }
    
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
    
    // Update the project status bar
    updateProjectStatusBar();
}

// Add this function to your ui.js file
function updateProjectStatusBar() {
    const projectNameEl = document.getElementById('current-project-name');
    const projectIdEl = document.getElementById('current-project-id');
    const phaseIndicatorEl = document.getElementById('current-phase-indicator');
    
    if (state.currentProject && state.currentProject.id) {
        projectNameEl.textContent = state.currentProject.title || 'Untitled Project';
        projectIdEl.textContent = `(ID: ${state.currentProject.id})`;
        
        // Change the color to indicate an active project
        projectNameEl.classList.remove('text-gray-500');
        projectNameEl.classList.add('text-blue-600');
    } else {
        projectNameEl.textContent = 'No project selected';
        projectIdEl.textContent = '';
        
        // Change the color to indicate no project is active
        projectNameEl.classList.remove('text-blue-600');
        projectNameEl.classList.add('text-gray-500');
    }
    
    // Update phase indicator
    if (phaseIndicatorEl) {
        phaseIndicatorEl.textContent = state.currentPhase || 'idea';
        
        // Update the styling based on the phase
        phaseIndicatorEl.className = 'px-2 py-1 rounded-full text-xs';
        
        switch (state.currentPhase) {
            case 'idea':
                phaseIndicatorEl.classList.add('bg-purple-100', 'text-purple-800');
                break;
            case 'expand':
                phaseIndicatorEl.classList.add('bg-blue-100', 'text-blue-800');
                break;
            case 'story':
                phaseIndicatorEl.classList.add('bg-green-100', 'text-green-800');
                break;
            default:
                phaseIndicatorEl.classList.add('bg-gray-100', 'text-gray-800');
        }
    }
}

async function selectProject(id) {
    await projectManager.selectProject(id);
    updateProjectStatusBar(); // Update the status bar after project selection
}

async function analyzeIdea() {
    const ideaText = ideaTextArea.value.trim();
    if (ideaText.length < 10) {
        ui.showToast('Nápad je příliš krátký.', 'warning');
        return;
    }

    ui.showLoading('AI analyzuje váš nápad...');
    try {
        const response = await state.api.analyzeIdea(ideaText, state.selectedStoryIntent);
        state.ideaAnalysisResults = response.analysis;
        const userResponse = await state.api.getCurrentUser();
        state.currentUser = userResponse.user;
        ui.updateTokenDisplay(state.currentUser);
        
        ui.displayIdeaAnalysis(state.ideaAnalysisResults);
        ui.prepareProjectCreation(state.ideaAnalysisResults);
        ui.showToast('Analýza dokončena!', 'success');
    } catch (error) {
        ui.showToast('Chyba AI analýzy: ' + error.message, 'error');
    } finally {
        ui.hideLoading();
    }
}

async function createProjectFromIdea() {
    if (!state.ideaAnalysisResults) {
        ui.showToast('Nejdříve analyzujte nápad.', 'warning');
        return;
    }
    
    const projectTitle = document.getElementById('project-title-input').value.trim();
    if (!projectTitle) {
        ui.showToast('Zadejte název projektu.', 'warning');
        return;
    }

    ui.showLoading('Vytvářím projekt...');
    try {
        const projectData = {
            project_title: projectTitle,
            project_description: document.getElementById('project-description-input').value.trim(),
            project_genre: document.getElementById('project-genre-input').value,
            story_intent: state.selectedStoryIntent,
            first_scene: state.ideaAnalysisResults.first_scene_suggestion,
            extracted_objects: state.ideaAnalysisResults.extracted_objects
        };
        const response = await state.api.createProjectFromIdea(projectData);
        
        const userResponse = await state.api.getCurrentUser();
        state.currentUser = userResponse.user;
        ui.updateTokenDisplay(state.currentUser);

        ui.showToast('Projekt úspěšně vytvořen!', 'success');
        if (response.project) {
            await loadProjects();
            await selectProject(response.project.id);
            setPhase('expand');
        }
    } catch (error) {
        ui.showToast('Chyba při vytváření projektu: ' + error.message, 'error');
    } finally {
        ui.hideLoading();
    }
}

async function retryConnection() {
    ui.showLoading('Zkouším se připojit...');
    const isOnline = await state.api.healthCheck();
    ui.hideLoading();
    if (isOnline) {
        ui.updateConnectionStatus(true);
        await checkAuthStatus();
        ui.showToast('Připojení obnoveno!', 'success');
    } else {
        ui.updateConnectionStatus(false);
        ui.showToast('Připojení se nezdařilo.', 'error');
    }
}

// Placeholder functions
async function loadProjects() { console.log("Načítání projektů..."); }
async function selectProject(id) { console.log(`Výběr projektu ${id}`); }
function createNewProject() { ui.showToast('Pro vytvoření projektu použijte fázi "Nápad"', 'info'); setPhase('idea'); }

// Phase management (delegated to UI, but called from app logic)
function setPhase(phase) {
    state.currentPhase = phase;
    ui.setPhase(phase);
    updateProjectStatusBar(); // Update the status bar when phase changes
}

// --- EVENT LISTENERS & INITIALIZATION ---
function setupEventListeners() {
    loginForm.addEventListener('submit', handleLogin);
    ideaTextArea.addEventListener('input', ui.updateCharCount);
    analyzeIdeaBtn.addEventListener('click', analyzeIdea);
    document.getElementById('create-project-btn').addEventListener('click', createProjectFromIdea);

    document.addEventListener('click', (e) => {
        const intentBtn = e.target.closest('.intent-btn');
        if (intentBtn) {
            document.querySelectorAll('.intent-btn').forEach(btn => btn.classList.remove('selected'));
            intentBtn.classList.add('selected');
            state.selectedStoryIntent = intentBtn.dataset.intent;
        }

        const templateCard = e.target.closest('[data-template]');
        if (templateCard) {
            const templates = {
                mystery: "Při úklidu po babičce najdu v její staré skřínce záhadný dopis...",
                relationship: "Můj nejlepší přítel mi během večeře prozradí, že má románek s mou sestrou...",
                adventure: "Probudím se v neznámém lese bez jakékoliv vzpomínky..."
            };
            ideaTextArea.value = templates[templateCard.dataset.template] || '';
            ui.updateCharCount();
            ui.showToast(`Template načten`, 'success');
        }
    });
}
// In your app.js or where you initialize everything
document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎭 StoryForge AI - Initializing...');
    ui.updateConnectionStatus(false);
    ui.connectionIndicator.textContent = '🔄 Připojuji...';
    
    // Initialize managers
    window.projectManager = new ProjectManager();
    window.expandManager = new ExpandPhaseManager();
    
    // Setup event listeners
    setupEventListeners();
    
    const isOnline = await state.api.healthCheck();
    if (isOnline) {
        await checkAuthStatus();
    } else {
        ui.updateConnectionStatus(false);
        document.getElementById('current-project-title').textContent = 'Problém s připojením k serveru';
    }
    
    // Initialize the status bar
    updateProjectStatusBar();
    
    setPhase('idea');
    console.log('✅ StoryForge AI - Initialized');
});