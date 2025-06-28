// src/components/pages/SceneEditor.tsx (Partial update with collaboration features)
// Note: This is a partial implementation focusing on adding collaboration features

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Tab } from '@headlessui/react';
import { 
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

const SceneEditor: React.FC = () => {
  const { projectId, sceneId } = useParams<{ projectId: string; sceneId: string }>();
  const navigate = useNavigate();
  const { socket, isConnected, joinRoom, leaveRoom } = useSocketContext();
  
  // ... existing state variables ...
  
  // Setup typing detection
  const { handleInputChange } = useTypingDetection({
    roomType: 'scene',
    roomId: sceneId || '',
    isEnabled: isConnected && sceneId !== 'new',
  });
  
  // Join scene room for real-time collaboration
  useEffect(() => {
    if (!socket || !isConnected || !sceneId || sceneId === 'new') return;
    
    // Join scene room
    joinRoom('scene', sceneId);
    
    // Listen for scene updates from other users
    socket.on('scene_updated', (updatedScene) => {
      if (updatedScene.id === sceneId) {
        setScene(updatedScene);
      }
    });
    
    return () => {
      // Leave scene room on unmount
      leaveRoom('scene', sceneId);
      socket.off('scene_updated');
    };
  }, [socket, isConnected, sceneId, joinRoom, leaveRoom]);
  
  // ... existing code ...
  
  // Handle content changes with typing detection
  const handleContentChange = (content: string) => {
    updateSceneContent(content);
    handleInputChange();
  };
  
  // ... existing code ...
  
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Scene Editor Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          {/* ... existing title/navigation ... */}
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Add Presence Indicator */}
          {sceneId && sceneId !== 'new' && (
            <PresenceIndicator roomType="scene" roomId={sceneId} />
          )}
          
          {/* ... existing buttons ... */}
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-md mb-6">
          {error}
        </div>
      )}
      
      {/* Add Typing Indicator */}
      {sceneId && sceneId !== 'new' && (
        <div className="h-6 mb-2">
          <TypingIndicator roomType="scene" roomId={sceneId} />
        </div>
      )}
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Editor column */}
        <div className="lg:col-span-2">
          <div className="card mb-6">
            {/* Scene title input */}
            <input
              type="text"
              value={scene?.title || ''}
              onChange={(e) => updateSceneTitle(e.target.value)}
              placeholder="Scene Title"
              className="block w-full border-0 border-b border-gray-300 focus:border-indigo-600 focus:ring-0 text-xl font-medium mb-4"
              onKeyDown={() => handleInputChange()} // Detect typing
            />
            
            {/* Scene content editor */}
            <textarea
              value={scene?.content || ''}
              onChange={(e) => handleContentChange(e.target.value)} // Use new handler with typing detection
              placeholder="Start writing your scene here..."
              className="block w-full border-0 focus:ring-0 text-base"
              rows={20}
            />
          </div>
          
          {/* ... existing editor components ... */}
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
                  <PencilIcon className="h-5 w-5 mr-2" />
                  Properties
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
              {/* Properties tab */}
              <Tab.Panel>
                {/* ... existing properties panel ... */}
              </Tab.Panel>
              
              {/* Comments tab */}
              <Tab.Panel>
                {sceneId && sceneId !== 'new' ? (
                  <CommentList targetId={sceneId} targetType="scene" />
                ) : (
                  <div className="card p-4 text-center text-gray-500">
                    <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p>Save the scene first to enable comments</p>
                  </div>
                )}
              </Tab.Panel>
              
              {/* Collaborators tab */}
              <Tab.Panel>
                {projectId ? (
                  <div>
                    {/* ... collaborators component ... */}
                    <p className="text-center text-gray-500 py-4">
                      Manage collaborators at the project level
                    </p>
                    <Button
                      variant="secondary"
                      className="w-full"
                      onClick={() => navigate(`/projects/${projectId}`)}
                    >
                      <UsersIcon className="h-5 w-5 mr-2" />
                      Go to Project
                    </Button>
                  </div>
                ) : (
                  <div className="card p-4 text-center text-gray-500">
                    <UsersIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p>Save the scene first to enable collaboration</p>
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

export default SceneEditor;
