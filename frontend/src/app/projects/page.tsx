"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Header from "@/components/Header";
import ProjectCard from "@/components/ProjectCard";
import { backendAPI, Project } from "@/lib/backend-api";
import { FaPlus, FaGithub, FaFilter, FaSearch } from "react-icons/fa";
import Link from "next/link";

type FilterType =
  | "all"
  | "never_analyzed"
  | "analyzing"
  | "completed"
  | "failed";

export default function ProjectsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterType>("all");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (status === "loading") return;
    if (!session) {
      router.push("/auth/signin");
      return;
    }

    loadProjects();
  }, [session, status, router]);

  const loadProjects = async () => {
    try {
      console.log("🔄 Loading projects...");
      setLoading(true);
      const data = await backendAPI.getProjects();
      console.log("✅ Projects loaded:", data);
      setProjects(data);
    } catch (err) {
      console.error("❌ Failed to load projects:", err);
      setError(err instanceof Error ? err.message : "Failed to load projects");
      setProjects([]); // Empty array when API fails
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (projectId: string) => {
    try {
      // Update project status to analyzing
      setProjects((prev) =>
        prev.map((p) =>
          p.id === projectId ? { ...p, status: "analyzing" as const } : p
        )
      );

      // Start analysis
      const analysis = await backendAPI.startAnalysis({ projectId });
      console.log("Started analysis:", analysis.id);

      // Navigate to analysis page
      router.push(`/analysis/${analysis.id}`);
    } catch (err) {
      console.error("Failed to start analysis:", err);
      // Revert status
      setProjects((prev) =>
        prev.map((p) =>
          p.id === projectId ? { ...p, status: "never_analyzed" as const } : p
        )
      );
    }
  };

  const handleDelete = async (projectId: string) => {
    try {
      await backendAPI.deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err) {
      console.error("Failed to delete project:", err);
    }
  };

  const filteredProjects = projects.filter((project) => {
    const matchesFilter = filter === "all" || project.status === filter;
    const matchesSearch =
      searchQuery === "" ||
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.github_full_name
        .toLowerCase()
        .includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const getFilterCounts = () => {
    return {
      all: projects.length,
      never_analyzed: projects.filter((p) => p.status === "never_analyzed")
        .length,
      analyzing: projects.filter((p) => p.status === "analyzing").length,
      completed: projects.filter((p) => p.status === "completed").length,
      failed: projects.filter((p) => p.status === "failed").length,
    };
  };

  const filterCounts = getFilterCounts();

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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Your Projects</h1>
            <p className="text-gray-600 mt-2">
              Manage and analyze your code repositories
            </p>
          </div>

          <div className="flex space-x-3">
            <Link
              href="/repositories"
              className="inline-flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200"
            >
              <FaGithub className="h-4 w-4" />
              <span>Import from GitHub</span>
            </Link>

            <button className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors duration-200">
              <FaPlus className="h-4 w-4" />
              <span>New Project</span>
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 mb-6">
          {/* Search */}
          <div className="flex-1 relative">
            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
          </div>

          {/* Filter Tabs */}
          <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
            {[
              { key: "all", label: "All", count: filterCounts.all },
              {
                key: "never_analyzed",
                label: "Not Analyzed",
                count: filterCounts.never_analyzed,
              },
              {
                key: "analyzing",
                label: "Analyzing",
                count: filterCounts.analyzing,
              },
              {
                key: "completed",
                label: "Completed",
                count: filterCounts.completed,
              },
              { key: "failed", label: "Failed", count: filterCounts.failed },
            ].map(({ key, label, count }) => (
              <button
                key={key}
                onClick={() => setFilter(key as FilterType)}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-200 ${
                  filter === key
                    ? "bg-white text-gray-900 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                {label} {count > 0 && `(${count})`}
              </button>
            ))}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
            <button
              onClick={loadProjects}
              className="mt-2 text-red-600 hover:text-red-800 font-medium"
            >
              Try again
            </button>
          </div>
        )}

        {/* Projects Grid */}
        {filteredProjects.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onAnalyze={handleAnalyze}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : (
          /* Empty State */
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <FaGithub className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {projects.length === 0
                  ? "No projects yet"
                  : "No projects match your filters"}
              </h3>
              <p className="text-gray-500 mb-6">
                {projects.length === 0
                  ? "Get started by importing repositories from GitHub or creating a new project."
                  : "Try adjusting your search or filter criteria."}
              </p>
              {projects.length === 0 && (
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Link
                    href="/repositories"
                    className="inline-flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors duration-200"
                  >
                    <FaGithub className="h-4 w-4" />
                    <span>Import from GitHub</span>
                  </Link>
                  <button className="inline-flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                    <FaPlus className="h-4 w-4" />
                    <span>Create New Project</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
