// src/types/story.ts
export interface NarrativeOptions {
  narrativeVoice: 'first_person' | 'third_person_limited' | 'third_person_omniscient';
  proseStyle: 'minimal' | 'balanced' | 'descriptive';
  dialogStyle: 'direct' | 'indirect' | 'mixed';
  tonePreference: string;
}

export interface ChapterData {
  id: string;
  title: string;
  content: string;
  scenes: string[]; // Array of scene IDs that make up this chapter
  order: number;
}

export interface StoryMetadata {
  genre: string;
  theme: string;
  targetAudience: string;
  tone: string;
  uniqueElements: string[];
  keySymbols: string[];
  marketabilityScore?: number;
  qualityScore?: number;
}

export interface StoryData {
  id: string;
  projectId: string;
  title: string;
  premise: string;
  content: string;
  metadata: StoryMetadata;
  chapters?: ChapterData[];
  wordCount?: number;
  createdAt: string;
  updatedAt: string;
}

export interface StoryStats {
  wordCount: number;
  pageCount: number;
  readingTime: number;
  marketabilityScore: number;
  overallQuality: number;
}

// src/types/index.ts
export * from './auth';
export * from './project';
export * from './scene';
export * from './story';
export * from './object';
export * from './collaboration';
export * from './billing';

// Add these interface definitions if they don't already exist in your project

// src/types/project.ts (if not already defined)
export interface Project {
  id: string;
  title: string;
  description: string;
  genre: string;
  currentPhase: 'idea' | 'expand' | 'story';
  sceneCount: number;
  createdAt: string;
  updatedAt: string;
  premise?: string;
  wordCount?: number;
  targetAudience?: string;
}

// src/types/scene.ts (if not already defined)
export interface Scene {
  id: string;
  projectId: string;
  title: string;
  description: string;
  content?: string;
  order_index: number; 
  sceneType?: string;
  emotional_intensity?: number;
  conflict?: string;
  location?: string;
  hook?: string;
  characterFocus?: string[];
  wordCount?: number;
  createdAt: string;
  updatedAt?: string;
}

// src/types/object.ts (if not already defined)
export interface StoryObject {
  id: string;
  projectId: string;
  name: string;
  objectType: 'character' | 'location' | 'prop';
  description: string;
  importance: 'minor' | 'supporting' | 'major';
  status: 'active' | 'inactive';
  attributes: Record<string, any>;
  symbolism?: string;
  firstAppearance?: number; // Scene order where first appears
  createdAt: string;
  updatedAt?: string;
}

// src/services/api.ts additions
// Add these service functions to your existing API service

// Story Phase API endpoints
export const storyService = {
  getStory: async (projectId: string) => {
    return api.get(`/api/projects/${projectId}/story`);
  },
  
  generateStory: async (projectId: string, options: NarrativeOptions) => {
    return api.post(`/api/projects/${projectId}/generate-story`, { narrativeOptions: options });
  },
  
  updateStory: async (projectId: string, storyData: Partial<StoryData>) => {
    return api.put(`/api/projects/${projectId}/story`, storyData);
  },
  
  regenerateSection: async (projectId: string, chapterIndex: number, options: NarrativeOptions) => {
    return api.post(`/api/projects/${projectId}/regenerate-section`, {
      chapterIndex,
      narrativeOptions: options
    });
  },
  
  exportStory: async (projectId: string, format: 'pdf' | 'docx' | 'epub' | 'txt') => {
    return api.get(`/api/projects/${projectId}/export-story?format=${format}`, {
      responseType: 'blob'
    });
  }
};

// If you don't already have these hooks defined in your project, add them:

// src/hooks/useApi.ts
import { useCallback } from 'react';
import { api } from '../services/api';

export const useApi = () => {
  const get = useCallback(async (url: string, config = {}) => {
    try {
      const response = await api.get(url, config);
      return response;
    } catch (error) {
      console.error(`API GET Error (${url}):`, error);
      throw error;
    }
  }, []);
  
  const post = useCallback(async (url: string, data = {}, config = {}) => {
    try {
      const response = await api.post(url, data, config);
      return response;
    } catch (error) {
      console.error(`API POST Error (${url}):`, error);
      throw error;
    }
  }, []);
  
  const put = useCallback(async (url: string, data = {}, config = {}) => {
    try {
      const response = await api.put(url, data, config);
      return response;
    } catch (error) {
      console.error(`API PUT Error (${url}):`, error);
      throw error;
    }
  }, []);
  
  const del = useCallback(async (url: string, config = {}) => {
    try {
      const response = await api.delete(url, config);
      return response;
    } catch (error) {
      console.error(`API DELETE Error (${url}):`, error);
      throw error;
    }
  }, []);
  
  return { get, post, put, delete: del };
};

// src/hooks/useToast.ts (simple implementation)
import { useCallback } from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

export const useToast = () => {
  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    // This would interact with your toast notification system
    // For simplicity, we're just logging to console here
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // In a real implementation, this would trigger your UI toast component
    // Example: toast.show({ message, type });
  }, []);
  
  return { showToast };
};