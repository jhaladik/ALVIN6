// This file represents the initial project structure and core files
// You would create this project using:
// npm create vite@latest storyforge-ai -- --template react-ts
// npm install -D tailwindcss postcss autoprefixer
// npx tailwindcss init -p
// npm install react-router-dom socket.io-client axios @headlessui/react @heroicons/react

// File: src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.tsx'
import { AuthProvider } from './context/AuthContext'
import { SocketProvider } from './context/SocketContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <SocketProvider>
          <App />
        </SocketProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)

// File: src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  color-scheme: light dark;
  background-color: #f9fafb;
  color: #1a1a1a;
}

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 
    focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors;
  }
  
  .btn-secondary {
    @apply px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300
    focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors;
  }

  .input-standard {
    @apply px-3 py-2 border border-gray-300 rounded-md shadow-sm
    focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 block w-full;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }
}

// File: src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Projects from './pages/Projects'
import ProjectDetail from './pages/ProjectDetail'
import Settings from './pages/Settings'
import Layout from './components/layout/Layout'
import NotFound from './pages/NotFound'
import { Suspense, lazy } from 'react'
import LoadingSpinner from './components/ui/LoadingSpinner'

// Lazy-loaded routes for better performance
const SceneEditor = lazy(() => import('./pages/SceneEditor'))
const StoryEditor = lazy(() => import('./pages/StoryEditor'))
const ObjectManager = lazy(() => import('./pages/ObjectManager'))
const AIWorkshop = lazy(() => import('./pages/AIWorkshop'))

