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