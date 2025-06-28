// File: src/types/index.ts

// User and Authentication
export type User = {
  id: string;
  email: string;
  username: string;
  plan: string;
  tokensRemaining: number;
  createdAt: string;
};

// Projects
export type Project = {
  id: string;
  title: string;
  description: string;
  phase: 'idea' | 'expand' | 'story';
  genre?: string;
  targetAudience?: string;
  collaborators?: string[];
  isPublic: boolean;
  createdAt: string;
  updatedAt?: string;
  lastModified: string;
  progress: number;
};

// Story Objects
export type StoryObjectType = 'character' | 'location' | 'prop';

export type StoryObject = {
  id: string;
  projectId: string;
  name: string;
  description?: string;
  objectType: StoryObjectType;
  imageUrl?: string;
  // Type-specific fields
  age?: number;
  role?: string;
  motivation?: string;
  background?: string;
  personalityTraits?: string;
  address?: string;
  ambiance?: string;
  significance?: string;
  appearance?: string;
  history?: string;
  // Metadata
  createdAt: string;
  updatedAt?: string;
};

// Relationships between objects
export type Relationship = {
  sourceId: string;
  targetId: string;
  relationshipType: string;
  description?: string;
  createdAt: string;
  updatedAt?: string;
};

// Scenes
export type Scene = {
  id: string;
  projectId: string;
  title: string;
  content: string;
  order: number;
  emotionalIntensity: number;
  sceneType?: 'opening' | 'inciting' | 'progressive' | 'climax' | 'resolution';
  characters: string[]; // IDs of characters in this scene
  locations: string[]; // IDs of locations in this scene
  props: string[]; // IDs of props in this scene
  createdAt: string;
  updatedAt?: string;
};

// AI Analysis
export type AIAnalysis = {
  id: string;
  projectId: string;
  targetId: string; // Scene or project ID
  targetType: 'scene' | 'project' | 'story';
  criticType: string; // 'character', 'plot', 'pacing', etc.
  content: string;
  suggestions: string[];
  score?: number;
  createdAt: string;
};

// AI Task
export type AITask = {
  id: string;
  projectId: string;
  projectTitle: string;
  taskType: string;
  status: 'completed' | 'in-progress' | 'failed';
  createdAt: string;
};

// Comments
export type Comment = {
  id: string;
  projectId: string;
  targetId: string; // Scene, project, or object ID
  targetType: 'scene' | 'project' | 'character' | 'location' | 'prop';
  userId: string;
  username: string;
  content: string;
  createdAt: string;
  updatedAt?: string;
};

// Presence for real-time collaboration
export type UserPresence = {
  userId: string;
  username: string;
  location: string; // URL path or identifier
  status: 'active' | 'idle' | 'offline';
  lastActive: string;
};

// Token usage
export type TokenUsage = {
  tokensUsed: number;
  remainingTokens: number;
  operation: string;
  timestamp: string;
};

// Subscription plan
export type SubscriptionPlan = {
  id: string;
  name: string;
  description: string;
  price: number;
  tokensPerMonth: number;
  features: string[];
  isActive: boolean;
};
