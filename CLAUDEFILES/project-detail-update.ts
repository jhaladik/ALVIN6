// File: src/pages/ProjectDetail.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { Project, Scene } from '../types';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import EditProjectModal from '../components/projects/EditProjectModal';
import DeleteProjectModal from '../components/projects/DeleteProjectModal';
import ProjectPhaseSelector from '../components/projects/ProjectPhaseSelector';
import { useSocket } from '../hooks/useSocket';
import {
  PencilIcon,
  TrashIcon,
  UserIcon,
  ClockIcon,
  DocumentTextIcon,
  ViewBoardsIcon,
  CubeIcon,
  SparklesIcon,
  ExclamationCircleIcon,
  ArrowLeftIcon,
  PlusIcon,
  AnnotationIcon
} from '@heroicons/react/24/outline';

const ProjectDetail = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { socket, isConnected } = useSocket();
  
  const [project, setProject] = useState<Project | null>(null);
  const [recentScenes, setRecentScenes] = useState<Scene[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [error, setError] = useState('');
  
  // Load project data
  useEffect(() => {
    const loadProjectData = async () => {
      if (!projectId) return;
      
      try {
        setIsLoading(true);
        
        // Load project and recent scenes in parallel
        const [projectResponse, scenesResponse] = await Promise.all([
          api.get(`/api/projects/${projectId}`),
          api.get(`/api/projects/${projectId}/scenes?limit=5&sort=last_modified`)
        ]);
        
        setProject(projectResponse.data);
        setRecentScenes(scenesResponse.data);
        setError('');
      } catch (err) {
        console.error('Failed to load project data', err);
        setError('Failed to load project data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadProjectData();
  }, [projectId]);
  
  // Setup real-time socket for collaborative editing
  useEffect(() => {
    if (!socket || !isConnected || !projectId) return;
    
    // Join project room
    socket.emit('join_project', { projectId });
    
    // Listen for project updates
    socket.on('project_updated', (updatedProject: Project) => {
      if (updatedProject.id === projectId) {
        setProject(updatedProject);
      }
    });
    
    // Listen for scene updates
    socket.on('scene_updated', (updatedScene: Scene) => {
      setRecentScenes(prev => {
        // Check if the scene is already in our list
        const exists = prev.some(scene => scene.id === updatedScene.id);
        
        if (exists) {
          // Update the existing scene
          return prev.map(scene => 
            scene.id === updatedScene.id ? updatedScene : scene
          );
        } else if (prev.length < 5) {
          // Add the new scene if we have less than 5
          return [...prev, updatedScene];
        } else {
          // Replace the oldest scene with the new one
          return [...prev.slice(1), updatedScene];
        }
      });
    });
    
    return () => {
      // Leave project room on unmount
      socket.emit('leave_project', { projectId });
      socket.off('project_updated');
      socket.off('scene_updated');
    };
  }, [socket, isConnected, projectId]);
  
  // Handle project update
  const handleUpdateProject = async (updatedProject: Partial<Project>) => {
    if (!projectId) return;
    
    try {
      const response = await api.put(`/api/projects/${projectId}`, updatedProject);
      setProject(response.data);
      setIsEditModalOpen(false);
    } catch (err) {
      console.error('Failed to update project', err);
      throw new Error('Failed to update project. Please try again.');
    }
  };
  
  // Handle project deletion
  const handleDeleteProject = async () => {
    if (!projectId) return;
    
    try {
      await api.delete(`/api/projects/${projectId}`);
      navigate('/projects');
    } catch (err) {
      console.error('Failed to delete project', err);
      throw new Error('Failed to delete project. Please try again.');
    }
  };
  
  // Handle phase change
  const handlePhaseChange = async (phase: Project['phase']) => {
    if (!projectId || !project) return;
    
    try {
      await handleUpdateProject({ phase });
    } catch (err) {
      console.error('Failed to update project phase', err);
      setError('Failed to update project phase. Please try again.');
    }
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  
  // Error state
  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <ExclamationCircleIcon className="h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 mb-2">Project Not Found</h2>
        <p className="text-gray-600 mb-4">
          The project you're looking for doesn't exist or you don't have access to it.
        </p>
        <Button onClick={() => navigate('/projects')}>
          <ArrowLeftIcon className="h-5 w-5 mr-1" />
          Back to Projects
        </Button>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/projects')}
            >
              <ArrowLeftIcon className="h-5 w-5 mr-1" />
              All Projects
            </Button>
            
            <h1 className="text-2xl font-bold text-gray-900 ml-4">{project.title}</h1>
          </div>
          
          {project.description && (
            <p className="mt-1 text-gray-600 ml-14">{project.description}</p>
          )}
        </div>
        
        <div className="flex space-x-2">
          <Button
            variant="secondary"
            onClick={() => setIsEditModalOpen(true)}
          >
            <PencilIcon className="h-5 w-5 mr-1" />
            Edit
          </Button>
          
          <Button
            variant="danger"
            onClick={() => setIsDeleteModalOpen(true)}
          >
            <TrashIcon className="h-5 w-5 mr-1" />
            Delete
          </Button>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Phase selector */}
      <div className="card">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Project Phase</h2>
        <ProjectPhaseSelector
          currentPhase={project.phase}
          onChange={handlePhaseChange}
        />
      </div>
      
      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Scenes */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <DocumentTextIcon className="h-5 w-5 mr-2 text-indigo-500" />
              Scenes
            </h2>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(`/projects/${projectId}/scenes`)}
            >
              <ViewBoardsIcon className="h-5 w-5 mr-1" />
              Manage
            </Button>
          </div>
          
          {recentScenes.length > 0 ? (
            <div className="space-y-3">
              {recentScenes.map(scene => (
                <div 
                  key={scene.id}
                  className="flex items-center p-3 border border-gray-200 rounded-md hover:border-indigo-300 hover:bg-indigo-50 transition-colors cursor-pointer"
                  onClick={() => navigate(`/projects/${projectId}/scenes/${scene.id}`)}
                >
                  <div className="flex-shrink-0 mr-3 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-medium">
                    {scene.order}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {scene.title}
                    </p>
                    {scene.sceneType && (
                      <p className="text-xs text-gray-500">
                        {scene.sceneType.charAt(0).toUpperCase() + scene.sceneType.slice(1)}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              
              <Link
                to={`/projects/${projectId}/scenes`}
                className="block text-center text-sm text-indigo-600 hover:text-indigo-500 font-medium"
              >
                View all scenes
              </Link>
            </div>
          ) : (
            <div className="text-center py-6 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-500 mb-4">No scenes created yet</p>
              <Button
                size="sm"
                onClick={() => navigate(`/projects/${projectId}/scenes`)}
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Create First Scene
              </Button>
            </div>
          )}
        </div>
        
        {/* Story Objects */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <CubeIcon className="h-5 w-5 mr-2 text-green-500" />
              Story Objects
            </h2>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(`/projects/${projectId}/objects`)}
            >
              <CubeIcon className="h-5 w-5 mr-1" />
              Manage
            </Button>
          </div>
          
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-3">
              <div className="p-4 bg-indigo-50 rounded-lg text-center">
                <UserIcon className="h-6 w-6 text-indigo-500 mx-auto mb-1" />
                <h3 className="text-sm font-medium text-gray-900">Characters</h3>
                <p className="text-lg font-bold text-indigo-600">
                  {project.characterCount || 0}
                </p>
              </div>
              
              <div className="p-4 bg-green-50 rounded-lg text-center">
                <MapPinIcon className="h-6 w-6 text-green-500 mx-auto mb-1" />
                <h3 className="text-sm font-medium text-gray-900">Locations</h3>
                <p className="text-lg font-bold text-green-600">
                  {project.locationCount || 0}
                </p>
              </div>
              
              <div className="p-4 bg-amber-50 rounded-lg text-center">
                <CubeIcon className="h-6 w-6 text-amber-500 mx-auto mb-1" />
                <h3 className="text-sm font-medium text-gray-900">Props</h3>
                <p className="text-lg font-bold text-amber-600">
                  {project.propCount || 0}
                </p>
              </div>
            </div>
            
            <Link
              to={`/projects/${projectId}/objects`}
              className="block text-center text-sm text-indigo-600 hover:text-indigo-500 font-medium"
            >
              Manage objects
            </Link>
          </div>
        </div>
        
        {/* AI Tools */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <SparklesIcon className="h-5 w-5 mr-2 text-purple-500" />
              AI Workshop
            </h2>
            <Button
              variant="primary"
              size="sm"
              onClick={() => navigate(`/projects/${projectId}/ai`)}
            >
              <SparklesIcon className="h-5 w-5 mr-1" />
              Open
            </Button>
          </div>
          
          <div className="space-y-2">
            <button 
              className="w-full p-3 flex items-center justify-between rounded-md hover:bg-indigo-50 transition-colors"
              onClick={() => navigate(`/projects/${projectId}/ai?tool=structure`)}
            >
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 mr-3">
                  <SparklesIcon className="h-5 w-5" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-medium text-gray-900">Analyze Structure</h3>
                  <p className="text-xs text-gray-500">Get feedback on story structure</p>
                </div>
              </div>
            </button>
            
            <button 
              className="w-full p-3 flex items-center justify-between rounded-md hover:bg-indigo-50 transition-colors"
              onClick={() => navigate(`/projects/${projectId}/ai?tool=suggestions`)}
            >
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 mr-3">
                  <SparklesIcon className="h-5 w-5" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-medium text-gray-900">Scene Suggestions</h3>
                  <p className="text-xs text-gray-500">Generate new scene ideas</p>
                </div>
              </div>
            </button>
            
            <button 
              className="w-full p-3 flex items-center justify-between rounded-md hover:bg-indigo-50 transition-colors"
              onClick={() => navigate(`/projects/${projectId}/ai?tool=critics`)}
            >
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 mr-3">
                  <SparklesIcon className="h-5 w-5" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-medium text-gray-900">AI Critics</h3>
                  <p className="text-xs text-gray-500">Get feedback from 8 specialist critics</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
      
      {/* Collaboration section */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900 flex items-center">
            <UserIcon className="h-5 w-5 mr-2 text-blue-500" />
            Collaboration
          </h2>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => navigate(`/projects/${projectId}/collaborators`)}
          >
            <UserIcon className="h-5 w-5 mr-1" />
            Invite
          </Button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Active Users</h3>
            <div className="bg-gray-50 p-3 rounded-lg min-h-16">
              {project.activeUsers && project.activeUsers.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {project.activeUsers.map(user => (
                    <div key={user.id} className="flex items-center text-sm">
                      <div className="h-6 w-6 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs mr-1">
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <span>{user.username}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No active users</p>
              )}
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Comments</h3>
            <div className="bg-gray-50 p-3 rounded-lg min-h-16">
              {project.recentComments && project.recentComments.length > 0 ? (
                <div className="space-y-2">
                  {project.recentComments.map(comment => (
                    <div key={comment.id} className="text-sm">
                      <div className="flex items-center">
                        <span className="font-medium">{comment.username}</span>
                        <span className="text-gray-500 text-xs ml-2">
                          {new Date(comment.createdAt).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-gray-600">{comment.content}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No comments yet</p>
              )}
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Activity</h3>
            <div className="bg-gray-50 p-3 rounded-lg min-h-16">
              {project.recentActivity && project.recentActivity.length > 0 ? (
                <div className="space-y-2">
                  {project.recentActivity.map((activity, index) => (
                    <div key={index} className="text-sm flex items-center">
                      <ClockIcon className="h-4 w-4 text-gray-400 mr-1" />
                      <span className="text-gray-600">{activity}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">No recent activity</p>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Modals */}
      <EditProjectModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        project={project}
        onUpdate={handleUpdateProject}
      />
      
      <DeleteProjectModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        projectTitle={project.title}
        onDelete={handleDeleteProject}
      />
    </div>
  );
};

export default ProjectDetail;
