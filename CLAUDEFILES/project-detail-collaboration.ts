// src/components/pages/ProjectDetail.tsx (Partial update with collaboration features)
// Note: This is a partial implementation focusing on adding collaboration features

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Tab } from '@headlessui/react';
import { 
  DocumentTextIcon,
  SparklesIcon,
  ChatBubbleLeftRightIcon,
  UsersIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';

// ... other imports ...

import { useSocketContext } from '../../context/SocketContext';
import useTypingDetection from '../../hooks/useTypingDetection';
import PresenceIndicator from '../collaboration/PresenceIndicator';
import TypingIndicator from '../collaboration/TypingIndicator';
import CommentList from '../collaboration/CommentList';
import CollaboratorsList from '../collaboration/CollaboratorsList';

const ProjectDetail: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { socket, isConnected, joinRoom, leaveRoom } = useSocketContext();
  
  // ... existing state variables ...
  
  // Setup typing detection
  const { handleInputChange } = useTypingDetection({
    roomType: 'project',
    roomId: projectId || '',
    isEnabled: isConnected && !!projectId,
  });
  
  // Join project room for real-time collaboration
  useEffect(() => {
    if (!socket || !isConnected || !projectId) return;
    
    // Join project room
    joinRoom('project', projectId);
    
    // Listen for project updates from other users
    socket.on('project_updated', (updatedProject) => {
      if (updatedProject.id === projectId) {
        setProject(updatedProject);
      }
    });
    
    // Listen for scene updates in this project
    socket.on('scene_updated', (updatedScene) => {
      if (updatedScene.projectId === projectId) {
        setScenes(prevScenes => 
          prevScenes.map(scene => 
            scene.id === updatedScene.id ? updatedScene : scene
          )
        );
      }
    });
    
    // Listen for new scenes
    socket.on('scene_created', (newScene) => {
      if (newScene.projectId === projectId) {
        setScenes(prevScenes => [...prevScenes, newScene]);
      }
    });
    
    // Listen for deleted scenes
    socket.on('scene_deleted', (deletedSceneId) => {
      setScenes(prevScenes => 
        prevScenes.filter(scene => scene.id !== deletedSceneId)
      );
    });
    
    return () => {
      // Leave project room on unmount
      leaveRoom('project', projectId);
      socket.off('project_updated');
      socket.off('scene_updated');
      socket.off('scene_created');
      socket.off('scene_deleted');
    };
  }, [socket, isConnected, projectId, joinRoom, leaveRoom]);
  
  // ... existing code ...
  
  // Handle content changes with typing detection
  const handleDescriptionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (!project) return;
    setProject({ ...project, description: e.target.value });
    handleInputChange();
  };
  
  // ... existing code ...
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Project Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          {/* ... existing title/navigation ... */}
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Add Presence Indicator */}
          {projectId && (
            <PresenceIndicator roomType="project" roomId={projectId} />
          )}
          
          {/* ... existing buttons ... */}
          
          {/* Add AI Features button */}
          <Link to={`/projects/${projectId}/ai`}>
            <Button variant="secondary" className="flex items-center">
              <SparklesIcon className="h-5 w-5 mr-2" />
              AI Features
            </Button>
          </Link>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
          {error}
        </div>
      )}
      
      {/* Add Typing Indicator */}
      {projectId && (
        <div className="h-6 mb-2">
          <TypingIndicator roomType="project" roomId={projectId} />
        </div>
      )}
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content column */}
        <div className="lg:col-span-2">
          {/* Project description */}
          <div className="card mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-2">Description</h2>
            <textarea
              value={project?.description || ''}
              onChange={handleDescriptionChange} // Use new handler with typing detection
              placeholder="Add a description for your project..."
              className="block w-full border-gray-300 rounded-md shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              rows={4}
              disabled={isEditing}
            />
          </div>
          
          {/* ... existing scenes list ... */}
        </div>
        
        {/* Sidebar */}
        <div>
          {/* Tabs for sidebar content */}
          <Tab.Group>
            <Tab.List className="flex space-x-1 rounded-xl bg-indigo-100 p-1 mb-6">
              <Tab
                className={({ selected }) =>
                  `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
                   ${
                     selected
                       ? 'bg-white shadow text-indigo-700'
                       : 'text-indigo-600 hover:bg-white/[0.12] hover:text-indigo-900'
                   }`
                }
              >
                <div className="flex items-center justify-center">
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                  Details
                </div>
              </Tab>
              <Tab
                className={({ selected }) =>
                  `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
                   ${
                     selected
                       ? 'bg-white shadow text-indigo-700'
                       : 'text-indigo-600 hover:bg-white/[0.12] hover:text-indigo-900'
                   }`
                }
              >
                <div className="flex items-center justify-center">
                  <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
                  Comments
                </div>
              </Tab>
              <Tab
                className={({ selected }) =>
                  `w-full rounded-lg py-2.5 text-sm font-medium leading-5 
                   ${
                     selected
                       ? 'bg-white shadow text-indigo-700'
                       : 'text-indigo-600 hover:bg-white/[0.12] hover:text-indigo-900'
                   }`
                }
              >
                <div className="flex items-center justify-center">
                  <UsersIcon className="h-5 w-5 mr-2" />
                  Collaborators
                </div>
              </Tab>
            </Tab.List>
            
            <Tab.Panels>
              {/* Details tab */}
              <Tab.Panel>
                {/* ... existing details panel ... */}
                <div className="card mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Project Details</h3>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Genre
                      </label>
                      <select
                        value={project?.genre || ''}
                        onChange={(e) => setProject(prev => prev ? { ...prev, genre: e.target.value } : null)}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        disabled={isEditing}
                        onFocus={() => handleInputChange()}
                      >
                        <option value="">Select a genre</option>
                        <option value="fantasy">Fantasy</option>
                        <option value="science_fiction">Science Fiction</option>
                        <option value="mystery">Mystery</option>
                        <option value="thriller">Thriller</option>
                        <option value="romance">Romance</option>
                        <option value="historical">Historical</option>
                        <option value="horror">Horror</option>
                        <option value="literary">Literary Fiction</option>
                        <option value="young_adult">Young Adult</option>
                        <option value="childrens">Children's</option>
                        <option value="non_fiction">Non-Fiction</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Current Phase
                      </label>
                      <select
                        value={project?.currentPhase || ''}
                        onChange={(e) => setProject(prev => prev ? { ...prev, currentPhase: e.target.value } : null)}
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        disabled={isEditing}
                        onFocus={() => handleInputChange()}
                      >
                        <option value="idea">Idea</option>
                        <option value="expand">Expand</option>
                        <option value="story">Story</option>
                      </select>
                    </div>
                    
                    <div className="flex justify-between text-sm text-gray-500">
                      <span>Created: {formatDate(project?.createdAt)}</span>
                      <span>Updated: {formatDate(project?.updatedAt)}</span>
                    </div>
                  </div>
                </div>
              </Tab.Panel>
              
              {/* Comments tab */}
              <Tab.Panel>
                {projectId ? (
                  <CommentList targetId={projectId} targetType="project" />
                ) : (
                  <div className="card p-4 text-center text-gray-500">
                    <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p>Loading comments...</p>
                  </div>
                )}
              </Tab.Panel>
              
              {/* Collaborators tab */}
              <Tab.Panel>
                {projectId ? (
                  <CollaboratorsList projectId={projectId} />
                ) : (
                  <div className="card p-4 text-center text-gray-500">
                    <UsersIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p>Loading collaborators...</p>
                  </div>
                )}
              </Tab.Panel>
            </Tab.Panels>
          </Tab.Group>
          
          {/* ... existing sidebar content ... */}
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail;
