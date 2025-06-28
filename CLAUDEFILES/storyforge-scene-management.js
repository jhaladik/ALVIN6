// File: src/pages/SceneEditor.tsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { Scene, StoryObject, AIAnalysis } from '../types'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import Button from '../components/ui/Button'
import {
  ArrowLeftIcon,
  LightBulbIcon,
  DocumentTextIcon,
  PencilIcon,
  TrashIcon,
  ChatBubbleBottomCenterTextIcon,
  BookmarkIcon,
  UserIcon,
  MapPinIcon,
  SparklesIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import SceneContentEditor from '../components/scenes/SceneContentEditor'
import SceneObjectSelector from '../components/scenes/SceneObjectSelector'
import ScenePropertiesPanel from '../components/scenes/ScenePropertiesPanel'
import AICriticPanel from '../components/ai/AICriticPanel'
import CommentSection from '../components/collaboration/CommentSection'
import { useSocket } from '../hooks/useSocket'

type EditorTab = 'write' | 'properties' | 'ai' | 'comments'

const SceneEditor = () => {
  const { projectId, sceneId } = useParams<{ projectId: string; sceneId: string }>()
  const navigate = useNavigate()
  const { socket, isConnected } = useSocket()
  
  const [scene, setScene] = useState<Scene | null>(null)
  const [projectObjects, setProjectObjects] = useState<{
    characters: StoryObject[]
    locations: StoryObject[]
    props: StoryObject[]
  }>({
    characters: [],
    locations: [],
    props: [],
  })
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<EditorTab>('write')
  const [isAiAnalyzing, setIsAiAnalyzing] = useState(false)
  const [activeCriticType, setActiveCriticType] = useState<string>('general')
  
  // Setup real-time socket for collaborative editing
  useEffect(() => {
    if (!socket || !isConnected || !sceneId) return
    
    // Join scene room
    socket.emit('join_scene', { sceneId })
    
    // Listen for scene updates
    socket.on('scene_updated', (updatedScene: Scene) => {
      if (updatedScene.id === sceneId) {
        setScene(updatedScene)
      }
    })
    
    // Listen for new AI analysis
    socket.on('ai_analysis_completed', (analysis: AIAnalysis) => {
      if (analysis.targetId === sceneId) {
        setAiAnalysis(prev => [...prev, analysis])
        setIsAiAnalyzing(false)
      }
    })
    
    return () => {
      // Leave scene room on unmount
      socket.emit('leave_scene', { sceneId })
      socket.off('scene_updated')
      socket.off('ai_analysis_completed')
    }
  }, [socket, isConnected, sceneId])
  
  // Load scene data
  useEffect(() => {
    const loadSceneData = async () => {
      if (!projectId || !sceneId) return
      
      try {
        setIsLoading(true)
        const isNewScene = sceneId === 'new'
        
        if (isNewScene) {
          // For new scene, just load project objects
          const objectsResponse = await api.get(`/api/projects/${projectId}/objects`)
          
          const defaultNewScene: Scene = {
            id: '',
            projectId: projectId,
            title: 'Untitled Scene',
            content: '',
            emotionalIntensity: 5,
            order: 1, // Will be set to highest order + 1 on save
            characters: [],
            locations: [],
            props: [],
            createdAt: new Date().toISOString(),
            lastModified: new Date().toISOString(),
          }
          
          setScene(defaultNewScene)
          
          // Organize objects by type
          const characters = objectsResponse.data.filter(
            (obj: StoryObject) => obj.type === 'character'
          )
          const locations = objectsResponse.data.filter(
            (obj: StoryObject) => obj.type === 'location'
          )
          const props = objectsResponse.data.filter(
            (obj: StoryObject) => obj.type === 'prop'
          )
          
          setProjectObjects({
            characters,
            locations,
            props,
          })
        } else {
          // For existing scene, load scene, objects, and AI analysis
          const [sceneResponse, objectsResponse, aiResponse] = await Promise.all([
            api.get(`/api/scenes/${sceneId}`),
            api.get(`/api/projects/${projectId}/objects`),
            api.get(`/api/ai/analysis?targetId=${sceneId}&targetType=scene`),
          ])
          
          setScene(sceneResponse.data)
          setAiAnalysis(aiResponse.data)
          
          // Organize objects by type
          const characters = objectsResponse.data.filter(
            (obj: StoryObject) => obj.type === 'character'
          )
          const locations = objectsResponse.data.filter(
            (obj: StoryObject) => obj.type === 'location'
          )
          const props = objectsResponse.data.filter(
            (obj: StoryObject) => obj.type === 'prop'
          )
          
          setProjectObjects({
            characters,
            locations,
            props,
          })
        }
      } catch (err) {
        console.error('Failed to load scene data', err)
        setError('Failed to load scene data. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }
    
    loadSceneData()
  }, [projectId, sceneId])
  
  const handleSaveScene = async () => {
    if (!scene || !projectId) return
    
    try {
      setIsSaving(true)
      let response
      
      if (sceneId === 'new') {
        // For new scenes, get the highest order
        const scenesResponse = await api.get(`/api/scenes?projectId=${projectId}`)
        const scenes = scenesResponse.data
        const highestOrder = scenes.length > 0 
          ? Math.max(...scenes.map((s: Scene) => s.order)) 
          : 0
          
        // Create new scene
        response = await api.post('/api/scenes', {
          ...scene,
          projectId,
          order: highestOrder + 1,
        })
        
        // Navigate to the newly created scene
        navigate(`/projects/${projectId}/scenes/${response.data.id}`, { replace: true })
      } else {
        // Update existing scene
        response = await api.put(`/api/scenes/${scene.id}`, scene)
      }
      
      setScene(response.data)
      
      // Emit scene update event for real-time collaboration
      if (socket && isConnected) {
        socket.emit('scene_update', response.data)
      }
    } catch (err) {
      console.error('Failed to save scene', err)
      setError('Failed to save scene. Please try again.')
    } finally {
      setIsSaving(false)
    }
  }
  
  const handleDeleteScene = async () => {
    if (!scene || !projectId || sceneId === 'new') return
    
    if (!confirm('Are you sure you want to delete this scene? This action cannot be undone.')) {
      return
    }
    
    try {
      await api.delete(`/api/scenes/${scene.id}`)
      navigate(`/projects/${projectId}`)
    } catch (err) {
      console.error('Failed to delete scene', err)
      setError('Failed to delete scene. Please try again.')
    }
  }
  
  const updateSceneContent = (content: string) => {
    if (!scene) return
    setScene({ ...scene, content, lastModified: new Date().toISOString() })
  }
  
  const updateSceneTitle = (title: string) => {
    if (!scene) return
    setScene({ ...scene, title, lastModified: new Date().toISOString() })
  }
  
  const updateSceneObjects = (
    type: 'characters' | 'locations' | 'props',
    objectIds: string[]
  ) => {
    if (!scene) return
    setScene({ ...scene, [type]: objectIds, lastModified: new Date().toISOString() })
  }
  
  const updateSceneProperties = (properties: Partial<Scene>) => {
    if (!scene) return
    setScene({ ...scene, ...properties, lastModified: new Date().toISOString() })
  }
  
  const requestAiAnalysis = async (criticType: string) => {
    if (!scene || !projectId || sceneId === 'new') return
    
    try {
      setIsAiAnalyzing(true)
      setActiveCriticType(criticType)
      
      // Save the scene first to ensure the latest content is analyzed
      await handleSaveScene()
      
      // Request AI analysis
      await api.post(`/api/ai/analyze-scene`, {
        sceneId: scene.id,
        criticType,
      })
      
      // The socket will handle the response when analysis is completed
    } catch (err) {
      console.error('Failed to request AI analysis', err)
      setError('Failed to request AI analysis. Please try again.')
      setIsAiAnalyzing(false)
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  if (!scene && !isLoading) {
    return (
      <div className="text-center py-12">
        <ExclamationCircleIcon className="h-12 w-12 text-red-500 mx-auto" />
        <h2 className="mt-4 text-lg font-medium text-gray-900">Scene not found</h2>
        <p className="mt-2 text-gray-600">This scene may have been deleted or you don't have access.</p>
        <Button 
          variant="primary" 
          className="mt-4" 
          onClick={() => navigate(`/projects/${projectId}`)}
        >
          Back to Project
        </Button>
      </div>
    )
  }
  
  return (
    <div className="h-full flex flex-col">
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      
      {/* Scene header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Button
            variant="ghost"
            onClick={() => navigate(`/projects/${projectId}`)}
            className="mr-2"
          >
            <ArrowLeftIcon className="h-5 w-5" />
          </Button>
          
          <div>
            <div className="flex items-center">
              <input
                type="text"
                value={scene?.title || ''}
                onChange={(e) => updateSceneTitle(e.target.value)}
                className="text-2xl font-bold text-gray-900 border-none focus:ring-0 focus:outline-none p-0 bg-transparent"
                placeholder="Untitled Scene"
              />
            </div>
            
            <p className="text-sm text-gray-500">
              Scene #{scene?.order} • Last modified: {new Date(scene?.lastModified || '').toLocaleString()}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="primary"
            onClick={handleSaveScene}
            isLoading={isSaving}
          >
            Save
          </Button>
          
          {sceneId !== 'new' && (
            <Button
              variant="danger"
              onClick={handleDeleteScene}
            >
              <TrashIcon className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-gray-200 mb-4">
        <nav className="-mb-px flex space-x-6">
          <button
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center ${
              activeTab === 'write'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('write')}
          >
            <DocumentTextIcon className="h-5 w-5 mr-2" />
            Write
          </button>
          <button
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center ${
              activeTab === 'properties'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('properties')}
          >
            <PencilIcon className="h-5 w-5 mr-2" />
            Properties
          </button>
          <button
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center ${
              activeTab === 'ai'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('ai')}
          >
            <SparklesIcon className="h-5 w-5 mr-2" />
            AI Critics
          </button>
          <button
            className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center ${
              activeTab === 'comments'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('comments')}
          >
            <ChatBubbleBottomCenterTextIcon className="h-5 w-5 mr-2" />
            Comments
          </button>
        </nav>
      </div>
      
      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'write' && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="md:col-span-3">
              <SceneContentEditor 
                content={scene?.content || ''}
                onChange={updateSceneContent}
              />
            </div>
            
            <div className="space-y-6">
              <SceneObjectSelector
                title="Characters"
                icon={<UserIcon className="h-5 w-5" />}
                selectedIds={scene?.characters || []}
                objects={projectObjects.characters}
                onChange={(ids) => updateSceneObjects('characters', ids)}
              />
              
              <SceneObjectSelector
                title="Locations"
                icon={<MapPinIcon className="h-5 w-5" />}
                selectedIds={scene?.locations || []}
                objects={projectObjects.locations}
                onChange={(ids) => updateSceneObjects('locations', ids)}
              />
              
              <SceneObjectSelector
                title="Props"
                icon={<BookmarkIcon className="h-5 w-5" />}
                selectedIds={scene?.props || []}
                objects={projectObjects.props}
                onChange={(ids) => updateSceneObjects('props', ids)}
              />
              
              <div className="card">
                <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <LightBulbIcon className="h-5 w-5 text-yellow-500 mr-1" />
                  AI Suggestion
                </h3>
                <p className="text-sm text-gray-600">
                  Save your scene to get AI suggestions for improvement or click the AI Critics tab.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-3 w-full"
                  onClick={() => {
                    handleSaveScene().then(() => {
                      setActiveTab('ai')
                      requestAiAnalysis('general')
                    })
                  }}
                >
                  <SparklesIcon className="h-4 w-4 mr-2" />
                  Get Suggestions
                </Button>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'properties' && scene && (
          <ScenePropertiesPanel
            scene={scene}
            onUpdate={updateSceneProperties}
          />
        )}
        
        {activeTab === 'ai' && (
          <AICriticPanel
            sceneId={scene?.id || ''}
            aiAnalysis={aiAnalysis}
            isAnalyzing={isAiAnalyzing}
            activeCriticType={activeCriticType}
            onRequestAnalysis={requestAiAnalysis}
          />
        )}
        
        {activeTab === 'comments' && sceneId !== 'new' && (
          <CommentSection targetId={sceneId} targetType="scene" />
        )}
        
        {activeTab === 'comments' && sceneId === 'new' && (
          <div className="text-center py-12">
            <ChatBubbleBottomCenterTextIcon className="h-12 w-12 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">Save this scene first</h3>
            <p className="mt-1 text-sm text-gray-500">
              You need to save this scene before you can add comments.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default SceneEditor

// File: src/components/scenes/SceneContentEditor.tsx
import { useEffect, useRef } from 'react'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import CharacterCount from '@tiptap/extension-character-count'
import Placeholder from '@tiptap/extension-placeholder'

// Note: In a real implementation, you would need to install these dependencies:
// npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-character-count @tiptap/extension-placeholder

type SceneContentEditorProps = {
  content: string
  onChange: (content: string) => void
}

const SceneContentEditor = ({ content, onChange }: SceneContentEditorProps) => {
  const editorRef = useRef<HTMLDivElement>(null)
  
  const editor = useEditor({
    extensions: [
      StarterKit,
      CharacterCount.configure({
        limit: 50000,
      }),
      Placeholder.configure({
        placeholder: 'Start writing your scene here...',
      }),
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    autofocus: 'end',
  })
  
  // Update content when prop changes
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content)
    }
  }, [content, editor])
  
  // Handle tab key for indentation
  useEffect(() => {
    if (!editorRef.current) return
    
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Tab' && editor) {
        event.preventDefault()
        editor.commands.insertContent('&nbsp;&nbsp;&nbsp;&nbsp;')
      }
    }
    
    editorRef.current.addEventListener('keydown', handleKeyDown)
    
    return () => {
      editorRef.current?.removeEventListener('keydown', handleKeyDown)
    }
  }, [editor])
  
  return (
    <div className="card min-h-[500px] flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-700">Scene Content</h3>
        {editor && (
          <span className="text-xs text-gray-500">
            {editor.storage.characterCount.characters()}/50,000 characters
          </span>
        )}
      </div>
      
      <div 
        className="flex-1 border border-gray-300 rounded-md overflow-y-auto"
        ref={editorRef}
      >
        <EditorContent 
          editor={editor} 
          className="h-full px-4 py-3 prose max-w-none"
        />
      </div>
    </div>
  )
}

export default SceneContentEditor

// File: src/components/scenes/SceneObjectSelector.tsx
import { ReactNode, useState } from 'react'
import { StoryObject } from '../../types'
import { PlusIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { useParams } from 'react-router-dom'

type SceneObjectSelectorProps = {
  title: string
  icon: ReactNode
  selectedIds: string[]
  objects: StoryObject[]
  onChange: (ids: string[]) => void
}

const SceneObjectSelector = ({ 
  title, 
  icon, 
  selectedIds, 
  objects, 
  onChange 
}: SceneObjectSelectorProps) => {
  const { projectId } = useParams<{ projectId: string }>()
  const [isExpanded, setIsExpanded] = useState(true)
  
  const toggleSelection = (id: string) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter(selectedId => selectedId !== id))
    } else {
      onChange([...selectedIds, id])
    }
  }
  
  return (
    <div className="card">
      <div 
        className="flex items-center justify-between cursor-pointer" 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="text-sm font-medium text-gray-700 flex items-center">
          {icon}
          <span className="ml-2">{title}</span>
          <span className="ml-2 text-xs text-gray-500">
            ({selectedIds.length}/{objects.length})
          </span>
        </h3>
        {isExpanded ? (
          <ChevronUpIcon className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDownIcon className="h-5 w-5 text-gray-400" />
        )}
      </div>
      
      {isExpanded && (
        <div className="mt-3 space-y-2">
          {objects.length > 0 ? (
            objects.map(obj => (
              <div 
                key={obj.id} 
                className={`flex items-center rounded-md p-2 cursor-pointer transition-colors ${
                  selectedIds.includes(obj.id) 
                    ? 'bg-indigo-50 border border-indigo-200'
                    : 'hover:bg-gray-50 border border-transparent'
                }`}
                onClick={() => toggleSelection(obj.id)}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.includes(obj.id)}
                  onChange={() => toggleSelection(obj.id)}
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded mr-3"
                />
                <div className="flex-1 overflow-hidden">
                  <p className="text-sm font-medium text-gray-900 truncate">{obj.name}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-sm text-gray-500 text-center py-2">
              No {title.toLowerCase()} available
            </div>
          )}
          
          <Link
            to={`/projects/${projectId}/objects?type=${title.toLowerCase()}`}
            className="flex items-center justify-center w-full text-sm text-indigo-600 hover:text-indigo-500 font-medium mt-2 py-1"
          >
            <PlusIcon className="h-4 w-4 mr-1" />
            Add New {title.slice(0, -1)}
          </Link>
        </div>
      )}
    </div>
  )
}

export default SceneObjectSelector

// File: src/components/scenes/ScenePropertiesPanel.tsx
import { Scene } from '../../types'

type ScenePropertiesPanelProps = {
  scene: Scene
  onUpdate: (properties: Partial<Scene>) => void
}

const ScenePropertiesPanel = ({ scene, onUpdate }: ScenePropertiesPanelProps) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Properties</h3>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="scene-title" className="block text-sm font-medium text-gray-700 mb-1">
              Scene Title
            </label>
            <input
              id="scene-title"
              type="text"
              value={scene.title}
              onChange={(e) => onUpdate({ title: e.target.value })}
              className="input-standard"
            />
          </div>
          
          <div>
            <label htmlFor="scene-order" className="block text-sm font-medium text-gray-700 mb-1">
              Scene Order
            </label>
            <input
              id="scene-order"
              type="number"
              min="1"
              value={scene.order}
              onChange={(e) => onUpdate({ order: parseInt(e.target.value) })}
              className="input-standard"
            />
            <p className="text-xs text-gray-500 mt-1">
              The order determines where this scene appears in the story sequence.
            </p>
          </div>
          
          <div>
            <label htmlFor="emotional-intensity" className="block text-sm font-medium text-gray-700 mb-1">
              Emotional Intensity ({scene.emotionalIntensity}/10)
            </label>
            <input
              id="emotional-intensity"
              type="range"
              min="1"
              max="10"
              value={scene.emotionalIntensity}
              onChange={(e) => onUpdate({ emotionalIntensity: parseInt(e.target.value) })}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>Subtle</span>
              <span>Moderate</span>
              <span>Intense</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Scene Relationships</h3>
        
        <div className="space-y-6">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Characters in this Scene</h4>
            <div className="flex flex-wrap gap-2">
              {scene.characters.length > 0 ? (
                scene.characters.map(charId => {
                  const character = charId
                  return (
                    <div 
                      key={charId}
                      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {character}
                    </div>
                  )
                })
              ) : (
                <p className="text-sm text-gray-500">No characters selected</p>
              )}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Locations in this Scene</h4>
            <div className="flex flex-wrap gap-2">
              {scene.locations.length > 0 ? (
                scene.locations.map(locId => {
                  const location = locId
                  return (
                    <div 
                      key={locId}
                      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                    >
                      {location}
                    </div>
                  )
                })
              ) : (
                <p className="text-sm text-gray-500">No locations selected</p>
              )}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Props in this Scene</h4>
            <div className="flex flex-wrap gap-2">
              {scene.props.length > 0 ? (
                scene.props.map(propId => {
                  const prop = propId
                  return (
                    <div 
                      key={propId}
                      className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                    >
                      {prop}
                    </div>
                  )
                })
              ) : (
                <p className="text-sm text-gray-500">No props selected</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScenePropertiesPanel

// File: src/components/ai/AICriticPanel.tsx
import { AIAnalysis } from '../../types'
import Button from '../ui/Button'
import LoadingSpinner from '../ui/LoadingSpinner'
import { SparklesIcon } from '@heroicons/react/24/outline'

type AICriticPanelProps = {
  sceneId: string
  aiAnalysis: AIAnalysis[]
  isAnalyzing: boolean
  activeCriticType: string
  onRequestAnalysis: (criticType: string) => void
}

const AICriticPanel = ({
  sceneId,
  aiAnalysis,
  isAnalyzing,
  activeCriticType,
  onRequestAnalysis,
}: AICriticPanelProps) => {
  // List of available AI critics
  const critics = [
    { id: 'general', name: 'General Analysis', color: 'bg-indigo-100 text-indigo-800' },
    { id: 'character', name: 'Character Development', color: 'bg-blue-100 text-blue-800' },
    { id: 'plot', name: 'Plot Coherence', color: 'bg-purple-100 text-purple-800' },
    { id: 'pacing', name: 'Pacing & Rhythm', color: 'bg-amber-100 text-amber-800' },
    { id: 'dialogue', name: 'Dialogue Evaluation', color: 'bg-green-100 text-green-800' },
    { id: 'setting', name: 'Setting & Atmosphere', color: 'bg-rose-100 text-rose-800' },
    { id: 'theme', name: 'Thematic Elements', color: 'bg-teal-100 text-teal-800' },
    { id: 'style', name: 'Style & Voice', color: 'bg-orange-100 text-orange-800' },
  ]
  
  // Get filtered analysis for the active critic
  const filteredAnalysis = aiAnalysis.filter(
    (analysis) => analysis.criticType === activeCriticType
  ).sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  
  // Get date formatted for display
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }
  
  const getActiveCriticColor = () => {
    const critic = critics.find(c => c.id === activeCriticType)
    return critic?.color || 'bg-gray-100 text-gray-800'
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Critics sidebar */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">AI Critics</h3>
        
        <div className="space-y-2">
          {critics.map((critic) => (
            <button
              key={critic.id}
              onClick={() => onRequestAnalysis(critic.id)}
              disabled={isAnalyzing}
              className={`w-full flex items-center justify-between p-3 rounded-md text-sm font-medium transition-colors ${
                activeCriticType === critic.id
                  ? 'bg-indigo-50 border border-indigo-200'
                  : 'hover:bg-gray-50 border border-transparent'
              }`}
            >
              <span>{critic.name}</span>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${critic.color}`}>
                {aiAnalysis.filter((a) => a.criticType === critic.id).length > 0 ? 'Available' : 'New'}
              </span>
            </button>
          ))}
        </div>
        
        <div className="mt-6 text-xs text-gray-500">
          <p>Each AI critic provides specialized feedback from a different perspective.</p>
          <p className="mt-2">Running an AI analysis will use tokens from your account.</p>
        </div>
      </div>
      
      {/* Analysis content */}
      <div className="md:col-span-2">
        {isAnalyzing ? (
          <div className="card flex flex-col items-center justify-center min-h-[400px]">
            <SparklesIcon className="h-12 w-12 text-indigo-500 mb-4 animate-pulse" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">AI Analysis in Progress</h3>
            <p className="text-gray-600 text-center max-w-md mb-6">
              Our AI critic is carefully analyzing your scene from the perspective of 
              "{critics.find(c => c.id === activeCriticType)?.name}".
              This may take up to a minute.
            </p>
            <LoadingSpinner size="lg" />
          </div>
        ) : filteredAnalysis.length > 0 ? (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900 flex items-center">
                <span className={`inline-flex items-center justify-center h-6 w-6 rounded-full ${getActiveCriticColor()} mr-2 text-xs`}>
                  AI
                </span>
                {critics.find(c => c.id === activeCriticType)?.name}
              </h3>
              
              <Button
                variant="secondary"
                size="sm"
                onClick={() => onRequestAnalysis(activeCriticType)}
              >
                <SparklesIcon className="h-4 w-4 mr-1" />
                Refresh Analysis
              </Button>
            </div>
            
            <div className="space-y-6">
              {filteredAnalysis.map((analysis) => (
                <div key={analysis.id}>
                  <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: analysis.content }} />
                  
                  <p className="text-xs text-gray-500 mt-4">
                    Analysis generated on {formatDate(analysis.createdAt)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="card flex flex-col items-center justify-center min-h-[400px]">
            <SparklesIcon className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Analysis Yet</h3>
            <p className="text-gray-600 text-center max-w-md mb-6">
              Get insights from our AI critic on your scene's 
              {critics.find(c => c.id === activeCriticType)?.name.toLowerCase()}.
            </p>
            <Button onClick={() => onRequestAnalysis(activeCriticType)}>
              <SparklesIcon className="h-5 w-5 mr-1" />
              Generate Analysis
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

export default AICriticPanel

// File: src/components/collaboration/CommentSection.tsx
import { useState, useEffect, FormEvent } from 'react'
import { api } from '../../services/api'
import { Comment } from '../../types'
import { useAuth } from '../../hooks/useAuth'
import { useSocket } from '../../hooks/useSocket'
import Button from '../ui/Button'
import LoadingSpinner from '../ui/LoadingSpinner'
import {
  ChatBubbleBottomCenterTextIcon,
  PaperAirplaneIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'

type CommentSectionProps = {
  targetId: string
  targetType: 'project' | 'scene' | 'object'
}

const CommentSection = ({ targetId, targetType }: CommentSectionProps) => {
  const [comments, setComments] = useState<Comment[]>([])
  const [newComment, setNewComment] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { user } = useAuth()
  const { socket, isConnected } = useSocket()
  
  // Load comments
  useEffect(() => {
    const loadComments = async () => {
      try {
        setIsLoading(true)
        const response = await api.get(`/api/collaboration/comments?targetId=${targetId}&targetType=${targetType}`)
        setComments(response.data)
      } catch (error) {
        console.error('Failed to load comments', error)
      } finally {
        setIsLoading(false)
      }
    }
    
    loadComments()
  }, [targetId, targetType])
  
  // Set up socket for real-time comments
  useEffect(() => {
    if (!socket || !isConnected) return
    
    socket.on('new_comment', (comment: Comment) => {
      if (comment.targetId === targetId) {
        setComments(prevComments => [comment, ...prevComments])
      }
    })
    
    socket.on('delete_comment', (commentId: string) => {
      setComments(prevComments => prevComments.filter(c => c.id !== commentId))
    })
    
    return () => {
      socket.off('new_comment')
      socket.off('delete_comment')
    }
  }, [socket, isConnected, targetId])
  
  const handleSubmitComment = async (e: FormEvent) => {
    e.preventDefault()
    
    if (!newComment.trim() || !user) return
    
    try {
      setIsSubmitting(true)
      
      const response = await api.post('/api/collaboration/comments', {
        targetId,
        targetType,
        content: newComment.trim(),
      })
      
      // Add to local state if socket doesn't update it
      setComments(prevComments => [response.data, ...prevComments])
      setNewComment('')
    } catch (error) {
      console.error('Failed to post comment', error)
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const handleDeleteComment = async (commentId: string) => {
    try {
      await api.delete(`/api/collaboration/comments/${commentId}`)
      
      // Remove from local state if socket doesn't update it
      setComments(prevComments => prevComments.filter(c => c.id !== commentId))
    } catch (error) {
      console.error('Failed to delete comment', error)
    }
  }
  
  const formatDate = (date: string) => {
    const commentDate = new Date(date)
    const now = new Date()
    const diffMs = now.getTime() - commentDate.getTime()
    const diffMins = Math.round(diffMs / 60000)
    const diffHours = Math.round(diffMs / 3600000)
    const diffDays = Math.round(diffMs / 86400000)
    
    if (diffMins < 1) return 'just now'
    if (diffMins < 60) return `${diffMins} ${diffMins === 1 ? 'minute' : 'minutes'} ago`
    if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`
    if (diffDays < 7) return `${diffDays} ${diffDays === 1 ? 'day' : 'days'} ago`
    
    return commentDate.toLocaleDateString()
  }
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-8">
        <LoadingSpinner size="lg" />
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Comment form */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Add Comment</h3>
        
        <form onSubmit={handleSubmitComment}>
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            className="input-standard min-h-[100px]"
            placeholder="Add your comments, suggestions, or questions..."
            required
          />
          
          <div className="flex justify-end mt-4">
            <Button
              type="submit"
              disabled={!newComment.trim() || isSubmitting}
              isLoading={isSubmitting}
            >
              <PaperAirplaneIcon className="h-5 w-5 mr-1" />
              Post Comment
            </Button>
          </div>
        </form>
      </div>
      
      {/* Comments list */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Comments</h3>
        
        {comments.length > 0 ? (
          <div className="space-y-6 divide-y divide-gray-200">
            {comments.map((comment) => (
              <div key={comment.id} className="pt-6 first:pt-0">
                <div className="flex justify-between">
                  <div className="flex items-center">
                    <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                      <span className="text-white font-medium">
                        {comment.username[0].toUpperCase()}
                      </span>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">{comment.username}</p>
                      <p className="text-xs text-gray-500">{formatDate(comment.createdAt)}</p>
                    </div>
                  </div>
                  
                  {user?.id === comment.userId && (
                    <button
                      onClick={() => handleDeleteComment(comment.id)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  )}
                </div>
                <div className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
                  {comment.content}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 border border-dashed border-gray-300 rounded-md">
            <ChatBubbleBottomCenterTextIcon className="h-10 w-10 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No comments yet</h3>
            <p className="mt-1 text-sm text-gray-500">Be the first to add a comment.</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default CommentSection

// File: src/pages/ScenesKanban.tsx
import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../services/api'
import { Scene } from '../types'
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import Button from '../components/ui/Button'
import {
  PlusIcon,
  ArrowPathIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

// Note: In a real implementation, you would need to install this dependency:
// npm install react-beautiful-dnd

const ScenesKanban = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [scenes, setScenes] = useState<Scene[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  
  // Load scenes
  useEffect(() => {
    const loadScenes = async () => {
      if (!projectId) return
      
      try {
        setIsLoading(true)
        const response = await api.get(`/api/scenes?projectId=${projectId}`)
        
        // Sort scenes by order
        const sortedScenes = response.data.sort((a: Scene, b: Scene) => a.order - b.order)
        setScenes(sortedScenes)
      } catch (err) {
        console.error('Failed to load scenes', err)
        setError('Failed to load scenes. Please try again.')
      } finally {
        setIsLoading(false)
      }
    }
    
    loadScenes()
  }, [projectId])
  
  // Update scene orders after drag and drop
  const handleDragEnd = async (result: DropResult) => {
    const { destination, source, draggableId } = result
    
    // If dropped outside a droppable area or same position
    if (!destination || (destination.index === source.index)) {
      return
    }
    
    // Create a copy of scenes
    const newScenes = Array.from(scenes)
    
    // Get the dragged scene
    const draggedScene = newScenes.find(scene => scene.id === draggableId)
    
    if (!draggedScene) return
    
    // Remove from the original position
    newScenes.splice(source.index, 1)
    
    // Insert at the new position
    newScenes.splice(destination.index, 0, draggedScene)
    
    // Update scene orders
    const updatedScenes = newScenes.map((scene, index) => ({
      ...scene,
      order: index + 1,
    }))
    
    // Update state optimistically
    setScenes(updatedScenes)
    
    // Update on the server
    try {
      await Promise.all(
        updatedScenes.map(scene => 
          api.put(`/api/scenes/${scene.id}`, {
            ...scene,
            order: scene.order
          })
        )
      )
    } catch (err) {
      console.error('Failed to update scene orders', err)
      setError('Failed to update scene orders. Please try again.')
    }
  }
  
  if (isLoading) {
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
      
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-900">Scene Timeline</h2>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => window.location.reload()}
          >
            <ArrowPathIcon className="h-5 w-5 mr-1" />
            Refresh
          </Button>
          <Link to={`/projects/${projectId}/scenes/new`} className="btn-primary inline-flex items-center">
            <PlusIcon className="h-5 w-5 mr-1" />
            Add Scene
          </Link>
        </div>
      </div>
      
      {scenes.length > 0 ? (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="scenes" direction="vertical">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="space-y-4"
              >
                {scenes.map((scene, index) => (
                  <Draggable key={scene.id} draggableId={scene.id} index={index}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        className="card border border-gray-200 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start">
                          <div 
                            {...provided.dragHandleProps} 
                            className="h-8 w-8 bg-gray-100 rounded-full flex items-center justify-center mr-4 cursor-grab"
                          >
                            {scene.order}
                          </div>
                          
                          <div className="flex-1">
                            <Link to={`/projects/${projectId}/scenes/${scene.id}`} className="block">
                              <h3 className="text-lg font-medium text-gray-900 hover:text-indigo-600">
                                {scene.title}
                              </h3>
                              <div className="mt-2">
                                <div className="text-sm text-gray-600 line-clamp-2">
                                  {scene.content.replace(/<[^>]*>/g, '')}
                                </div>
                              </div>
                            </Link>
                            
                            <div className="mt-4 flex flex-wrap gap-2">
                              {scene.characters.length > 0 && (
                                <div className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
                                  {scene.characters.length} character{scene.characters.length !== 1 ? 's' : ''}
                                </div>
                              )}
                              
                              {scene.locations.length > 0 && (
                                <div className="text-xs bg-purple-50 text-purple-700 px-2 py-1 rounded-full">
                                  {scene.locations.length} location{scene.locations.length !== 1 ? 's' : ''}
                                </div>
                              )}
                              
                              {scene.props.length > 0 && (
                                <div className="text-xs bg-green-50 text-green-700 px-2 py-1 rounded-full">
                                  {scene.props.length} prop{scene.props.length !== 1 ? 's' : ''}
                                </div>
                              )}
                              
                              <div className="text-xs bg-yellow-50 text-yellow-700 px-2 py-1 rounded-full">
                                Intensity: {scene.emotionalIntensity}/10
                              </div>
                            </div>
                          </div>
                          
                          <Link 
                            to={`/projects/${projectId}/scenes/${scene.id}`}
                            className="inline-flex items-center ml-4 text-sm text-indigo-600 hover:text-indigo-500"
                          >
                            Edit
                          </Link>
                        </div>
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      ) : (
        <div className="text-center py-16 border border-dashed border-gray-300 rounded-md">
          <SparklesIcon className="h-12 w-12 text-gray-400 mx-auto" />
          <h3 className="mt-4 text-sm font-medium text-gray-900">No scenes yet</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by creating your first scene.</p>
          <div className="mt-6">
            <Link 
              to={`/projects/${projectId}/scenes/new`}
              className="btn-primary inline-flex items-center"
            >
              <PlusIcon className="h-5 w-5 mr-1" />
              Create First Scene
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default ScenesKanban