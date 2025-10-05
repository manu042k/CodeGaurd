import { 
  Project, 
  Analysis, 
  CreateProjectRequest, 
  UpdateProjectRequest, 
  StartAnalysisRequest 
} from '@/types/project'

// Mock API base URL - will be replaced with actual backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new ApiError(response.status, `API Error: ${response.statusText}`)
  }

  return response.json()
}

// Project API functions
export const projectApi = {
  // Get all projects for current user
  async getProjects(): Promise<Project[]> {
    return apiRequest<Project[]>('/api/projects')
  },

  // Get single project by ID
  async getProject(id: string): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${id}`)
  },

  // Create new project
  async createProject(data: CreateProjectRequest): Promise<Project> {
    return apiRequest<Project>('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Update existing project
  async updateProject(id: string, data: UpdateProjectRequest): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  // Delete project
  async deleteProject(id: string): Promise<void> {
    return apiRequest<void>(`/api/projects/${id}`, {
      method: 'DELETE',
    })
  },

  // Get project analyses
  async getProjectAnalyses(projectId: string): Promise<Analysis[]> {
    return apiRequest<Analysis[]>(`/api/projects/${projectId}/analyses`)
  },
}

// Analysis API functions
export const analysisApi = {
  // Start new analysis
  async startAnalysis(data: StartAnalysisRequest): Promise<Analysis> {
    return apiRequest<Analysis>('/api/analysis/start', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Get analysis by ID
  async getAnalysis(id: string): Promise<Analysis> {
    return apiRequest<Analysis>(`/api/analysis/${id}`)
  },

  // Get analysis status (for polling)
  async getAnalysisStatus(id: string): Promise<{ status: string; progress: number }> {
    return apiRequest<{ status: string; progress: number }>(`/api/analysis/${id}/status`)
  },

  // Cancel running analysis
  async cancelAnalysis(id: string): Promise<void> {
    return apiRequest<void>(`/api/analysis/${id}/cancel`, {
      method: 'POST',
    })
  },
}

// Mock data for development (remove when backend is ready)
export const mockData = {
  projects: [
    {
      id: '1',
      name: 'CodeGuard Frontend',
      description: 'Next.js frontend application',
      repository: {
        id: 123,
        name: 'CodeGaurd',
        full_name: 'manu042k/CodeGaurd',
        description: 'Security analysis platform',
        private: false,
        html_url: 'https://github.com/manu042k/CodeGaurd',
        clone_url: 'https://github.com/manu042k/CodeGaurd.git',
        language: 'TypeScript',
        stargazers_count: 5,
        forks_count: 1,
        updated_at: '2025-10-05T14:30:00Z',
        created_at: '2025-10-05T10:00:00Z',
        owner: {
          login: 'manu042k',
          avatar_url: 'https://github.com/manu042k.png',
        },
      },
      userId: 'user1',
      createdAt: '2025-10-05T10:00:00Z',
      updatedAt: '2025-10-05T14:30:00Z',
      analysisCount: 2,
      status: 'completed' as const,
      settings: {
        analysisConfig: {
          enabledAgents: ['CodeQuality', 'Security', 'Architecture', 'Documentation'] as const,
          excludePatterns: ['node_modules', '*.test.*'],
          includePaths: ['src', 'pages', 'components'],
        },
        notifications: {
          onComplete: true,
          onFailure: true,
        },
      },
      latestAnalysis: {
        id: 'analysis-1',
        projectId: '1',
        status: 'completed' as const,
        startedAt: '2025-10-05T14:00:00Z',
        completedAt: '2025-10-05T14:15:00Z',
        duration: 900, // 15 minutes
        agents: [],
        overallScore: 85,
        summary: 'Good code quality with some security improvements needed.',
      },
    },
  ] as Project[],
}
