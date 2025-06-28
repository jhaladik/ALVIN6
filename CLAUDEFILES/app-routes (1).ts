// src/App.tsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Auth & Context Providers
import { AuthProvider } from './context/AuthContext';
import { SocketProvider } from './context/SocketContext';
import { ToastProvider } from './context/ToastContext';

// Layout Components
import Layout from './components/layout/Layout';
import PrivateRoute from './components/auth/PrivateRoute';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ProjectList from './pages/ProjectList';
import ProjectDetail from './pages/ProjectDetail';
import SceneManager from './pages/SceneManager';
import SceneEditor from './pages/SceneEditor';
import ObjectManager from './pages/ObjectManager';
import AIFeatures from './pages/AIFeatures';
import StoryPhase from './pages/StoryPhase';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <SocketProvider>
          <ToastProvider>
            <Routes>
              {/* Public Routes */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              
              {/* Protected Routes */}
              <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
                <Route index element={<Dashboard />} />
                <Route path="projects" element={<ProjectList />} />
                <Route path="projects/:projectId" element={<ProjectDetail />} />
                <Route path="projects/:projectId/scenes" element={<SceneManager />} />
                <Route path="projects/:projectId/scenes/:sceneId" element={<SceneEditor />} />
                <Route path="projects/:projectId/objects" element={<ObjectManager />} />
                <Route path="projects/:projectId/ai" element={<AIFeatures />} />
                
                {/* Story Phase Route */}
                <Route path="projects/:projectId/story" element={<StoryPhase />} />
                
                <Route path="settings" element={<Settings />} />
              </Route>
              
              {/* Fallback Routes */}
              <Route path="/404" element={<NotFound />} />
              <Route path="*" element={<Navigate to="/404" replace />} />
            </Routes>
          </ToastProvider>
        </SocketProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;

// src/components/layout/Sidebar.tsx (add Story Phase navigation item)
import React from 'react';
import { NavLink, useParams } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  BookOpenIcon,
  UserGroupIcon,
  AdjustmentsIcon,
  SparklesIcon,
  PuzzlePieceIcon,
  ViewListIcon,
} from '@heroicons/react/24/outline';

interface SidebarProps {
  isCollapsed: boolean;
  toggleSidebar: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, toggleSidebar }) => {
  const { projectId } = useParams<{ projectId: string }>();
  
  const mainNavItems = [
    { to: '/', icon: HomeIcon, label: 'Dashboard' },
    { to: '/projects', icon: DocumentTextIcon, label: 'Projects' }
  ];
  
  const projectNavItems = projectId ? [
    { to: `/projects/${projectId}`, icon: DocumentTextIcon, label: 'Overview' },
    { to: `/projects/${projectId}/scenes`, icon: ViewListIcon, label: 'Scenes' },
    { to: `/projects/${projectId}/objects`, icon: PuzzlePieceIcon, label: 'Objects' },
    { to: `/projects/${projectId}/ai`, icon: SparklesIcon, label: 'AI Features' },
    // Add Story Phase link
    { to: `/projects/${projectId}/story`, icon: BookOpenIcon, label: 'Story' },
    { to: `/projects/${projectId}/collaboration`, icon: UserGroupIcon, label: 'Collaboration' }
  ] : [];
  
  const bottomNavItems = [
    { to: '/settings', icon: AdjustmentsIcon, label: 'Settings' }
  ];
  
  const renderNavItem = (item: any, index: number) => (
    <NavLink
      key={index}
      to={item.to}
      className={({ isActive }) => `
        flex items-center px-4 py-2 my-1 rounded-lg transition-colors
        ${isActive
          ? 'bg-indigo-100 text-indigo-700'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        }
      `}
    >
      <item.icon className="h-5 w-5 mr-3" />
      {!isCollapsed && <span>{item.label}</span>}
    </NavLink>
  );
  
  return (
    <aside className={`
      flex flex-col bg-white border-r border-gray-200 h-screen transition-all
      ${isCollapsed ? 'w-16' : 'w-64'}
    `}>
      {/* Logo & Toggle */}
      <div className="p-4 flex items-center justify-between border-b border-gray-200">
        {!isCollapsed && <h1 className="text-xl font-bold text-indigo-600">StoryForge AI</h1>}
        <button
          onClick={toggleSidebar}
          className="p-1 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200"
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>
      
      {/* Main Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {mainNavItems.map(renderNavItem)}
        
        {/* Project Navigation (only if in a project) */}
        {projectNavItems.length > 0 && (
          <>
            <div className="my-4 border-t border-gray-200"></div>
            <div className="px-4 mb-2 text-xs font-semibold text-gray-500 uppercase">
              {!isCollapsed && 'Current Project'}
            </div>
            {projectNavItems.map(renderNavItem)}
          </>
        )}
      </nav>
      
      {/* Bottom Navigation */}
      <div className="px-2 py-4 border-t border-gray-200">
        {bottomNavItems.map(renderNavItem)}
      </div>
    </aside>
  );
};

export default Sidebar;

// Update ProjectDetail.tsx to add a link to the Story Phase
// Add this button to the actions section of ProjectDetail.tsx

{/* Story Phase button */}
<Link to={`/projects/${projectId}/story`}>
  <Button variant="secondary" className="flex items-center">
    <BookOpenIcon className="h-5 w-5 mr-2" />
    Story Phase
  </Button>
</Link>
