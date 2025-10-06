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

export interface Analysis {
  id: string;
  project_id: string;
  status: string;
  results?: any;
  created_at: string;
  updated_at?: string;
}

// Backend API client with NextAuth integration
export class BackendAPI {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const session = await getSession();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    console.log(`🔐 Session:`, session ? "Found" : "Not found");
    console.log(
      `🎫 Backend Token:`,
      session?.backendToken ? "Found" : "Not found"
    );

    if (session?.backendToken) {
      headers.Authorization = `Bearer ${session.backendToken}`;
    } else if (session?.accessToken) {
      // Fallback to GitHub access token if backend token not available
      headers.Authorization = `Bearer ${session.accessToken}`;
      console.log(`🔄 Using GitHub access token as fallback`);
    }

    return headers;
  }

  private async apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = await this.getAuthHeaders();

    console.log(`🔄 API Request: ${options.method || "GET"} ${url}`);
    console.log(`🔑 Headers:`, headers);

    const response = await fetch(url, {
      headers: {
        ...headers,
        ...(options.headers as Record<string, string>),
      },
      ...options,
    });

    console.log(`📡 API Response: ${response.status} ${response.statusText}`);

    if (!response.ok) {
      // Handle 401 Unauthorized - session expired
      if (response.status === 401) {
        console.log("🔐 Session expired (401), triggering logout...");
        // Set flag for logout notification
        if (typeof window !== 'undefined') {
          sessionStorage.setItem("autoLoggedOut", "true");
        }
        // Import signOut dynamically to avoid circular dependencies
        const { signOut } = await import("next-auth/react");
        await signOut({ 
          redirect: false,
          callbackUrl: "/auth/signin"
        });
        // Redirect to signin page
        if (typeof window !== 'undefined') {
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
    console.log(`✅ API Success:`, data);
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
    return this.apiRequest<void>(`/api/projects/${id}/`, {
      method: "DELETE",
    });
  }

  // Analysis API methods
  async startAnalysis(data: { projectId: string }): Promise<Analysis> {
    return this.apiRequest<Analysis>("/api/analyses/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getAnalysis(id: string): Promise<Analysis> {
    return this.apiRequest<Analysis>(`/api/analyses/${id}/`);
  }

  async getAnalysisStatus(id: string): Promise<{
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
    console.log(`🧪 Testing API connection to ${API_BASE_URL}`);

    try {
      // 1. Test health endpoint
      const health = await this.healthCheck();
      console.log(`✅ Health check passed:`, health);

      // 2. Test authentication
      const session = await getSession();
      console.log(`🔐 Session status:`, session ? "Found" : "Missing");

      if (session?.backendToken) {
        console.log(`🎫 Backend token: Found`);
        // Try to get current user
        try {
          const user = await this.getCurrentUser();
          console.log(`👤 Current user:`, user.username);
        } catch (error) {
          console.error(`❌ User fetch failed:`, error);
        }
      } else {
        console.log(`⚠️ No backend token found in session`);
      }
    } catch (error) {
      console.error(`❌ API connection test failed:`, error);
      throw error;
    }
  }
}

// Export singleton instance
export const backendAPI = new BackendAPI();

// Export as default for easy importing
export default backendAPI;
