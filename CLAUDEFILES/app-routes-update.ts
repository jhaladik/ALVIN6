// src/App.tsx
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';

// Layout components
import MainLayout from './components/layout/MainLayout';
import AuthLayout from './components/layout/AuthLayout';

// Auth components
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import ForgotPassword from './components/auth/ForgotPassword';

// Core pages
import Dashboard from './components/pages/Dashboard';
import ProjectDetail from './components/pages/ProjectDetail';
import SceneManager from './components/pages/SceneManager';
import SceneEditor from './components/pages/SceneEditor';

// New AI Features page
import AIFeaturesPage from './components/pages/AIFeaturesPage';

// Settings pages
import SettingsProfile from './components/settings/SettingsProfile';
import SettingsBilling from './components/settings/SettingsBilling';
import SettingsNotifications from './components/settings/SettingsNotifications';

// Context providers
import { AuthProvider } from './context/AuthContext';
import { SocketProvider } from './context/SocketContext';

// Error and loading states
import LoadingScreen from './components/ui/LoadingScreen';
import ErrorBoundary from './components/ui/ErrorBoundary';

// Protected route component
import ProtectedRoute from './components/auth/ProtectedRoute';

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <SocketProvider>
          <Router>
            <Suspense fallback={<LoadingScreen />}>
              <Routes>
                {/* Auth routes */}
                <Route element={<AuthLayout />}>
                  <Route path="/login" element={<Login />} />
                  <Route path="/register" element={<Register />} />
                  <Route path="/forgot-password" element={<ForgotPassword />} />
                </Route>

                {/* Protected routes */}
                <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/projects" element={<Dashboard />} />
                  <Route path="/projects/:projectId" element={<ProjectDetail />} />
                  
                  {/* Scene management */}
                  <Route path="/projects/:projectId/scenes" element={<SceneManager />} />
                  <Route path="/projects/:projectId/scenes/:sceneId" element={<SceneEditor />} />
                  
                  {/* AI Features */}
                  <Route path="/projects/:projectId/ai" element={<AIFeaturesPage />} />
                  
                  {/* Settings */}
                  <Route path="/settings/profile" element={<SettingsProfile />} />
                  <Route path="/settings/billing" element={<SettingsBilling />} />
                  <Route path="/settings/notifications" element={<SettingsNotifications />} />
                </Route>

                {/* Redirect to dashboard if already logged in */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Suspense>
          </Router>
        </SocketProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
