import { getSession } from "next-auth/react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
export interface BackendUser {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  github_id: string;
  created_at: string;
  updated_at?: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  github_repo_id: number;
  github_url: string;
  github_full_name: string;
  status: "never_analyzed" | "analyzing" | "completed" | "failed";
  analysis_count: number;
  created_at: string;
  updated_at?: string;
  latest_analysis?: {
    id: string;
    startedAt: string;
    completedAt?: string;
    overallScore?: number;
  };
  settings: {
    analysisConfig: {
      enabledAgents: string[];
      excludePatterns: string[];
      includePaths: string[];
    };
    notifications: {
      onComplete: boolean;
      onFailure: boolean;
    };
  };
}

export interface ProjectCreate {
  name: string;
  description?: string;
  github_repo_id: number;
  github_url: string;
  github_full_name: string;
  settings?: {
    analysisConfig?: {
      enabledAgents?: string[];
      excludePatterns?: string[];
      includePaths?: string[];
    };
    notifications?: {
      onComplete?: boolean;
      onFailure?: boolean;
    };
  };
}

export interface Issue {
  id: string;
  type: "error" | "warning" | "info" | "suggestion";
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  description: string;
  file_path?: string;
  line_number?: number;
  column_number?: number;
  rule?: string;
}

export interface AgentResult {
  id: string;
  agent_name: "CodeQuality" | "Security" | "Architecture" | "Documentation";
  status: "pending" | "running" | "completed" | "failed";
  score?: number;
  summary?: string;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  error?: string;
  issues: Issue[];
}

export interface Analysis {
  id: string;
  project_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  started_at: string;
  completed_at?: string;
  duration?: number;
  overall_score?: number;
  summary?: string;
  error?: string;
  agent_results: AgentResult[];
}

// Backend API client with NextAuth integration
export class BackendAPI {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const session = await getSession();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (session?.backendToken) {
      headers.Authorization = `Bearer ${session.backendToken}`;
    } else if (session?.accessToken) {
      // Fallback to GitHub access token if backend token not available
      headers.Authorization = `Bearer ${session.accessToken}`;
    }