function App() {
  const { isAuthenticated, isLoading } = useAuth()
  
  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/dashboard" />} />
      <Route path="/register" element={!isAuthenticated ? <Register /> : <Navigate to="/dashboard" />} />
      
      {/* Protected routes */}
      <Route element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/projects/:projectId" element={<ProjectDetail />} />
        <Route path="/projects/:projectId/scenes/:sceneId" element={
          <Suspense fallback={<LoadingSpinner />}>
            <SceneEditor />
          </Suspense>
        } />
        <Route path="/projects/:projectId/story" element={
          <Suspense fallback={<LoadingSpinner />}>
            <StoryEditor />
          </Suspense>
        } />
        <Route path="/projects/:projectId/objects" element={
          <Suspense fallback={<LoadingSpinner />}>
            <ObjectManager />
          </Suspense>
        } />
        <Route path="/projects/:projectId/ai" element={
          <Suspense fallback={<LoadingSpinner />}>
            <AIWorkshop />
          </Suspense>
        } />
        <Route path="/settings" element={<Settings />} />
      </Route>
      
      {/* Fallback routes */}
      <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default App

// File: src/context/AuthContext.tsx
import { createContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../services/api'

type User = {
  id: string
  email: string
  username: string
  plan: string
  tokensRemaining: number
  createdAt: string
}

type AuthContextType = {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  logout: async () => {},
})

type AuthProviderProps = {
  children: ReactNode
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is already logged in
    const checkAuthStatus = async () => {
      try {
        const { data } = await api.get('/api/auth/me')
        setUser(data)
      } catch (error) {
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
    
    checkAuthStatus()
  }, [])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const { data } = await api.post('/api/auth/login', { email, password })
      setUser(data)
    } catch (error) {
      throw new Error('Invalid credentials')
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (username: string, email: string, password: string) => {
    setIsLoading(true)
    try {
      const { data } = await api.post('/api/auth/register', { username, email, password })
      setUser(data)
    } catch (error) {
      throw new Error('Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await api.post('/api/auth/logout')
      setUser(null)
    } catch (error) {
      console.error('Logout failed', error)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// File: src/context/SocketContext.tsx
import { createContext, useEffect, useState, ReactNode } from 'react'
import { io, Socket } from 'socket.io-client'
import { useAuth } from '../hooks/useAuth'

type SocketContextType = {
  socket: Socket | null
  isConnected: boolean
  onlineUsers: string[]
}

export const SocketContext = createContext<SocketContextType>({
  socket: null,
  isConnected: false,
  onlineUsers: [],
})

type SocketProviderProps = {
  children: ReactNode
}

export const SocketProvider = ({ children }: SocketProviderProps) => {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [onlineUsers, setOnlineUsers] = useState<string[]>([])
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (!isAuthenticated) {
      // Clean up if not authenticated
      if (socket) {
        socket.disconnect()
        setSocket(null)
        setIsConnected(false)
        setOnlineUsers([])
      }
      return
    }

    // Initialize socket connection
    const socketInstance = io(import.meta.env.VITE_API_URL || 'http://localhost:5000', {
      withCredentials: true,
    })

    socketInstance.on('connect', () => {
      setIsConnected(true)
    })

    socketInstance.on('disconnect', () => {
      setIsConnected(false)
    })

    socketInstance.on('presence', (users: string[]) => {
      setOnlineUsers(users)
    })

    setSocket(socketInstance)

    return () => {
      socketInstance.disconnect()
    }
  }, [isAuthenticated])

  return (
    <SocketContext.Provider
      value={{
        socket,
        isConnected,
        onlineUsers,
      }}
    >
      {children}
    </SocketContext.Provider>
  )
}

// File: src/services/api.ts
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5000',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle authentication errors
    if (error.response && error.response.status === 401) {
      // Redirect to login if not authenticated
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// File: src/hooks/useAuth.ts
import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext'

export const useAuth = () => {
  return useContext(AuthContext)
}

// File: src/hooks/useSocket.ts
import { useContext } from 'react'
import { SocketContext } from '../context/SocketContext'

export const useSocket = () => {
  return useContext(SocketContext)
}

// File: src/components/layout/Layout.tsx
import { Outlet } from 'react-router-dom'
import { useState } from 'react'
import Sidebar from './Sidebar'
import Header from './Header'

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen)
  }
  
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isOpen={isSidebarOpen} />
      
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header toggleSidebar={toggleSidebar} />
        
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout

// File: src/components/layout/Sidebar.tsx
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import {
  HomeIcon,
  DocumentTextIcon,
  CogIcon,
  UserGroupIcon,
  SparklesIcon,
  FolderIcon,
  ArrowLeftOnRectangleIcon
} from '@heroicons/react/24/outline'

type SidebarProps = {
  isOpen: boolean
}

const Sidebar = ({ isOpen }: SidebarProps) => {
  const { user, logout } = useAuth()

  return (
    <div className={`bg-indigo-900 text-white transition-all duration-300 ${isOpen ? 'w-64' : 'w-20'}`}>
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center justify-center h-16 border-b border-indigo-800">
          <div className={`flex items-center ${isOpen ? 'justify-start pl-4' : 'justify-center'}`}>
            <SparklesIcon className="h-8 w-8 text-indigo-300" />
            {isOpen && <span className="ml-2 text-xl font-bold">StoryForge AI</span>}
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 py-4 overflow-y-auto">
          <ul className="space-y-2 px-2">
            <li>
              <NavLink 
                to="/dashboard" 
                className={({ isActive }) => 
                  `flex items-center py-2 px-4 rounded-md ${isActive ? 'bg-indigo-700' : 'hover:bg-indigo-800'}`
                }
              >
                <HomeIcon className="h-6 w-6" />
                {isOpen && <span className="ml-3">Dashboard</span>}
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/projects" 
                className={({ isActive }) => 
                  `flex items-center py-2 px-4 rounded-md ${isActive ? 'bg-indigo-700' : 'hover:bg-indigo-800'}`
                }
              >
                <FolderIcon className="h-6 w-6" />
                {isOpen && <span className="ml-3">Projects</span>}
              </NavLink>
            </li>
            <li>
              <NavLink 
                to="/settings" 
                className={({ isActive }) => 
                  `flex items-center py-2 px-4 rounded-md ${isActive ? 'bg-indigo-700' : 'hover:bg-indigo-800'}`
                }
              >
                <CogIcon className="h-6 w-6" />
                {isOpen && <span className="ml-3">Settings</span>}
              </NavLink>
            </li>
          </ul>
        </nav>
        
        {/* User info */}
        <div className="border-t border-indigo-800 p-4">
          <div className="flex items-center">
            <div className="h-10 w-10 rounded-full bg-indigo-600 flex items-center justify-center">
              <span className="text-white font-medium">
                {user?.username ? user.username[0].toUpperCase() : '?'}
              </span>
            </div>
            {isOpen && (
              <div className="ml-3 overflow-hidden">
                <p className="text-sm font-medium truncate">{user?.username}</p>
                <p className="text-xs text-indigo-300 truncate">{user?.email}</p>
                <p className="text-xs text-indigo-300 mt-1">
                  <span className="font-medium">{user?.tokensRemaining}</span> tokens left
                </p>
              </div>
            )}
          </div>
          
          <button 
            className="mt-4 w-full flex items-center justify-center py-2 px-4 rounded-md hover:bg-indigo-800 transition-colors"
            onClick={logout}
          >
            <ArrowLeftOnRectangleIcon className="h-5 w-5" />
            {isOpen && <span className="ml-2">Logout</span>}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Sidebar

// File: src/components/layout/Header.tsx
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Bars3Icon, BellIcon, MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useAuth } from '../../hooks/useAuth'
import { useSocket } from '../../hooks/useSocket'

type HeaderProps = {
  toggleSidebar: () => void
}

const Header = ({ toggleSidebar }: HeaderProps) => {
  const location = useLocation()
  const navigate = useNavigate()
  const { onlineUsers } = useSocket()
  const [searchQuery, setSearchQuery] = useState('')
  const [notificationsOpen, setNotificationsOpen] = useState(false)
  
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // Implement search functionality
    if (searchQuery.trim()) {
      navigate(`/projects?search=${encodeURIComponent(searchQuery)}`)
    }
  }
  
  // Get page title based on current route
  const getPageTitle = () => {
    const path = location.pathname
    if (path.includes('/dashboard')) return 'Dashboard'
    if (path.includes('/projects') && !path.includes('/scenes') && !path.includes('/story') && !path.includes('/objects') && !path.includes('/ai')) return 'Projects'
    if (path.includes('/scenes')) return 'Scene Editor'
    if (path.includes('/story')) return 'Story Editor'
    if (path.includes('/objects')) return 'Story Objects'
    if (path.includes('/ai')) return 'AI Workshop'
    if (path.includes('/settings')) return 'Settings'
    return 'StoryForge AI'
  }
  
  return (
    <header className="bg-white shadow-sm z-10">
      <div className="flex items-center justify-between h-16 px-4 md:px-6">
        <div className="flex items-center">
          <button
            type="button"
            className="text-gray-500 hover:text-gray-700 focus:outline-none"
            onClick={toggleSidebar}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          <h1 className="ml-4 text-lg font-medium text-gray-800">
            {getPageTitle()}
          </h1>
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Search bar - only show on certain pages */}
          {(location.pathname === '/projects' || location.pathname === '/dashboard') && (
            <form onSubmit={handleSearch} className="hidden md:block">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="search"
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white 
                  placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-indigo-500 
                  focus:ring-1 focus:ring-indigo-500"
                  placeholder="Search projects..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </form>
          )}
          
          {/* Notification bell */}
          <div className="relative">
            <button
              type="button"
              className="flex items-center text-gray-500 hover:text-gray-700 focus:outline-none"
              onClick={() => setNotificationsOpen(!notificationsOpen)}
            >
              <BellIcon className="h-6 w-6" />
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full flex items-center justify-center text-xs text-white">
                2
              </span>
            </button>
            
            {/* Dropdown menu */}
            {notificationsOpen && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg overflow-hidden z-20">
                <div className="py-2 px-4 bg-gray-50 text-sm font-medium text-gray-700 border-b border-gray-200 flex justify-between items-center">
                  <span>Notifications</span>
                  <button 
                    onClick={() => setNotificationsOpen(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
                <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                  <div className="px-4 py-3 hover:bg-gray-50">
                    <p className="text-sm font-medium text-gray-900">New comment on "Chapter 1"</p>
                    <p className="text-xs text-gray-500 mt-1">5 minutes ago</p>
                  </div>
                  <div className="px-4 py-3 hover:bg-gray-50">
                    <p className="text-sm font-medium text-gray-900">AI analysis completed</p>
                    <p className="text-xs text-gray-500 mt-1">1 hour ago</p>
                  </div>
                </div>
                <a
                  href="#"
                  className="block text-center py-2 text-sm text-indigo-600 bg-gray-50 hover:bg-gray-100 border-t border-gray-200"
                >
                  View all notifications
                </a>
              </div>
            )}
          </div>
          
          {/* Online users indicator */}
          <div className="flex items-center">
            <div className="relative flex -space-x-2">
              {onlineUsers.length > 0 ? (
                onlineUsers.slice(0, 3).map((user, index) => (
                  <div
                    key={index}
                    className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center border-2 border-white"
                    title={user}
                  >
                    <span className="text-white text-xs font-medium">{user[0]?.toUpperCase()}</span>
                  </div>
                ))
              ) : null}
              
              {onlineUsers.length > 3 && (
                <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center border-2 border-white">
                  <span className="text-gray-600 text-xs font-medium">+{onlineUsers.length - 3}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header

// File: src/components/ui/LoadingSpinner.tsx
type SpinnerSize = 'sm' | 'md' | 'lg'

type LoadingSpinnerProps = {
  size?: SpinnerSize
  className?: string
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
}

const LoadingSpinner = ({ size = 'md', className = '' }: LoadingSpinnerProps) => {
  return (
    <div className="flex justify-center items-center">
      <div
        className={`${sizeClasses[size]} ${className} animate-spin rounded-full border-4 border-gray-200 border-t-indigo-600`}
      ></div>
    </div>
  )
}

export default LoadingSpinner

// File: src/pages/Login.tsx
import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { SparklesIcon } from '@heroicons/react/24/outline'

const Login = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      await login(email, password)
      // Successful login will redirect via the App component
    } catch (err) {
      setError('Invalid email or password')
      setIsSubmitting(false)
    }
  }

  const handleDemoLogin = async () => {
    setEmail('demo@storyforge.ai')
    setPassword('demo123')
    setError('')
    setIsSubmitting(true)

    try {
      await login('demo@storyforge.ai', 'demo123')
      // Successful login will redirect via the App component
    } catch (err) {
      setError('Demo login failed. Please try again.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="card max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <SparklesIcon className="h-12 w-12 text-indigo-600" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Sign in to StoryForge AI
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Unleash your creative potential
          </p>
        </div>
        
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-standard mt-1"
                placeholder="your@email.com"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-standard mt-1"
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">
                Forgot your password?
              </a>
            </div>
          </div>

          <div className="space-y-3">
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full btn-primary flex justify-center items-center"
            >
              {isSubmitting ? <LoadingSpinner size="sm" /> : 'Sign in'}
            </button>
            
            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={isSubmitting}
              className="w-full btn-secondary flex justify-center"
            >
              Use demo account
            </button>
          </div>
        </form>
        
        <div className="text-center">
          <span className="text-gray-600 text-sm">
            Don't have an account?{' '}
            <Link to="/register" className="text-indigo-600 hover:text-indigo-500 font-medium">
              Register
            </Link>
          </span>
        </div>
      </div>
    </div>
  )
}

export default Login

// File: src/pages/Register.tsx
import { useState, FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { SparklesIcon } from '@heroicons/react/24/outline'

const Register = () => {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { register } = useAuth()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    
    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    
    setIsSubmitting(true)

    try {
      await register(username, email, password)
      // Successful register will redirect via the App component
    } catch (err) {
      setError('Registration failed. Please try a different email or username.')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="card max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <SparklesIcon className="h-12 w-12 text-indigo-600" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Join StoryForge AI and start creating
          </p>
        </div>
        
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-standard mt-1"
                placeholder="YourUsername"
              />
            </div>
            
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-standard mt-1"
                placeholder="your@email.com"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-standard mt-1"
              />
            </div>
            
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700">
                Confirm password
              </label>
              <input
                id="confirm-password"
                name="confirm-password"
                type="password"
                autoComplete="new-password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-standard mt-1"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full btn-primary flex justify-center items-center"
          >
            {isSubmitting ? <LoadingSpinner size="sm" /> : 'Create account'}
          </button>
        </form>
        
        <div className="text-center">
          <span className="text-gray-600 text-sm">
            Already have an account?{' '}
            <Link to="/login" className="text-indigo-600 hover:text-indigo-500 font-medium">
              Sign in
            </Link>
          </span>
        </div>
      </div>
    </div>
  )
}

export default Register

// File: src/pages/Dashboard.tsx
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { useAuth } from '../hooks/useAuth'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { 
  PlusIcon, 
  ClockIcon, 
  SparklesIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon 
} from '@heroicons/react/24/outline'

type RecentProject = {
  id: string
  title: string
  description: string
  phase: 'idea' | 'expand' | 'story'
  lastModified: string
  progress: number
}

type AITask = {
  id: string
  projectId: string
  projectTitle: string
  taskType: string
  status: 'completed' | 'in-progress' | 'failed'
  createdAt: string
}

const Dashboard = () => {
  const [recentProjects, setRecentProjects] = useState<RecentProject[]>([])
  const [aiTasks, setAiTasks] = useState<AITask[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const { user } = useAuth()
  
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [projectsResponse, tasksResponse] = await Promise.all([
          api.get('/api/projects?limit=5&sort=last_modified'),
          api.get('/api/ai/tasks?limit=3')
        ])
        
        setRecentProjects(projectsResponse.data)
        setAiTasks(tasksResponse.data)
      } catch (error) {
        console.error('Failed to load dashboard data', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadDashboardData()
  }, [])
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Welcome section */}
      <div className="card">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              Welcome back, {user?.username || 'Writer'}
            </h2>
            <p className="mt-1 text-gray-600">
              You have <span className="font-semibold">{user?.tokensRemaining}</span> tokens remaining on your {user?.plan || 'free'} plan.
            </p>
          </div>
          <Link to="/projects/new" className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-1" />
            New Project
          </Link>
        </div>
      </div>
      
      {/* Projects section */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Recent Projects</h3>
          <Link to="/projects" className="text-sm text-indigo-600 hover:text-indigo-500 font-medium">
            View all
          </Link>
        </div>
        
        {recentProjects.length > 0 ? (
          <div className="space-y-4">
            {recentProjects.map((project) => (
              <Link
                to={`/projects/${project.id}`}
                key={project.id}
                className="block border border-gray-200 rounded-md p-4 hover:bg-gray-50 transition"
              >
                <div className="flex justify-between">
                  <h4 className="text-md font-medium text-gray-800">{project.title}</h4>
                  <span className="text-xs inline-flex items-center px-2.5 py-0.5 rounded-full bg-indigo-100 text-indigo-800">
                    {project.phase === 'idea' && 'Idea Phase'}
                    {project.phase === 'expand' && 'Expand Phase'}
                    {project.phase === 'story' && 'Story Phase'}
                  </span>
                </div>
                <p className="mt-1 text-sm text-gray-600 line-clamp-2">{project.description}</p>
                <div className="mt-2 flex justify-between text-xs text-gray-500">
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    <span>
                      {new Date(project.lastModified).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full" 
                        style={{ width: `${project.progress}%` }}
                      ></div>
                    </div>
                    <span className="ml-2">{project.progress}%</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 border border-dashed border-gray-300 rounded-md">
            <SparklesIcon className="h-10 w-10 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No projects yet</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new project.</p>
            <div className="mt-4">
              <Link to="/projects/new" className="btn-primary inline-flex items-center">
                <PlusIcon className="h-5 w-5 mr-1" />
                New Project
              </Link>
            </div>
          </div>
        )}
      </div>
      
      {/* AI Tasks section */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-800">Recent AI Tasks</h3>
        </div>
        
        {aiTasks.length > 0 ? (
          <div className="space-y-4">
            {aiTasks.map((task) => (
              <div
                key={task.id}
                className="border border-gray-200 rounded-md p-4"
              >
                <div className="flex justify-between">
                  <div>
                    <h4 className="text-md font-medium text-gray-800">{task.taskType}</h4>
                    <p className="text-sm text-gray-600">Project: {task.projectTitle}</p>
                  </div>
                  <span className={`text-xs inline-flex items-center px-2.5 py-0.5 rounded-full ${
                    task.status === 'completed' ? 'bg-green-100 text-green-800' :
                    task.status === 'in-progress' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {task.status === 'completed' && (
                      <>
                        <CheckCircleIcon className="h-4 w-4 mr-1" />
                        Completed
                      </>
                    )}
                    {task.status === 'in-progress' && (
                      <>
                        <ClockIcon className="h-4 w-4 mr-1" />
                        In Progress
                      </>
                    )}
                    {task.status === 'failed' && (
                      <>
                        <ExclamationCircleIcon className="h-4 w-4 mr-1" />
                        Failed
                      </>
                    )}
                  </span>
                </div>
                <div className="mt-2 text-xs text-gray-500 flex items-center">
                  <ClockIcon className="h-4 w-4 mr-1" />
                  <span>{new Date(task.createdAt).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-6 border border-dashed border-gray-300 rounded-md">
            <SparklesIcon className="h-10 w-10 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No recent AI tasks</h3>
            <p className="mt-1 text-sm text-gray-500">AI tasks will appear here when you use AI features.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard

// File: src/pages/NotFound.tsx
import { Link } from 'react-router-dom'
import { FaceFrownIcon } from '@heroicons/react/24/outline'

const NotFound = () => {
  return (
    <div className="min-h-screen flex flex-col justify-center items-center px-4">
      <FaceFrownIcon className="h-16 w-16 text-indigo-600 mb-4" />
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Page not found</h1>
      <p className="text-lg text-gray-600 mb-8 text-center max-w-md">
        Sorry, we couldn't find the page you're looking for.
      </p>
      <Link to="/" className="btn-primary">
        Go back home
      </Link>
    </div>
  )
}

export default NotFound

// File: src/types/index.ts
// Define all types used across the application here
export type User = {
  id: string
  username: string
  email: string
  plan: string
  tokensRemaining: number
  createdAt: string
}

export type Project = {
  id: string
  title: string
  description: string
  phase: 'idea' | 'expand' | 'story'
  createdAt: string
  lastModified: string
  progress: number
  collaborators: string[]
}

export type Scene = {
  id: string
  projectId: string
  title: string
  content: string
  emotionalIntensity: number
  order: number
  characters: string[]
  locations: string[]
  props: string[]
  aiAnalysis?: AIAnalysis
  createdAt: string
  lastModified: string
}

export type StoryObject = {
  id: string
  projectId: string
  type: 'character' | 'location' | 'prop'
  name: string
  description: string
  attributes: Record<string, any>
  relationships: Relationship[]
}

export type Relationship = {
  targetId: string
  type: string
  description: string
}

export type AIAnalysis = {
  id: string
  targetId: string
  targetType: 'project' | 'scene' | 'object'
  criticType: string
  content: string
  createdAt: string
}

export type Comment = {
  id: string
  userId: string
  username: string
  targetId: string
  targetType: 'project' | 'scene' | 'object'
  content: string
  createdAt: string
}

export type Notification = {
  id: string
  userId: string
  type: string
  message: string
  read: boolean
  targetId?: string
  targetType?: 'project' | 'scene' | 'comment'
  createdAt: string
}

// File: src/components/ui/Button.tsx
import { ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'success' | 'danger' | 'ghost'
type ButtonSize = 'sm' | 'md' | 'lg'

type ButtonProps = {
  children: ReactNode
  variant?: ButtonVariant
  size?: ButtonSize
  isLoading?: boolean
  disabled?: boolean
  className?: string
  onClick?: () => void
  type?: 'button' | 'submit' | 'reset'
}

const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  className = '',
  onClick,
  type = 'button',
}: ButtonProps) => {
  const variantClasses = {
    primary: 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500',
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  }

  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center rounded-md font-medium transition-colors 
                 focus:outline-none focus:ring-2 focus:ring-offset-2
                 ${variantClasses[variant]} 
                 ${sizeClasses[size]}
                 ${disabled || isLoading ? 'opacity-60 cursor-not-allowed' : ''}
                 ${className}`}
      onClick={onClick}
      disabled={disabled || isLoading}
    >
      {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : null}
      {children}
    </button>
  )
}

export default Button

// Add more components as needed for the project