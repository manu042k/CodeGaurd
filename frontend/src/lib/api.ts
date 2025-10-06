import {
  Project,
  Analysis,
  CreateProjectRequest,
  UpdateProjectRequest,
  StartAnalysisRequest,
} from "@/types/project";

// Mock API base URL - will be replaced with actual backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// Types for auth
interface AuthUser {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  github_id: string;
  created_at: string;
  updated_at?: string;
}

interface AuthResponse {
  auth_url: string;
  state: string;
}

// Auth utility functions
function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("auth_token", token);
}

function removeAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("auth_token");
}

// Enhanced apiRequest with auth support
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    headers,
    ...options,
  });

  if (!response.ok) {
    if (response.status === 401) {
      // Token is invalid, remove it
      removeAuthToken();
      // Redirect to login or throw specific error
      throw new ApiError(401, "Authentication required");
    }
    throw new ApiError(response.status, `API Error: ${response.statusText}`);
  }

  return response.json();
}

// Project API functions
export const projectApi = {
  // Get all projects for current user
  async getProjects(): Promise<Project[]> {
    return apiRequest<Project[]>("/api/projects");
  },

  // Get single project by ID
  async getProject(id: string): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${id}`);
  },

  // Create new project
  async createProject(data: CreateProjectRequest): Promise<Project> {
    return apiRequest<Project>("/api/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Update existing project
  async updateProject(
    id: string,
    data: UpdateProjectRequest
  ): Promise<Project> {
    return apiRequest<Project>(`/api/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  // Delete project
  async deleteProject(id: string): Promise<void> {
    return apiRequest<void>(`/api/projects/${id}`, {
      method: "DELETE",
    });
  },

  // Get project analyses
  async getProjectAnalyses(projectId: string): Promise<Analysis[]> {
    return apiRequest<Analysis[]>(`/api/projects/${projectId}/analyses`);
  },
};

// Analysis API functions
export const analysisApi = {
  // Start new analysis
  async startAnalysis(data: StartAnalysisRequest): Promise<Analysis> {
    return apiRequest<Analysis>("/api/analyses", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Get analysis by ID
  async getAnalysis(id: string): Promise<Analysis> {
    return apiRequest<Analysis>(`/api/analyses/${id}`);
  },

  // Get analysis status (for polling)
  async getAnalysisStatus(
    id: string
  ): Promise<{
    status: string;
    progress: number;
    current_agent?: string;
    message?: string;
  }> {
    return apiRequest<{
      status: string;
      progress: number;
      current_agent?: string;
      message?: string;
    }>(`/api/analyses/${id}/status`);
  },

  // Cancel running analysis
  async cancelAnalysis(id: string): Promise<void> {
    return apiRequest<void>(`/api/analyses/${id}`, {
      method: "DELETE",
    });
  },
};

// Auth API functions
export const authApi = {
  // Initialize GitHub OAuth flow
  async initiateGitHubLogin(): Promise<AuthResponse> {
    return apiRequest<AuthResponse>("/api/auth/github/login");
  },

  // Get current authenticated user
  async getCurrentUser(): Promise<AuthUser> {
    return apiRequest<AuthUser>("/api/auth/me");
  },

  // Verify token validity
  async verifyToken(): Promise<{ valid: boolean; user_id: string }> {
    return apiRequest<{ valid: boolean; user_id: string }>("/api/auth/verify");
  },

  // Logout user
  async logout(): Promise<{ message: string }> {
    const result = await apiRequest<{ message: string }>("/api/auth/logout", {
      method: "POST",
    });
    removeAuthToken();
    return result;
  },

  // Client-side auth helpers
  setToken: setAuthToken,
  getToken: getAuthToken,
  removeToken: removeAuthToken,

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return getAuthToken() !== null;
  },
};

// GitHub API functions
export const githubApi = {
  // Get user's repositories from GitHub
  async getRepositories(): Promise<any[]> {
    return apiRequest<any[]>("/api/github/repos");
  },

  // Get specific repository
  async getRepository(repoId: number): Promise<any> {
    return apiRequest<any>(`/api/github/repos/${repoId}`);
  },
};

// Mock data for development (remove when backend is ready)
export const mockData = {
  projects: [
    {
      id: "1",
      name: "CodeGuard Frontend",
      description: "Next.js frontend application",
      repository: {
        id: 123,
        name: "CodeGaurd",
        full_name: "manu042k/CodeGaurd",
        description: "Security analysis platform",
        private: false,
        html_url: "https://github.com/manu042k/CodeGaurd",
        clone_url: "https://github.com/manu042k/CodeGaurd.git",
        language: "TypeScript",
        stargazers_count: 5,
        forks_count: 1,
        updated_at: "2025-10-05T14:30:00Z",
        created_at: "2025-10-05T10:00:00Z",
        owner: {
          login: "manu042k",
          avatar_url: "https://github.com/manu042k.png",
        },
      },
      userId: "user1",
      createdAt: "2025-10-05T10:00:00Z",
      updatedAt: "2025-10-05T14:30:00Z",
      analysisCount: 2,
      status: "completed" as const,
      settings: {
        analysisConfig: {
          enabledAgents: [
            "CodeQuality",
            "Security",
            "Architecture",
            "Documentation",
          ] as const,
          excludePatterns: ["node_modules", "*.test.*"],
          includePaths: ["src", "pages", "components"],
        },
        notifications: {
          onComplete: true,
          onFailure: true,
        },
      },
      latestAnalysis: {
        id: "analysis-1",
        projectId: "1",
        status: "completed" as const,
        startedAt: "2025-10-05T14:00:00Z",
        completedAt: "2025-10-05T14:15:00Z",
        duration: 900, // 15 minutes
        agents: [],
        overallScore: 85,
        summary: "Good code quality with some security improvements needed.",
      },
    },
  ] as Project[],
};
