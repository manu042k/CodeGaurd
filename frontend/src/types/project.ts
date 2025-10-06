// Project-related types
export interface Repository {
  id: number;
  name: string;
  full_name: string;
  description: string | null;
  private: boolean;
  html_url: string;
  clone_url: string;
  language: string | null;
  stargazers_count: number;
  forks_count: number;
  updated_at: string;
  created_at: string;
  owner: {
    login: string;
    avatar_url: string;
  };
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  repository: Repository;
  userId: string;
  createdAt: string;
  updatedAt: string;
  latestAnalysis?: Analysis;
  analysisCount: number;
  status: ProjectStatus;
  settings: ProjectSettings;
}

export type ProjectStatus =
  | "never_analyzed"
  | "analyzing"
  | "completed"
  | "failed";

export interface ProjectSettings {
  analysisConfig: {
    enabledAgents: AgentType[];
    excludePatterns: string[];
    includePaths: string[];
  };
  notifications: {
    onComplete: boolean;
    onFailure: boolean;
  };
}

// Analysis-related types
export interface Analysis {
  id: string;
  projectId: string;
  status: AnalysisStatus;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  agents: AgentResult[];
  overallScore?: number;
  summary?: string;
  error?: string;
}

export type AnalysisStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface AgentResult {
  name: AgentType;
  status: AnalysisStatus;
  score?: number;
  issues: Issue[];
  summary: string;
  startedAt: string;
  completedAt?: string;
  duration?: number;
  error?: string;
}

export type AgentType =
  | "CodeQuality"
  | "Security"
  | "Architecture"
  | "Documentation";

export interface Issue {
  id: string;
  type: "error" | "warning" | "info" | "suggestion";
  severity: "critical" | "high" | "medium" | "low";
  title: string;
  description: string;
  file?: string;
  line?: number;
  column?: number;
  rule?: string;
  agent: AgentType;
}

// API Response types
export interface CreateProjectRequest {
  name: string;
  description?: string;
  repositoryId: number;
  settings?: Partial<ProjectSettings>;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  settings?: Partial<ProjectSettings>;
}

export interface StartAnalysisRequest {
  projectId: string;
  agentTypes?: AgentType[];
}
