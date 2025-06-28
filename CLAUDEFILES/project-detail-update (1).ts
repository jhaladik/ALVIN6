// src/components/pages/ProjectDetail.tsx (Partial with AI button addition)
// Note: This is a partial implementation focusing on adding the AI features link

import { Link } from 'react-router-dom';
import { SparklesIcon } from '@heroicons/react/24/outline';

// ... rest of imports ...

const ProjectDetail: React.FC = () => {
  // ... existing component code ...

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Project Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project?.title}</h1>
          <p className="text-gray-600 mt-1">{project?.genre} · Created {formatDate(project?.createdAt)}</p>
        </div>
        <div className="flex space-x-3">
          {/* Add AI Features button */}
          <Link to={`/projects/${projectId}/ai`}>
            <Button variant="secondary" className="flex items-center">
              <SparklesIcon className="h-5 w-5 mr-2" />
              AI Features
            </Button>
          </Link>
          
          {/* Existing buttons */}
          <Button variant="primary" onClick={handleEditProject}>
            Edit Project
          </Button>
        </div>
      </div>

      {/* Rest of the component... */}
    </div>
  );
};

export default ProjectDetail;
