import { getSession } from "next-auth/react";

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
  github_url?: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Analysis {
  id: string;
  project_id: string;
  status: string;
  results?: any;
  created_at: string;
  updated_at?: string;
}

// API Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// API Client with NextAuth integration
class BackendApi {
  private async getAuthHeaders(): Promise<Record<string, string>> {
    const session = await getSession();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    if (session?.backendToken) {
      headers.Authorization = `Bearer ${session.backendToken}`;
    }

    return headers;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = await this.getAuthHeaders();

    const config: RequestInit = {
      headers: {
        ...headers,
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      const errorText = await response.text();
      throw new ApiError(response.status, errorText || response.statusText);
    }

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    }

    return response.text() as unknown as T;
  }

  // Auth methods
  async getCurrentUser(): Promise<BackendUser> {
    return this.request<BackendUser>("/auth/me");
  }

  // Project methods
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>("/projects");
  }

  async getProject(id: string): Promise<Project> {
    return this.request<Project>(`/projects/${id}`);
  }

  async createProject(data: Partial<Project>): Promise<Project> {
    return this.request<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    return this.request<Project>(`/projects/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProject(id: string): Promise<void> {
    return this.request<void>(`/projects/${id}`, {
      method: "DELETE",
    });
  }

  // GitHub methods
  async getGitHubRepos(): Promise<any[]> {
    return this.request<any[]>("/github/repos");
  }

  async importGitHubRepo(repoUrl: string): Promise<Project> {
    return this.request<Project>("/github/import", {
      method: "POST",
      body: JSON.stringify({ repo_url: repoUrl }),
    });
  }

  // Analysis methods
  async getAnalyses(projectId?: string): Promise<Analysis[]> {
    const endpoint = projectId ? `/analyses?project_id=${projectId}` : "/analyses";
    return this.request<Analysis[]>(endpoint);
  }

  async getAnalysis(id: string): Promise<Analysis> {
    return this.request<Analysis>(`/analyses/${id}`);
  }

  async startAnalysis(projectId: string): Promise<Analysis> {
    return this.request<Analysis>("/analyses", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId }),
    });
  }
}

export const backendApi = new BackendApi();
