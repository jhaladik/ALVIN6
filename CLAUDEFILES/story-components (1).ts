// src/components/story/StoryStyleSelector.tsx
import React, { useState } from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/outline';
import { NarrativeOptions } from '../../types';

interface StoryStyleSelectorProps {
  options: NarrativeOptions;
  onChange: (options: Partial<NarrativeOptions>) => void;
  disabled?: boolean;
}

const StoryStyleSelector: React.FC<StoryStyleSelectorProps> = ({
  options,
  onChange,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const narrativeVoiceOptions = [
    { id: 'first_person', label: 'First Person' },
    { id: 'third_person_limited', label: 'Third Person Limited' },
    { id: 'third_person_omniscient', label: 'Third Person Omniscient' }
  ];
  
  const proseStyleOptions = [
    { id: 'minimal', label: 'Minimal' },
    { id: 'balanced', label: 'Balanced' },
    { id: 'descriptive', label: 'Descriptive' }
  ];
  
  const dialogStyleOptions = [
    { id: 'direct', label: 'Direct' },
    { id: 'indirect', label: 'Indirect' },
    { id: 'mixed', label: 'Mixed' }
  ];
  
  const toneOptions = [
    { id: 'dramatic', label: 'Dramatic' },
    { id: 'whimsical', label: 'Whimsical' },
    { id: 'serious', label: 'Serious' },
    { id: 'humorous', label: 'Humorous' },
    { id: 'melancholic', label: 'Melancholic' },
    { id: 'suspenseful', label: 'Suspenseful' }
  ];
  
  return (
    <div className="relative">
      <button
        type="button"
        className={`flex items-center gap-1 px-2 py-1 text-sm rounded border ${
          disabled 
            ? 'border-gray-200 text-gray-400 bg-gray-50' 
            : 'border-gray-300 text-gray-700 hover:bg-gray-50'
        }`}
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
      >
        <span>Narrative Style</span>
        <ChevronDownIcon className="h-4 w-4" />
      </button>
      
      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white rounded-md shadow-lg z-10 p-2">
          <div className="text-xs font-medium text-gray-500 mb-2 pb-1 border-b">
            Narrative Style Options
          </div>
          
          {/* Narrative Voice */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Narrative Voice
            </label>
            <select
              value={options.narrativeVoice}
              onChange={(e) => onChange({ narrativeVoice: e.target.value as any })}
              className="w-full text-sm rounded border border-gray-300 p-1"
            >
              {narrativeVoiceOptions.map(option => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Prose Style */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Prose Style
            </label>
            <select
              value={options.proseStyle}
              onChange={(e) => onChange({ proseStyle: e.target.value as any })}
              className="w-full text-sm rounded border border-gray-300 p-1"
            >
              {proseStyleOptions.map(option => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Dialog Style */}
          <div className="mb-3">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Dialog Style
            </label>
            <select
              value={options.dialogStyle}
              onChange={(e) => onChange({ dialogStyle: e.target.value as any })}
              className="w-full text-sm rounded border border-gray-300 p-1"
            >
              {dialogStyleOptions.map(option => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Tone */}
          <div className="mb-2">
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Tone
            </label>
            <select
              value={options.tonePreference}
              onChange={(e) => onChange({ tonePreference: e.target.value })}
              className="w-full text-sm rounded border border-gray-300 p-1"
            >
              {toneOptions.map(option => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="pt-2 border-t flex justify-end">
            <button
              type="button"
              className="text-xs text-indigo-600 hover:text-indigo-800"
              onClick={() => setIsOpen(false)}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryStyleSelector;

// src/components/story/ChapterOrganizer.tsx
import React from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { ChapterData } from '../../types';
import { RefreshIcon, PencilIcon } from '@heroicons/react/24/outline';

interface ChapterOrganizerProps {
  chapters: ChapterData[];
  onChapterSelect: (index: number) => void;
  onRegenerateChapter: (index: number) => void;
}

const ChapterOrganizer: React.FC<ChapterOrganizerProps> = ({
  chapters,
  onChapterSelect,
  onRegenerateChapter
}) => {
  const handleDragEnd = (result: any) => {
    // In a real implementation, this would reorder the chapters
    // Not implementing the full drag & drop functionality here for brevity
    if (!result.destination) return;
    // Would call a parent function to update chapter order
  };
  
  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="chapters">
        {(provided) => (
          <div
            {...provided.droppableProps}
            ref={provided.innerRef}
            className="space-y-2"
          >
            {chapters.map((chapter, index) => (
              <Draggable key={chapter.id} draggableId={chapter.id} index={index}>
                {(provided) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className="bg-gray-50 rounded p-2 cursor-pointer border border-gray-200 hover:border-indigo-300 transition-colors"
                    onClick={() => onChapterSelect(index)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1 mr-2">
                        <div className="text-xs text-gray-500">Chapter {index + 1}</div>
                        <div className="text-sm font-medium truncate">{chapter.title}</div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRegenerateChapter(index);
                        }}
                        className="text-gray-500 hover:text-indigo-600 p-1"
                        title="Regenerate chapter"
                      >
                        <RefreshIcon className="h-4 w-4" />
                      </button>
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
  );
};

export default ChapterOrganizer;

// src/components/story/EditorToolbar.tsx
import React from 'react';
import { Editor } from '@tiptap/react';
import {
  BoldIcon,
  ItalicIcon,
  ListBulletIcon,
  ListOrderedIcon,
  QuoteIcon,
  LinkIcon,
  ParagraphIcon,
  Heading1Icon,
  Heading2Icon,
  Heading3Icon,
  DividerHorizontalIcon,
  UndoIcon,
  RedoIcon,
} from './EditorIcons'; // You'd create these icons or import from a library

interface EditorToolbarProps {
  editor: Editor | null;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({ editor }) => {
  if (!editor) {
    return null;
  }
  
  return (
    <div className="flex flex-wrap items-center gap-1">
      <button
        onClick={() => editor.chain().focus().toggleBold().run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('bold') ? 'bg-gray-100' : ''}`}
        title="Bold"
      >
        <BoldIcon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().toggleItalic().run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('italic') ? 'bg-gray-100' : ''}`}
        title="Italic"
      >
        <ItalicIcon className="h-4 w-4" />
      </button>
      
      <span className="border-l border-gray-200 mx-1 h-5"></span>
      
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('heading', { level: 1 }) ? 'bg-gray-100' : ''}`}
        title="Heading 1"
      >
        <Heading1Icon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('heading', { level: 2 }) ? 'bg-gray-100' : ''}`}
        title="Heading 2"
      >
        <Heading2Icon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('heading', { level: 3 }) ? 'bg-gray-100' : ''}`}
        title="Heading 3"
      >
        <Heading3Icon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().setParagraph().run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('paragraph') ? 'bg-gray-100' : ''}`}
        title="Paragraph"
      >
        <ParagraphIcon className="h-4 w-4" />
      </button>
      
      <span className="border-l border-gray-200 mx-1 h-5"></span>
      
      <button
        onClick={() => editor.chain().focus().toggleBulletList().run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('bulletList') ? 'bg-gray-100' : ''}`}
        title="Bullet List"
      >
        <ListBulletIcon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().toggleOrderedList().run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('orderedList') ? 'bg-gray-100' : ''}`}
        title="Ordered List"
      >
        <ListOrderedIcon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().toggleBlockquote().run()}
        className={`p-1 rounded hover:bg-gray-100 ${editor.isActive('blockquote') ? 'bg-gray-100' : ''}`}
        title="Quote"
      >
        <QuoteIcon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().setHorizontalRule().run()}
        className="p-1 rounded hover:bg-gray-100"
        title="Horizontal Rule"
      >
        <DividerHorizontalIcon className="h-4 w-4" />
      </button>
      
      <span className="border-l border-gray-200 mx-1 h-5"></span>
      
      <button
        onClick={() => editor.chain().focus().undo().run()}
        disabled={!editor.can().undo()}
        className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
        title="Undo"
      >
        <UndoIcon className="h-4 w-4" />
      </button>
      
      <button
        onClick={() => editor.chain().focus().redo().run()}
        disabled={!editor.can().redo()}
        className="p-1 rounded hover:bg-gray-100 disabled:opacity-30"
        title="Redo"
      >
        <RedoIcon className="h-4 w-4" />
      </button>
    </div>
  );
};

export default EditorToolbar;

// src/components/story/EditorIcons.tsx
import React from 'react';

interface IconProps {
  className?: string;
}

// Simple implementations of icons - in a real project, you'd use a library like heroicons
export const BoldIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M6 12H14C16.2091 12 18 10.2091 18 8C18 5.79086 16.2091 4 14 4H6V12ZM6 12H15C17.2091 12 19 13.7909 19 16C19 18.2091 17.2091 20 15 20H6V12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const ItalicIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M19 4H10M14 20H5M15 4L9 20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const ListBulletIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M8 6H21M8 12H21M8 18H21M3 6H3.01M3 12H3.01M3 18H3.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const ListOrderedIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 6H21M10 12H21M10 18H21M4 6H5M4 18H5M4 12H5.5M5.5 12C5.5 12 6 12.1716 6 12.5C6 12.8284 5.5 13 5.5 13M5.5 13H5M5.5 13C5.5 13 6 13.1716 6 13.5C6 13.8284 5.5 14 5.5 14H4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const QuoteIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 21C9 21 9 15 9 15V9C9 9 9 3 3 3M15 21C21 21 21 15 21 15V9C21 9 21 3 15 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const LinkIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 13C10.8631 13.3039 11.8037 13.8637 12.5 14.5C13.1963 15.1363 13.6961 16.0869 14 17M9.5 10C8.66019 9.72755 7.66406 9.03325 7 8.5C5.5 7.5 4.5 6 4.5 4.5C4.5 3 5.5 2 7 2C8.5 2 11 4.5 11 4.5M13.5 21C13.5 21 16 18.5 17.5 18.5C19 18.5 20 19.5 20 21C20 22.5 19 23.5 17.5 24.5C16.8333 25 15.8333 25.7 15 26" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const ParagraphIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 6H20M12 12H20M4 18H20M4 6L8 10L4 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const Heading1Icon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 12H20M4 18V6M12 18V6M16 10V18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const Heading2Icon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 12H14M4 18V6M9 18V6M14 12C14 12 17 12 17 15C17 18 14 18 14 18H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const Heading3Icon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 12H12M4 18V6M8 18V6M13 8H19C19 8 19 10 17 11C19 12 19 14 19 14H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const DividerHorizontalIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 12H21M5 8H19M8 4H16M8 16H16M5 20H19" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const UndoIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 10H16C18.7614 10 21 12.2386 21 15C21 17.7614 18.7614 20 16 20H12M3 10L7 6M3 10L7 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const RedoIcon: React.FC<IconProps> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 10H8C5.23858 10 3 12.2386 3 15C3 17.7614 5.23858 20 8 20H12M21 10L17 6M21 10L17 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

// src/components/story/StoryStats.tsx
import React from 'react';
import { StoryStats as StoryStatsType } from '../../types';

interface StoryStatsProps {
  stats: StoryStatsType;
}

const StoryStats: React.FC<StoryStatsProps> = ({ stats }) => {
  const { wordCount, pageCount, readingTime, marketabilityScore, overallQuality } = stats;
  
  return (
    <div className="bg-white rounded-xl shadow-lg p-4">
      <h2 className="text-lg font-semibold mb-3">Story Statistics</h2>
      
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
        <div className="bg-indigo-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-indigo-600">
            {wordCount.toLocaleString()}
          </div>
          <div className="text-sm text-indigo-800">Words</div>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">
            {pageCount}
          </div>
          <div className="text-sm text-blue-800">Pages</div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-green-600">
            {readingTime}
          </div>
          <div className="text-sm text-green-800">Min Reading</div>
        </div>
        
        <div className="bg-yellow-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-yellow-600">
            {marketabilityScore > 0 ? marketabilityScore.toFixed(1) : 'N/A'}
          </div>
          <div className="text-sm text-yellow-800">Marketability</div>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-2xl font-bold text-red-600">
            {overallQuality > 0 ? overallQuality.toFixed(1) : 'N/A'}
          </div>
          <div className="text-sm text-red-800">Quality</div>
        </div>
      </div>
    </div>
  );
};

export default StoryStats;

// src/components/story/StoryMetadataPanel.tsx
import React, { useState } from 'react';
import { PencilIcon, CheckIcon, XIcon } from '@heroicons/react/24/outline';

interface StoryMetadataProps {
  metadata: {
    genre: string;
    theme: string;
    targetAudience: string;
    tone: string;
    uniqueElements: string[];
    keySymbols: string[];
  };
  onUpdate: (metadata: any) => void;
}

const StoryMetadataPanel: React.FC<StoryMetadataProps> = ({ metadata, onUpdate }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedMetadata, setEditedMetadata] = useState(metadata);
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setEditedMetadata(prev => ({ ...prev, [name]: value }));
  };
  
  const handleArrayInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>, field: 'uniqueElements' | 'keySymbols') => {
    const values = e.target.value.split(',').map(item => item.trim()).filter(Boolean);
    setEditedMetadata(prev => ({ ...prev, [field]: values }));
  };
  
  const handleSave = () => {
    onUpdate(editedMetadata);
    setIsEditing(false);
  };
  
  const handleCancel = () => {
    setEditedMetadata(metadata);
    setIsEditing(false);
  };
  
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="font-medium text-gray-900">Story Metadata</h3>
        {isEditing ? (
          <div className="flex space-x-1">
            <button
              onClick={handleSave}
              className="p-1 text-green-600 hover:text-green-800"
              title="Save"
            >
              <CheckIcon className="h-4 w-4" />
            </button>
            <button
              onClick={handleCancel}
              className="p-1 text-red-600 hover:text-red-800"
              title="Cancel"
            >
              <XIcon className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsEditing(true)}
            className="p-1 text-gray-500 hover:text-indigo-600"
            title="Edit metadata"
          >
            <PencilIcon className="h-4 w-4" />
          </button>
        )}
      </div>
      
      <div className="space-y-3">
        {/* Genre */}
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Genre</div>
          {isEditing ? (
            <input
              type="text"
              name="genre"
              value={editedMetadata.genre}
              onChange={handleInputChange}
              className="w-full p-1 text-sm border border-gray-300 rounded"
            />
          ) : (
            <div className="text-sm">{metadata.genre || 'Not specified'}</div>
          )}
        </div>
        
        {/* Theme */}
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Theme</div>
          {isEditing ? (
            <input
              type="text"
              name="theme"
              value={editedMetadata.theme}
              onChange={handleInputChange}
              className="w-full p-1 text-sm border border-gray-300 rounded"
            />
          ) : (
            <div className="text-sm">{metadata.theme || 'Not specified'}</div>
          )}
        </div>
        
        {/* Target Audience */}
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Target Audience</div>
          {isEditing ? (
            <input
              type="text"
              name="targetAudience"
              value={editedMetadata.targetAudience}
              onChange={handleInputChange}
              className="w-full p-1 text-sm border border-gray-300 rounded"
            />
          ) : (
            <div className="text-sm">{metadata.targetAudience || 'Not specified'}</div>
          )}
        </div>
        
        {/* Tone */}
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Tone</div>
          {isEditing ? (
            <input
              type="text"
              name="tone"
              value={editedMetadata.tone}
              onChange={handleInputChange}
              className="w-full p-1 text-sm border border-gray-300 rounded"
            />
          ) : (
            <div className="text-sm">{metadata.tone || 'Not specified'}</div>
          )}
        </div>
        
        {/* Unique Elements */}
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Unique Elements</div>
          {isEditing ? (
            <textarea
              name="uniqueElements"
              value={editedMetadata.uniqueElements.join(', ')}
              onChange={(e) => handleArrayInputChange(e, 'uniqueElements')}
              className="w-full p-1 text-sm border border-gray-300 rounded"
              rows={2}
              placeholder="Comma-separated list"
            />
          ) : (
            <div className="text-sm">
              {metadata.uniqueElements && metadata.uniqueElements.length > 0
                ? metadata.uniqueElements.join(', ')
                : 'None'}
            </div>
          )}
        </div>
        
        {/* Key Symbols */}
        <div>
          <div className="text-xs font-medium text-gray-500 mb-1">Key Symbols</div>
          {isEditing ? (
            <textarea
              name="keySymbols"
              value={editedMetadata.keySymbols.join(', ')}
              onChange={(e) => handleArrayInputChange(e, 'keySymbols')}
              className="w-full p-1 text-sm border border-gray-300 rounded"
              rows={2}
              placeholder="Comma-separated list"
            />
          ) : (
            <div className="text-sm">
              {metadata.keySymbols && metadata.keySymbols.length > 0
                ? metadata.keySymbols.join(', ')
                : 'None'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StoryMetadataPanel;

// src/components/story/ExportDialog.tsx
import React, { useState } from 'react';
import {
  DocumentTextIcon,
  DocumentIcon,
  BookOpenIcon,
  CodeIcon,
  XIcon
} from '@heroicons/react/24/outline';

interface ExportDialogProps {
  onExport: (format: 'pdf' | 'docx' | 'epub' | 'txt') => void;
  onClose: () => void;
}

const ExportDialog: React.FC<ExportDialogProps> = ({ onExport, onClose }) => {
  const [selectedFormat, setSelectedFormat] = useState<'pdf' | 'docx' | 'epub' | 'txt'>('pdf');
  
  const exportFormats = [
    { id: 'pdf', label: 'PDF Document', icon: DocumentTextIcon, description: 'Best for printing or sharing' },
    { id: 'docx', label: 'Word Document', icon: DocumentIcon, description: 'Editable in Microsoft Word' },
    { id: 'epub', label: 'ePub eBook', icon: BookOpenIcon, description: 'For e-readers and mobile devices' },
    { id: 'txt', label: 'Plain Text', icon: CodeIcon, description: 'Simple text format, no formatting' }
  ];
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-medium">Export Story</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <XIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-4">
          <p className="text-gray-600 mb-4">Select an export format:</p>
          
          <div className="space-y-2">
            {exportFormats.map((format) => (
              <div
                key={format.id}
                className={`flex items-center p-3 border rounded cursor-pointer transition-colors ${
                  selectedFormat === format.id
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 hover:border-indigo-300'
                }`}
                onClick={() => setSelectedFormat(format.id as any)}
              >
                <format.icon className="h-6 w-6 text-indigo-500 mr-3" />
                <div>
                  <div className="font-medium">{format.label}</div>
                  <div className="text-xs text-gray-500">{format.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end space-x-2 rounded-b-xl">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={() => onExport(selectedFormat)}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Export
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExportDialog;

// src/components/story/SectionRegenerateDialog.tsx
import React, { useState } from 'react';
import { NarrativeOptions } from '../../types';
import { XIcon, RefreshIcon } from '@heroicons/react/24/outline';

interface SectionRegenerateDialogProps {
  currentOptions: NarrativeOptions;
  onRegenerate: (options: Partial<NarrativeOptions>) => void;
  onClose: () => void;
}

const SectionRegenerateDialog: React.FC<SectionRegenerateDialogProps> = ({
  currentOptions,
  onRegenerate,
  onClose
}) => {
  const [options, setOptions] = useState<NarrativeOptions>(currentOptions);
  
  const narrativeVoiceOptions = [
    { id: 'first_person', label: 'First Person' },
    { id: 'third_person_limited', label: 'Third Person Limited' },
    { id: 'third_person_omniscient', label: 'Third Person Omniscient' }
  ];
  
  const proseStyleOptions = [
    { id: 'minimal', label: 'Minimal' },
    { id: 'balanced', label: 'Balanced' },
    { id: 'descriptive', label: 'Descriptive' }
  ];
  
  const dialogStyleOptions = [
    { id: 'direct', label: 'Direct' },
    { id: 'indirect', label: 'Indirect' },
    { id: 'mixed', label: 'Mixed' }
  ];
  
  const toneOptions = [
    { id: 'dramatic', label: 'Dramatic' },
    { id: 'whimsical', label: 'Whimsical' },
    { id: 'serious', label: 'Serious' },
    { id: 'humorous', label: 'Humorous' },
    { id: 'melancholic', label: 'Melancholic' },
    { id: 'suspenseful', label: 'Suspenseful' }
  ];
  
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setOptions(prev => ({ ...prev, [name]: value }));
  };
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
        <div className="flex justify-between items-center p-4 border-b">
          <h3 className="text-lg font-medium">Regenerate Section</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <XIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="p-4">
          <p className="text-gray-600 mb-4">Adjust the style options for this section:</p>
          
          <div className="space-y-4">
            {/* Narrative Voice */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Narrative Voice
              </label>
              <select
                name="narrativeVoice"
                value={options.narrativeVoice}
                onChange={handleChange}
                className="w-full p-2 border border-gray-300 rounded"
              >
                {narrativeVoiceOptions.map(option => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Prose Style */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Prose Style
              </label>
              <select
                name="proseStyle"
                value={options.proseStyle}
                onChange={handleChange}
                className="w-full p-2 border border-gray-300 rounded"
              >
                {proseStyleOptions.map(option => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Dialog Style */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Dialog Style
              </label>
              <select
                name="dialogStyle"
                value={options.dialogStyle}
                onChange={handleChange}
                className="w-full p-2 border border-gray-300 rounded"
              >
                {dialogStyleOptions.map(option => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Tone */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tone
              </label>
              <select
                name="tonePreference"
                value={options.tonePreference}
                onChange={handleChange}
                className="w-full p-2 border border-gray-300 rounded"
              >
                {toneOptions.map(option => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t bg-gray-50 flex justify-end space-x-2 rounded-b-xl">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded text-gray-700 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={() => onRegenerate(options)}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 flex items-center"
          >
            <RefreshIcon className="h-4 w-4 mr-1" />
            Regenerate
          </button>
        </div>
      </div>
    </div>
  );
};

export default SectionRegenerateDialog;