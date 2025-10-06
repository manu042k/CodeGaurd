"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Header from "@/components/Header";
import {
  FaGithub,
  FaStar,
  FaCodeBranch,
  FaLock,
  FaGlobe,
  FaCalendarAlt,
} from "react-icons/fa";

interface Repository {
  id: number;
  name: string;
  full_name: string;
  description: string;
  private: boolean;
  html_url: string;
  language: string;
  stargazers_count: number;
  forks_count: number;
  updated_at: string;
  owner: {
    login: string;
    avatar_url: string;
  };
}

export default function Repositories() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [repos, setRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return;
    if (!session) {
      router.push("/auth/signin");
      return;
    }

    fetchRepositories();
  }, [session, status, router]);

  const fetchRepositories = async () => {
    try {
      setLoading(true);
      // Import backend API dynamically to avoid SSR issues
      const { backendAPI } = await import("@/lib/backend-api");
      const data = await backendAPI.getRepositories();
      setRepos(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (repo: Repository) => {
    try {
      // Create project from repository
      const projectData = {
        name: repo.name,
        description:
          repo.description || `Analysis project for ${repo.full_name}`,
        repositoryId: repo.id,
        settings: {
          analysisConfig: {
            enabledAgents: [
              "CodeQuality",
              "Security",
              "Architecture",
              "Documentation",
            ],
            excludePatterns: ["node_modules", "*.test.*", "dist", "build"],
            includePaths: ["src", "lib", "pages", "components"],
          },
          notifications: {
            onComplete: true,
            onFailure: true,
          },
        },
      };

      // Create project using backend API
      const { backendAPI } = await import("@/lib/backend-api");
      const project = await backendAPI.createProject({
        name: projectData.name,
        description: projectData.description,
        github_repo_id: repo.id,
        github_url: repo.html_url,
        github_full_name: repo.full_name,
        settings: projectData.settings,
      });

      console.log("Created project:", project);

      // Redirect to projects page
      router.push("/projects?created=" + encodeURIComponent(repo.name));
    } catch (err) {
      console.error("Failed to create project:", err);
      alert("Failed to create project. Please try again.");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getLanguageColor = (language: string) => {
    const colors: { [key: string]: string } = {
      JavaScript: "bg-yellow-100 text-yellow-800",
      TypeScript: "bg-blue-100 text-blue-800",
      Python: "bg-green-100 text-green-800",
      Java: "bg-red-100 text-red-800",
      "C++": "bg-purple-100 text-purple-800",
      Go: "bg-cyan-100 text-cyan-800",
      Rust: "bg-orange-100 text-orange-800",
      PHP: "bg-indigo-100 text-indigo-800",
    };
    return colors[language] || "bg-gray-100 text-gray-800";
  };

  if (status === "loading" || loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  if (!session) {
    return null;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-red-800 font-semibold">
              Error loading repositories
            </h3>
            <p className="text-red-600 mt-2">{error}</p>
            <button
              onClick={fetchRepositories}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Your GitHub Repositories
          </h1>
          <p className="text-gray-600 mt-2">
            Found {repos.length} repositories in your GitHub account
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {repos.map((repo) => (
            <div
              key={repo.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow duration-200"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    {repo.private ? (
                      <FaLock className="h-4 w-4 text-yellow-600" />
                    ) : (
                      <FaGlobe className="h-4 w-4 text-green-600" />
                    )}
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                      {repo.private ? "Private" : "Public"}
                    </span>
                  </div>
                  <a
                    href={repo.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <FaGithub className="h-5 w-5" />
                  </a>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {repo.name}
                </h3>

                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {repo.description || "No description available"}
                </p>

                <div className="flex items-center justify-between mb-4">
                  {repo.language && (
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLanguageColor(
                        repo.language
                      )}`}
                    >
                      {repo.language}
                    </span>
                  )}

                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <FaStar className="h-3 w-3" />
                      <span>{repo.stargazers_count}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <FaCodeBranch className="h-3 w-3" />
                      <span>{repo.forks_count}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center text-xs text-gray-500">
                  <FaCalendarAlt className="h-3 w-3 mr-1" />
                  Updated {formatDate(repo.updated_at)}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleCreateProject(repo)}
                    className="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors duration-200 text-sm font-medium"
                  >
                    Create Project
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {repos.length === 0 && (
          <div className="text-center py-12">
            <FaGithub className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              No repositories found
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              It looks like you don't have any repositories yet.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
