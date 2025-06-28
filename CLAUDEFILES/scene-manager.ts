// File: src/pages/SceneManager.tsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { Scene } from '../types';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import Button from '../components/ui/Button';
import KanbanBoard from '../components/scenes/KanbanBoard';
import TimelineView from '../components/scenes/TimelineView';
import { useSocket } from '../hooks/useSocket';
import {
  ArrowLeftIcon,
  ViewBoardsIcon,
  ViewListIcon,
  PlusIcon,
  SearchIcon,
  DownloadIcon,
  RefreshIcon,
  SparklesIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

type ViewMode = 'kanban' | 'timeline';

const SceneManager = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { socket, isConnected } = useSocket();
  
  const [scenes, setScenes] = useState<Scene[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('kanban');
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isGeneratingScenes, setIsGeneratingScenes] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  
  // Load scenes for the current project
  useEffect(() => {
    const loadScenes = async () => {
      if (!projectId) return;
      
      try {
        setIsLoading(true);
        const response = await api.get(`/api/projects/${projectId}/scenes`);
        setScenes(response.data);
        setError('');
      } catch (err) {
        console.error('Failed to load scenes', err);
        setError('Failed to load scenes. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };
    
    loadScenes();
  }, [projectId]);
  
  // Setup real-time socket for collaborative editing
  useEffect(() => {
    if (!socket || !isConnected || !projectId) return;
    
    // Join project room
    socket.emit('join_project', { projectId });
    
    // Listen for scene updates
    socket.on('scene_updated', (updatedScene: Scene) => {
      setScenes(prev => 
        prev.map(scene => scene.id === updatedScene.id ? updatedScene : scene)
      );
    });
    
    // Listen for new scenes
    socket.on('scene_created', (newScene: Scene) => {
      setScenes(prev => [...prev, newScene]);
    });
    
    // Listen for deleted scenes
    socket.on('scene_deleted', (deletedId: string) => {
      setScenes(prev => prev.filter(scene => scene.id !== deletedId));
    });
    
    // Listen for scene order updates
    socket.on('scenes_reordered', (updatedScenes: Scene[]) => {
      setScenes(prev => {
        // Create a map of updated scenes by ID
        const updatedMap = updatedScenes.reduce((map, scene) => {
          map[scene.id] = scene;
          return map;
        }, {} as Record<string, Scene>);
        
        // Update existing scenes with new properties
        return prev.map(scene => 
          updatedMap[scene.id] ? { ...scene, ...updatedMap[scene.id] } : scene
        );
      });
    });
    
    return () => {
      // Leave project room on unmount
      socket.emit('leave_project', { projectId });
      socket.off('scene_updated');
      socket.off('scene_created');
      socket.off('scene_deleted');
      socket.off('scenes_reordered');
    };
  }, [socket, isConnected, projectId]);
  
  // Filter scenes based on search query
  const filteredScenes = searchQuery
    ? scenes.filter(scene =>
        scene.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        scene.content?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : scenes;
  
  // Handle scene order changes
  const handleSceneOrderChange = async (
    sceneOrder: { id: string, order: number, sceneType?: string }[]
  ) => {
    if (!projectId) return;
    
    try {
      setIsUpdating(true);
      await api.post(`/api/projects/${projectId}/scenes/reorder`, { sceneOrder });
      
      // Update local state with new orders and types
      setScenes(prev => {
        const orderMap = sceneOrder.reduce((map, item) => {
          map[item.id] = { order: item.order, sceneType: item.sceneType };
          return map;
        }, {} as Record<string, { order: number, sceneType?: string }>);
        
        return prev.map(scene => {
          if (orderMap[scene.id]) {
            return {
              ...scene,
              order: orderMap[scene.id].order,
              sceneType: orderMap[scene.id].sceneType || scene.sceneType
            };
          }
          return scene;
        });
      });
      
    } catch (err) {
      console.error('Failed to update scene order', err);
      setError('Failed to update scene order. Please try again.');
    } finally {
      setIsUpdating(false);
    }
  };
  
  // Generate scene suggestions using AI
  const handleGenerateScenes = async () => {
    if (!projectId) return;
    
    try {
      setIsGeneratingScenes(true);
      setError('');
      
      const response = await api.post(`/api/ai/projects/${projectId}/suggest-scenes`);
      
      // Append new scenes to the existing list
      if (response.data && Array.isArray(response.data)) {
        setScenes(prev => [...prev, ...response.data]);
      }
      
    } catch (err) {
      console.error('Failed to generate scenes', err);
      setError('Failed to generate scene suggestions. Please try again.');
    } finally {
      setIsGeneratingScenes(false);
    }
  };
  
  // Export scenes to text
  const handleExport = () => {
    if (!scenes.length) return;
    
    // Sort scenes by order
    const sortedScenes = [...scenes].sort((a, b) => a.order - b.order);
    
    // Create a formatted text representation
    const text = sortedScenes.map(scene => {
      return `# ${scene.title}\n\n${scene.content?.replace(/<[^>]*>?/gm, '') || 'No content'}\n\n`;
    }).join('---\n\n');
    
    // Create a download link
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenes-export-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate(`/projects/${projectId}`)}
          >
            <ArrowLeftIcon className="h-5 w-5 mr-1" />
            Back to Project
          </Button>
          <h1 className="text-2xl font-bold text-gray-900 ml-4">Scene Manager</h1>
        </div>
        
        <div className="flex space-x-2">
          <Button
            variant="primary"
            onClick={() => navigate(`/projects/${projectId}/scenes/new`)}
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            New Scene
          </Button>
          
          <Button
            variant="secondary"
            onClick={handleGenerateScenes}
            isLoading={isGeneratingScenes}
            disabled={isGeneratingScenes}
          >
            <SparklesIcon className="h-5 w-5 mr-1" />
            AI Suggestions
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
      
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex items-center space-x-4">
          {/* View mode toggles */}
          <div className="flex items-center space-x-2 bg-gray-100 rounded-md p-1">
            <button
              className={`px-3 py-1.5 rounded text-sm flex items-center ${
                viewMode === 'kanban' 
                  ? 'bg-white shadow-sm' 
                  : 'text-gray-600'
              }`}
              onClick={() => setViewMode('kanban')}
            >
              <ViewBoardsIcon className="h-4 w-4 mr-1.5" />
              Kanban
            </button>
            <button
              className={`px-3 py-1.5 rounded text-sm flex items-center ${
                viewMode === 'timeline' 
                  ? 'bg-white shadow-sm' 
                  : 'text-gray-600'
              }`}
              onClick={() => setViewMode('timeline')}
            >
              <ViewListIcon className="h-4 w-4 mr-1.5" />
              Timeline
            </button>
          </div>
          
          {/* Export button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleExport}
            disabled={!scenes.length}
          >
            <DownloadIcon className="h-4 w-4 mr-1" />
            Export
          </Button>
        </div>
        
        {/* Search */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <SearchIcon className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="input-standard pl-10 w-64"
            placeholder="Search scenes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>
      
      {/* Scene count */}
      <div className="text-sm text-gray-500">
        {filteredScenes.length} {filteredScenes.length === 1 ? 'scene' : 'scenes'} 
        {searchQuery && ` matching "${searchQuery}"`}
        
        {searchQuery && (
          <button
            className="ml-2 text-indigo-600 hover:text-indigo-500"
            onClick={() => setSearchQuery('')}
          >
            Clear search
          </button>
        )}
      </div>
      
      {/* Scene view */}
      {filteredScenes.length > 0 ? (
        viewMode === 'kanban' ? (
          <KanbanBoard
            projectId={projectId || ''}
            scenes={filteredScenes}
            onSceneOrderChange={handleSceneOrderChange}
          />
        ) : (
          <TimelineView
            projectId={projectId || ''}
            scenes={filteredScenes}
            onSceneOrderChange={handleSceneOrderChange}
          />
        )
      ) : (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <p className="text-gray-500 mb-4">No scenes found.</p>
          
          <div className="flex justify-center space-x-4">
            <Button
              onClick={() => navigate(`/projects/${projectId}/scenes/new`)}
            >
              <PlusIcon className="h-5 w-5 mr-1" />
              Create First Scene
            </Button>
            
            <Button
              variant="secondary"
              onClick={handleGenerateScenes}
              isLoading={isGeneratingScenes}
              disabled={isGeneratingScenes}
            >
              <SparklesIcon className="h-5 w-5 mr-1" />
              Generate with AI
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SceneManager;