    return headers;
  }

  private async apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = await this.getAuthHeaders();

    const response = await fetch(url, {
      headers: {
        ...headers,
        ...(options.headers as Record<string, string>),
      },
      ...options,
    });

    if (!response.ok) {
      // Handle 401 Unauthorized - session expired
      if (response.status === 401) {
        // Set flag for logout notification
        if (typeof window !== "undefined") {
          sessionStorage.setItem("autoLoggedOut", "true");
        }
        // Import signOut dynamically to avoid circular dependencies
        const { signOut } = await import("next-auth/react");
        await signOut({
          redirect: false,
          callbackUrl: "/auth/signin",
        });
        // Redirect to signin page
        if (typeof window !== "undefined") {
          window.location.href = "/auth/signin";
        }
        throw new Error("Session expired. Please sign in again.");
      }

      let errorText = "Unknown error";
      try {
        const errorData = await response.json();
        errorText = JSON.stringify(errorData, null, 2);
        console.error(`❌ API Error Details:`, errorData);
      } catch {
        errorText = await response.text().catch(() => "Unknown error");
      }
      console.error(
        `❌ API Error: ${response.status} ${response.statusText}`,
        errorText
      );
      throw new Error(
        `API Error: ${response.status} ${response.statusText} - ${errorText}`
      );
    }

    const data = await response.json();
    return data;
  }

  // Project API methods
  async getProjects(): Promise<Project[]> {
    return this.apiRequest<Project[]>("/api/projects/");
  }

  async getProject(id: string): Promise<Project> {
    return this.apiRequest<Project>(`/api/projects/${id}/`);
  }

  async createProject(data: ProjectCreate): Promise<Project> {
    return this.apiRequest<Project>("/api/projects/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    return this.apiRequest<Project>(`/api/projects/${id}/`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: string): Promise<void> {
    try {
      const result = await this.apiRequest<void>(`/api/projects/${id}/`, {
        method: "DELETE",
      });
      return result;
    } catch (error) {
      console.error("❌ BackendAPI.deleteProject failed:", error);
      throw error;
    }
  }

  // Analysis API methods
  async startAnalysis(data: { projectId: string }): Promise<Analysis> {
    return this.apiRequest<Analysis>("/api/analyses/", {
      method: "POST",
      body: JSON.stringify({ project_id: data.projectId }),
    });
  }

  async getAnalysis(id: string): Promise<Analysis> {
    console.log(`🔍 Fetching analysis: ${id}`);
    const result = await this.apiRequest<Analysis>(`/api/analyses/${id}/`);
    console.log(`✅ Analysis fetched:`, result);
    return result;
  }

  async getProjectAnalysisStatus(id: string): Promise<{
    status: string;
    progress: number;
    current_agent?: string;
    message?: string;
  }> {
    return this.apiRequest(`/api/analyses/${id}/status/`);
  }

  // GitHub API methods
  async getRepositories(): Promise<any[]> {
    return this.apiRequest<any[]>("/api/github/repos/");
  }

  async getRepository(repoId: number): Promise<any> {
    return this.apiRequest<any>(`/api/github/repos/${repoId}/`);
  }

  // Repository Analysis API methods
  async analyzeRepository(data: {
    repository_id: number;
    shallow_clone?: boolean;
    use_llm?: boolean;
    enabled_agents?: string[];
  }): Promise<{
    status: string;
    message: string;
    report: any;
  }> {
    return this.apiRequest("/api/repository-analysis/analyze", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAnalysisStatus(analysisId: string): Promise<{
    repository_id: number;
    status: string;
    message?: string;
  }> {
    return this.apiRequest(
      `/api/repository-analysis/analyze/${analysisId}/status`
    );
  }

  // User API methods
  async getCurrentUser(): Promise<BackendUser> {
    return this.apiRequest<BackendUser>("/api/auth/me/");
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`❌ Backend not accessible at ${API_BASE_URL}:`, error);
      throw new Error(`Backend server not accessible at ${API_BASE_URL}`);
    }
  }

  // Test API connection and authentication
  async testConnection(): Promise<void> {
    try {
      // 1. Test health endpoint
      const health = await this.healthCheck();

      // 2. Test authentication
      const session = await getSession();

      if (session?.backendToken) {
        // Try to get current user
        try {
          const user = await this.getCurrentUser();
        } catch (error) {
          console.error(`❌ User fetch failed:`, error);
        }
      }
    } catch (error) {
      console.error(`❌ API connection test failed:`, error);
      throw error;
    }
  }
}

// Export singleton instance
export const backendAPI = new BackendAPI();

// Export standalone functions for convenience
export const getProjects = () => backendAPI.getProjects();
export const getProjectById = (id: string) => backendAPI.getProject(id);
export const createProject = (data: ProjectCreate) =>
  backendAPI.createProject(data);
export const updateProject = (id: string, data: Partial<Project>) =>
  backendAPI.updateProject(id, data);
export const deleteProject = (id: string) => backendAPI.deleteProject(id);
export const startAnalysis = (projectId: string) =>
  backendAPI.startAnalysis({ projectId });
export const getAnalysis = (id: string) => backendAPI.getAnalysis(id);
export const getProjectAnalysisStatus = (id: string) =>
  backendAPI.getProjectAnalysisStatus(id);
export const getRepositories = () => backendAPI.getRepositories();
export const getRepository = (repoId: number) =>
  backendAPI.getRepository(repoId);
export const analyzeRepository = (
  data: Parameters<BackendAPI["analyzeRepository"]>[0]
) => backendAPI.analyzeRepository(data);
export const getAnalysisStatus = (analysisId: string) =>
  backendAPI.getAnalysisStatus(analysisId);
export const getCurrentUser = () => backendAPI.getCurrentUser();
export const healthCheck = () => backendAPI.healthCheck();
export const testConnection = () => backendAPI.testConnection();

// Export as default for easy importing
export default backendAPI;
