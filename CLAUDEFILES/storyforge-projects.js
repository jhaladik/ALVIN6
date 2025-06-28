// File: src/pages/Projects.tsx
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { Project } from '../types'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import Button from '../components/ui/Button'
import ProjectCard from '../components/projects/ProjectCard'
import ProjectFilter from '../components/projects/ProjectFilter'
import CreateProjectModal from '../components/projects/CreateProjectModal'
import { useSearchParams } from 'react-router-dom'
import {
  PlusIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

type ProjectsFilterType = 'all' | 'recent' | 'idea' | 'expand' | 'story'
type ProjectsSortType = 'newest' | 'oldest' | 'updated' | 'alphabetical'

const Projects = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [activeFilter, setActiveFilter] = useState<ProjectsFilterType>('all')
  const [activeSort, setActiveSort] = useState<ProjectsSortType>('updated')
  const [searchParams, setSearchParams] = useSearchParams()
  const searchQuery = searchParams.get('search') || ''
  
  useEffect(() => {
    const loadProjects = async () => {
      try {
        setIsLoading(true)
        const response = await api.get('/api/projects')
        setProjects(response.data)
      } catch (err) {
        console.error('Failed to load projects', err)
        setError('Failed to load projects. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }
    
    loadProjects()
  }, [])
  
  // Filter and sort projects whenever these values change
  useEffect(() => {
    let result = [...projects]
    
    // Apply search filter if present
    if (searchQuery) {
      result = result.filter(p => 
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
        p.description.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }
    
    // Apply phase filter
    if (activeFilter !== 'all' && activeFilter !== 'recent') {
      result = result.filter(p => p.phase === activeFilter)
    } else if (activeFilter === 'recent') {
      // Show last 5 modified projects
      result = result.sort((a, b) => 
        new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime()
      ).slice(0, 5)
    }
    
    // Apply sorting
    result = sortProjects(result, activeSort)
    
    setFilteredProjects(result)
  }, [projects, activeFilter, activeSort, searchQuery])
  
  const sortProjects = (projects: Project[], sortType: ProjectsSortType): Project[] => {
    switch (sortType) {
      case 'newest':
        return [...projects].sort((a, b) => 
          new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
        )
      case 'oldest':
        return [...projects].sort((a, b) => 
          new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
        )
      case 'updated':
        return [...projects].sort((a, b) => 
          new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime()
        )
      case 'alphabetical':
        return [...projects].sort((a, b) => a.title.localeCompare(b.title))
      default:
        return projects
    }
  }
  
  const handleCreateProject = async (project: { title: string; description: string }) => {
    try {
      setIsLoading(true)
      const response = await api.post('/api/projects', project)
      setProjects(prevProjects => [...prevProjects, response.data])
      setIsCreateModalOpen(false)
    } catch (err) {
      console.error('Failed to create project', err)
      setError('Failed to create project. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }
  
  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return
    }
    
    try {
      await api.delete(`/api/projects/${projectId}`)
      setProjects(prevProjects => prevProjects.filter(p => p.id !== projectId))
    } catch (err) {
      console.error('Failed to delete project', err)
      setError('Failed to delete project. Please try again.')
    }
  }
  
  const handleSearch = (query: string) => {
    if (query) {
      setSearchParams({ search: query })
    } else {
      setSearchParams({})
    }
  }
  
  if (isLoading && projects.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      
      {/* Projects header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Your Projects</h1>
          <p className="text-gray-600">Manage all your writing projects</p>
        </div>
        
        <div className="flex gap-2">
          <div className="relative">
            <input
              type="search"
              placeholder="Search projects..."
              className="input-standard pl-10"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
            />
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
            </div>
          </div>
          
          <Button 
            onClick={() => setIsCreateModalOpen(true)}
            className="whitespace-nowrap"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            New Project
          </Button>
        </div>
      </div>
      
      {/* Filters */}
      <ProjectFilter 
        activeFilter={activeFilter}
        setActiveFilter={setActiveFilter}
        activeSort={activeSort}
        setActiveSort={setActiveSort}
      />
      
      {/* Projects grid */}
      {filteredProjects.length > 0 ? (
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              onDelete={() => handleDeleteProject(project.id)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 border border-dashed border-gray-300 rounded-md">
          <SparklesIcon className="h-12 w-12 text-gray-400 mx-auto" />
          <h3 className="mt-4 text-sm font-medium text-gray-900">
            {searchQuery 
              ? 'No projects match your search' 
              : projects.length === 0 
                ? 'No projects yet' 
                : 'No projects match your filter'}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery 
              ? 'Try a different search term' 
              : projects.length === 0 
                ? 'Get started by creating a new project' 
                : 'Try a different filter'}
          </p>
          {!searchQuery && projects.length === 0 && (
            <div className="mt-6">
              <Button onClick={() => setIsCreateModalOpen(true)}>
                <PlusIcon className="h-5 w-5 mr-1" />
                Create New Project
              </Button>
            </div>
          )}
        </div>
      )}
      
      {/* Create project modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateProject}
      />
    </div>
  )
}

export default Projects

// File: src/components/projects/ProjectCard.tsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Project } from '../../types'
import { 
  PencilIcon, 
  TrashIcon, 
  EllipsisVerticalIcon,
  ClockIcon,
  UserGroupIcon,
} from '@heroicons/react/24/outline'
import { Menu } from '@headlessui/react'

type ProjectCardProps = {
  project: Project
  onDelete: () => void
}

const ProjectCard = ({ project, onDelete }: ProjectCardProps) => {
  const [isHovered, setIsHovered] = useState(false)
  
  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'idea':
        return 'bg-blue-100 text-blue-800'
      case 'expand':
        return 'bg-purple-100 text-purple-800'
      case 'story':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }
  
  const formatLastModified = (date: string) => {
    const now = new Date()
    const modifiedDate = new Date(date)
    const diffTime = Math.abs(now.getTime() - modifiedDate.getTime())
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      return 'Today'
    } else if (diffDays === 1) {
      return 'Yesterday'
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else if (diffDays < 30) {
      return `${Math.floor(diffDays / 7)} weeks ago`
    } else {
      return modifiedDate.toLocaleDateString()
    }
  }
  
  return (
    <div
      className="card hover:shadow-md transition-shadow relative"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Card menu */}
      <Menu as="div" className="absolute top-3 right-3 z-10">
        <Menu.Button className="flex items-center justify-center h-8 w-8 rounded-full hover:bg-gray-100">
          <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
        </Menu.Button>
        <Menu.Items className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg z-10 border border-gray-200 divide-y divide-gray-100">
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <Link
                  to={`/projects/${project.id}/edit`}
                  className={`${
                    active ? 'bg-gray-100' : ''
                  } flex items-center px-4 py-2 text-sm text-gray-700 w-full text-left`}
                >
                  <PencilIcon className="h-4 w-4 mr-2" />
                  Edit Project
                </Link>
              )}
            </Menu.Item>
          </div>
          <div className="py-1">
            <Menu.Item>
              {({ active }) => (
                <button
                  onClick={onDelete}
                  className={`${
                    active ? 'bg-red-50' : ''
                  } flex items-center px-4 py-2 text-sm text-red-600 w-full text-left`}
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete Project
                </button>
              )}
            </Menu.Item>
          </div>
        </Menu.Items>
      </Menu>

      {/* Phase badge */}
      <div className={`absolute top-3 left-3 text-xs font-medium px-2 py-1 rounded-full ${getPhaseColor(project.phase)}`}>
        {project.phase === 'idea' && 'Idea Phase'}
        {project.phase === 'expand' && 'Expand Phase'}
        {project.phase === 'story' && 'Story Phase'}
      </div>
      
      {/* Card content */}
      <div className="pt-10"> {/* Add padding to account for the absolute positioned elements */}
        <Link to={`/projects/${project.id}`} className="block">
          <h3 className="text-lg font-medium text-gray-900 line-clamp-2">{project.title}</h3>
          <p className="mt-2 text-sm text-gray-600 line-clamp-3">{project.description}</p>
          
          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>Progress</span>
              <span>{project.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-indigo-600 h-2 rounded-full" 
                style={{ width: `${project.progress}%` }}
              ></div>
            </div>
          </div>
          
          {/* Metadata */}
          <div className="mt-4 pt-4 border-t border-gray-100 flex justify-between text-xs text-gray-500">
            <div className="flex items-center">
              <ClockIcon className="h-4 w-4 mr-1" />
              {formatLastModified(project.lastModified)}
            </div>
            
            {project.collaborators.length > 0 && (
              <div className="flex items-center">
                <UserGroupIcon className="h-4 w-4 mr-1" />
                {project.collaborators.length} 
                {project.collaborators.length === 1 ? ' collaborator' : ' collaborators'}
              </div>
            )}
          </div>
        </Link>
      </div>
    </div>
  )
}

export default ProjectCard

// File: src/components/projects/ProjectFilter.tsx
type ProjectsFilterType = 'all' | 'recent' | 'idea' | 'expand' | 'story'
type ProjectsSortType = 'newest' | 'oldest' | 'updated' | 'alphabetical'

type ProjectFilterProps = {
  activeFilter: ProjectsFilterType
  setActiveFilter: (filter: ProjectsFilterType) => void
  activeSort: ProjectsSortType
  setActiveSort: (sort: ProjectsSortType) => void
}

const ProjectFilter = ({
  activeFilter,
  setActiveFilter,
  activeSort,
  setActiveSort,
}: ProjectFilterProps) => {
  return (
    <div className="flex flex-col sm:flex-row justify-between space-y-4 sm:space-y-0 sm:items-center">
      {/* Filters */}
      <div className="flex space-x-2 overflow-x-auto pb-2 sm:pb-0">
        <button
          className={`px-3 py-1.5 text-sm rounded-full ${
            activeFilter === 'all'
              ? 'bg-indigo-100 text-indigo-800'
              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
          }`}
          onClick={() => setActiveFilter('all')}
        >
          All Projects
        </button>
        <button
          className={`px-3 py-1.5 text-sm rounded-full ${
            activeFilter === 'recent'
              ? 'bg-indigo-100 text-indigo-800'
              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
          }`}
          onClick={() => setActiveFilter('recent')}
        >
          Recent
        </button>
        <button
          className={`px-3 py-1.5 text-sm rounded-full ${
            activeFilter === 'idea'
              ? 'bg-blue-100 text-blue-800'
              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
          }`}
          onClick={() => setActiveFilter('idea')}
        >
          Idea Phase
        </button>
        <button
          className={`px-3 py-1.5 text-sm rounded-full ${
            activeFilter === 'expand'
              ? 'bg-purple-100 text-purple-800'
              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
          }`}
          onClick={() => setActiveFilter('expand')}
        >
          Expand Phase
        </button>
        <button
          className={`px-3 py-1.5 text-sm rounded-full ${
            activeFilter === 'story'
              ? 'bg-green-100 text-green-800'
              : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
          }`}
          onClick={() => setActiveFilter('story')}
        >
          Story Phase
        </button>
      </div>
      
      {/* Sort */}
      <div className="flex items-center">
        <label htmlFor="sort" className="text-sm font-medium text-gray-700 mr-2">
          Sort by:
        </label>
        <select
          id="sort"
          value={activeSort}
          onChange={(e) => setActiveSort(e.target.value as ProjectsSortType)}
          className="input-standard py-1.5 pl-3 pr-10 text-sm"
        >
          <option value="updated">Last Updated</option>
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="alphabetical">Alphabetical</option>
        </select>
      </div>
    </div>
  )
}

export default ProjectFilter

// File: src/components/projects/CreateProjectModal.tsx
import { useState, FormEvent } from 'react'
import { Dialog } from '@headlessui/react'
import Button from '../ui/Button'
import { XMarkIcon } from '@heroicons/react/24/outline'

type CreateProjectModalProps = {
  isOpen: boolean
  onClose: () => void
  onSubmit: (project: { title: string; description: string }) => void
}

const CreateProjectModal = ({ isOpen, onClose, onSubmit }: CreateProjectModalProps) => {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    onSubmit({ 
      title: title.trim(), 
      description: description.trim() 
    })
    
    // Reset form after submission
    setTitle('')
    setDescription('')
    setIsSubmitting(false)
  }
  
  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      {/* Full-screen container to center the panel */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-white rounded-lg shadow-xl max-w-md w-full">
          <div className="flex justify-between items-start p-4 border-b border-gray-200">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Create New Project
            </Dialog.Title>
            <button
              className="text-gray-400 hover:text-gray-500"
              onClick={onClose}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="p-4 space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Project Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input-standard mt-1"
                  placeholder="My Amazing Story"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="input-standard mt-1"
                  placeholder="A brief description of your project..."
                />
              </div>
              
              <div className="text-xs text-gray-500">
                <p>
                  All new projects start in the <span className="font-medium">Idea Phase</span>. 
                  You can advance to later phases as your project develops.
                </p>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 p-4 border-t border-gray-200">
              <Button 
                variant="secondary" 
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={!title.trim() || isSubmitting}
                isLoading={isSubmitting}
              >
                Create Project
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}

export default CreateProjectModal

// File: src/pages/ProjectDetail.tsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { api } from '../services/api'
import { Project, Scene } from '../types'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import Button from '../components/ui/Button'
import {
  ArrowPathIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  UserPlusIcon,
  ChatBubbleBottomCenterTextIcon,
  ArrowRightIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import ProjectDetailTabs from '../components/projects/ProjectDetailTabs'
import EditProjectModal from '../components/projects/EditProjectModal'
import InviteCollaboratorModal from '../components/projects/InviteCollaboratorModal'

type ActiveTabType = 'overview' | 'scenes' | 'objects' | 'ai'

const ProjectDetail = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [project, setProject] = useState<Project | null>(null)
  const [scenes, setScenes] = useState<Scene[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<ActiveTabType>('overview')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false)
  
  useEffect(() => {
    const loadProjectDetails = async () => {
      if (!projectId) return
      
      try {
        setIsLoading(true)
        const [projectResponse, scenesResponse] = await Promise.all([
          api.get(`/api/projects/${projectId}`),
          api.get(`/api/scenes?projectId=${projectId}`)
        ])
        
        setProject(projectResponse.data)
        setScenes(scenesResponse.data)
      } catch (err) {
        console.error('Failed to load project details', err)
        setError('Failed to load project details. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }
    
    loadProjectDetails()
  }, [projectId])
  
  const handleUpdateProject = async (updatedProject: { title: string; description: string }) => {
    if (!project) return
    
    try {
      const response = await api.put(`/api/projects/${project.id}`, updatedProject)
      setProject(response.data)
      setIsEditModalOpen(false)
    } catch (err) {
      console.error('Failed to update project', err)
      setError('Failed to update project. Please try again.')
    }
  }
  
  const handleDeleteProject = async () => {
    if (!project) return
    
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return
    }
    
    try {
      await api.delete(`/api/projects/${project.id}`)
      navigate('/projects')
    } catch (err) {
      console.error('Failed to delete project', err)
      setError('Failed to delete project. Please try again.')
    }
  }
  
  const advanceProjectPhase = async () => {
    if (!project) return
    
    const phases = ['idea', 'expand', 'story']
    const currentPhaseIndex = phases.indexOf(project.phase)
    
    if (currentPhaseIndex >= phases.length - 1) {
      return // Already in the final phase
    }
    
    const nextPhase = phases[currentPhaseIndex + 1]
    
    try {
      const response = await api.patch(`/api/projects/${project.id}/phase`, { phase: nextPhase })
      setProject(response.data)
    } catch (err) {
      console.error('Failed to advance project phase', err)
      setError('Failed to advance project phase. Please try again.')
    }
  }
  
  const inviteCollaborator = async (email: string) => {
    if (!project) return
    
    try {
      await api.post(`/api/collaboration/invite`, {
        projectId: project.id,
        email
      })
      
      // Reload project to get updated collaborators list
      const { data } = await api.get(`/api/projects/${project.id}`)
      setProject(data)
      
      setIsInviteModalOpen(false)
    } catch (err) {
      console.error('Failed to invite collaborator', err)
      setError('Failed to invite collaborator. Please try again.')
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  if (!project && !isLoading) {
    return (
      <div className="text-center py-12">
        <ExclamationCircleIcon className="h-12 w-12 text-red-500 mx-auto" />
        <h2 className="mt-4 text-lg font-medium text-gray-900">Project not found</h2>
        <p className="mt-2 text-gray-600">This project may have been deleted or you don't have access.</p>
        <Link to="/projects" className="mt-4 inline-block btn-primary">
          Back to Projects
        </Link>
      </div>
    )
  }
  
  return (
    <div>
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      
      {/* Project header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-gray-900">{project?.title}</h1>
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${
              project?.phase === 'idea' ? 'bg-blue-100 text-blue-800' :
              project?.phase === 'expand' ? 'bg-purple-100 text-purple-800' :
              'bg-green-100 text-green-800'
            }`}>
              {project?.phase === 'idea' && 'Idea Phase'}
              {project?.phase === 'expand' && 'Expand Phase'}
              {project?.phase === 'story' && 'Story Phase'}
            </span>
          </div>
          <p className="text-gray-600 mt-1">{project?.description}</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {/* Action buttons */}
          <Button onClick={() => setIsEditModalOpen(true)}>
            <PencilIcon className="h-5 w-5 mr-1" />
            Edit
          </Button>
          
          <Button onClick={() => setIsInviteModalOpen(true)}>
            <UserPlusIcon className="h-5 w-5 mr-1" />
            Invite
          </Button>
          
          {project?.phase !== 'story' && (
            <Button onClick={advanceProjectPhase}>
              <ArrowRightIcon className="h-5 w-5 mr-1" />
              {project?.phase === 'idea' ? 'Expand' : 'Write Story'}
            </Button>
          )}
          
          <Button variant="danger" onClick={handleDeleteProject}>
            <TrashIcon className="h-5 w-5 mr-1" />
            Delete
          </Button>
        </div>
      </div>
      
      {/* Tabs */}
      <ProjectDetailTabs activeTab={activeTab} setActiveTab={setActiveTab} />
      
      {/* Tab content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Project Summary</h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Created</h4>
                  <p className="text-gray-600">{new Date(project?.createdAt || '').toLocaleDateString()}</p>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Last Modified</h4>
                  <p className="text-gray-600">{new Date(project?.lastModified || '').toLocaleString()}</p>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Progress</h4>
                  <div className="mt-1">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-indigo-600 h-2 rounded-full" 
                        style={{ width: `${project?.progress || 0}%` }}
                      ></div>
                    </div>
                    <p className="text-right text-xs text-gray-500 mt-1">{project?.progress || 0}% complete</p>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Collaborators</h4>
                  {project?.collaborators && project.collaborators.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {project.collaborators.map((collaborator, index) => (
                        <div key={index} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {collaborator}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-600">No collaborators yet</p>
                  )}
                </div>
              </div>
            </div>
            
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Stats</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Scenes</p>
                  <p className="mt-1 text-2xl font-semibold text-gray-900">{scenes.length}</p>
                </div>
                
                <div className="border rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Characters</p>
                  <p className="mt-1 text-2xl font-semibold text-gray-900">
                    {/* This would be calculated from story objects API */}
                    0
                  </p>
                </div>
                
                <div className="border rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Locations</p>
                  <p className="mt-1 text-2xl font-semibold text-gray-900">
                    {/* This would be calculated from story objects API */}
                    0
                  </p>
                </div>
                
                <div className="border rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-500">Words</p>
                  <p className="mt-1 text-2xl font-semibold text-gray-900">
                    {/* This would be calculated from scenes content */}
                    0
                  </p>
                </div>
              </div>
              
              <div className="mt-6 flex justify-center">
                <Button
                  variant="secondary"
                  size="sm"
                  className="w-full"
                  onClick={() => window.location.reload()}
                >
                  <ArrowPathIcon className="h-4 w-4 mr-1" />
                  Refresh Stats
                </Button>
              </div>
            </div>
            
            <div className="card md:col-span-2">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Recent Scenes</h3>
                <Link 
                  to={`/projects/${project?.id}/scenes/new`} 
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                >
                  Add Scene
                </Link>
              </div>
              
              {scenes.length > 0 ? (
                <div className="space-y-4">
                  {scenes.slice(0, 3).map(scene => (
                    <Link
                      to={`/projects/${project?.id}/scenes/${scene.id}`}
                      key={scene.id}
                      className="block border border-gray-200 rounded-md p-4 hover:bg-gray-50 transition"
                    >
                      <h4 className="font-medium text-gray-900">{scene.title}</h4>
                      <p className="text-sm text-gray-600 line-clamp-2 mt-1">{scene.content}</p>
                      <div className="mt-2 text-xs text-gray-500 flex justify-between">
                        <span>Order: {scene.order}</span>
                        <span>Last modified: {new Date(scene.lastModified).toLocaleDateString()}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 border border-dashed border-gray-300 rounded-md">
                  <h3 className="text-sm font-medium text-gray-900">No scenes yet</h3>
                  <p className="mt-1 text-sm text-gray-500">Create your first scene to get started.</p>
                  <div className="mt-4">
                    <Link 
                      to={`/projects/${project?.id}/scenes/new`}
                      className="btn-primary inline-flex items-center"
                    >
                      <PlusIcon className="h-5 w-5 mr-1" />
                      Create Scene
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {activeTab === 'scenes' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">All Scenes</h3>
              <Link 
                to={`/projects/${project?.id}/scenes/new`} 
                className="btn-primary inline-flex items-center"
              >
                <PlusIcon className="h-5 w-5 mr-1" />
                Create Scene
              </Link>
            </div>
            
            {scenes.length > 0 ? (
              <div className="space-y-4">
                {scenes.map(scene => (
                  <Link
                    to={`/projects/${project?.id}/scenes/${scene.id}`}
                    key={scene.id}
                    className="block border border-gray-200 rounded-md p-4 hover:bg-gray-50 transition"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">{scene.title}</h4>
                        <p className="text-sm text-gray-600 line-clamp-2 mt-1">{scene.content}</p>
                      </div>
                      <div className="text-lg font-bold text-indigo-600 bg-indigo-50 h-8 w-8 rounded-full flex items-center justify-center">
                        {scene.order}
                      </div>
                    </div>
                    <div className="mt-4 text-xs text-gray-500 flex justify-between">
                      <div className="flex items-center">
                        <ChatBubbleBottomCenterTextIcon className="h-4 w-4 mr-1" />
                        {scene.characters.length} characters
                      </div>
                      <span>
                        Emotional Intensity: {scene.emotionalIntensity}/10
                      </span>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-16 border border-dashed border-gray-300 rounded-md">
                <h3 className="text-sm font-medium text-gray-900">No scenes yet</h3>
                <p className="mt-1 text-sm text-gray-500">Create your first scene to get started.</p>
                <div className="mt-4">
                  <Link 
                    to={`/projects/${project?.id}/scenes/new`}
                    className="btn-primary inline-flex items-center"
                  >
                    <PlusIcon className="h-5 w-5 mr-1" />
                    Create Scene
                  </Link>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Additional tabs (objects, AI) would go here */}
      </div>
      
      {/* Modals */}
      {project && (
        <>
          <EditProjectModal
            isOpen={isEditModalOpen}
            onClose={() => setIsEditModalOpen(false)}
            onSubmit={handleUpdateProject}
            project={project}
          />
          
          <InviteCollaboratorModal
            isOpen={isInviteModalOpen}
            onClose={() => setIsInviteModalOpen(false)}
            onSubmit={inviteCollaborator}
            projectTitle={project.title}
          />
        </>
      )}
    </div>
  )
}

export default ProjectDetail

// File: src/components/projects/ProjectDetailTabs.tsx
type ActiveTabType = 'overview' | 'scenes' | 'objects' | 'ai'

type ProjectDetailTabsProps = {
  activeTab: ActiveTabType
  setActiveTab: (tab: ActiveTabType) => void
}

const ProjectDetailTabs = ({ activeTab, setActiveTab }: ProjectDetailTabsProps) => {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8">
        <button
          className={`py-4 px-1 border-b-2 font-medium text-sm ${
            activeTab === 'overview'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`py-4 px-1 border-b-2 font-medium text-sm ${
            activeTab === 'scenes'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
          onClick={() => setActiveTab('scenes')}
        >
          Scenes
        </button>
        <button
          className={`py-4 px-1 border-b-2 font-medium text-sm ${
            activeTab === 'objects'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
          onClick={() => setActiveTab('objects')}
        >
          Story Objects
        </button>
        <button
          className={`py-4 px-1 border-b-2 font-medium text-sm ${
            activeTab === 'ai'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
          onClick={() => setActiveTab('ai')}
        >
          AI Workshop
        </button>
      </nav>
    </div>
  )
}

export default ProjectDetailTabs

// File: src/components/projects/EditProjectModal.tsx
import { useState, FormEvent, useEffect } from 'react'
import { Dialog } from '@headlessui/react'
import Button from '../ui/Button'
import { Project } from '../../types'
import { XMarkIcon } from '@heroicons/react/24/outline'

type EditProjectModalProps = {
  isOpen: boolean
  onClose: () => void
  onSubmit: (project: { title: string; description: string }) => void
  project: Project
}

const EditProjectModal = ({ isOpen, onClose, onSubmit, project }: EditProjectModalProps) => {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  useEffect(() => {
    if (project) {
      setTitle(project.title)
      setDescription(project.description)
    }
  }, [project, isOpen])
  
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    onSubmit({ 
      title: title.trim(), 
      description: description.trim() 
    })
    
    setIsSubmitting(false)
  }
  
  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      {/* Full-screen container to center the panel */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-white rounded-lg shadow-xl max-w-md w-full">
          <div className="flex justify-between items-start p-4 border-b border-gray-200">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Edit Project
            </Dialog.Title>
            <button
              className="text-gray-400 hover:text-gray-500"
              onClick={onClose}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="p-4 space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700">
                  Project Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input-standard mt-1"
                  placeholder="My Amazing Story"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="input-standard mt-1"
                  placeholder="A brief description of your project..."
                />
              </div>
            </div>
            
            <div className="flex justify-end gap-2 p-4 border-t border-gray-200">
              <Button 
                variant="secondary" 
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={!title.trim() || isSubmitting}
                isLoading={isSubmitting}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}

export default EditProjectModal

// File: src/components/projects/InviteCollaboratorModal.tsx
import { useState, FormEvent } from 'react'
import { Dialog } from '@headlessui/react'
import Button from '../ui/Button'
import { XMarkIcon } from '@heroicons/react/24/outline'

type InviteCollaboratorModalProps = {
  isOpen: boolean
  onClose: () => void
  onSubmit: (email: string) => void
  projectTitle: string
}

const InviteCollaboratorModal = ({ 
  isOpen, 
  onClose, 
  onSubmit,
  projectTitle
}: InviteCollaboratorModalProps) => {
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    onSubmit(email.trim())
    
    // Reset form
    setEmail('')
    setIsSubmitting(false)
  }
  
  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/30" aria-hidden="true" />
      
      {/* Full-screen container to center the panel */}
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="bg-white rounded-lg shadow-xl max-w-md w-full">
          <div className="flex justify-between items-start p-4 border-b border-gray-200">
            <Dialog.Title className="text-lg font-semibold text-gray-900">
              Invite Collaborator
            </Dialog.Title>
            <button
              className="text-gray-400 hover:text-gray-500"
              onClick={onClose}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="p-4 space-y-4">
              <p className="text-sm text-gray-600">
                Invite someone to collaborate on <span className="font-medium">{projectTitle}</span>.
                They will receive an email invitation.
              </p>
              
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-standard mt-1"
                  placeholder="collaborator@example.com"
                  required
                />
              </div>
              
              <div className="text-xs text-gray-500 border-t border-gray-200 pt-3">
                <p>
                  Collaborators can:
                </p>
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li>View and edit project content</li>
                  <li>Add and modify scenes</li>
                  <li>Create and edit story objects</li>
                  <li>Use AI features on the project</li>
                </ul>
                <p className="mt-2">
                  Collaborators cannot delete the project or invite other collaborators.
                </p>
              </div>
            </div>
            
            <div className="flex justify-end gap-2 p-4 border-t border-gray-200">
              <Button 
                variant="secondary" 
                onClick={onClose}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={!email.trim() || isSubmitting}
                isLoading={isSubmitting}
              >
                Send Invitation
              </Button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  )
}

export default InviteCollaboratorModal