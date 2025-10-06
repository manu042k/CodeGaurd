"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { backendApi, Project, Analysis } from "@/lib/backend-api";
import {
  FaShieldAlt,
  FaExclamationTriangle,
  FaCheckCircle,
  FaCode,
  FaPlus,
  FaGithub,
} from "react-icons/fa";

interface DashboardStats {
  totalProjects: number;
  totalAnalyses: number;
  pendingAnalyses: number;
  completedAnalyses: number;
}

export default function Dashboard() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    totalAnalyses: 0,
    pendingAnalyses: 0,
    completedAnalyses: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "loading") return; // Still loading
    if (!session) router.push("/auth/signin");
  }, [session, status, router]);

  useEffect(() => {
    if (session?.backendToken) {
      loadDashboardData();
    }
  }, [session]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load projects and analyses in parallel
      const [projectsData, analysesData] = await Promise.all([
        backendApi.getProjects().catch(() => []),
        backendApi.getAnalyses().catch(() => []),
      ]);

      setProjects(projectsData);
      setAnalyses(analysesData);

      // Calculate stats
      const pendingAnalyses = analysesData.filter(
        (a) => a.status === "pending" || a.status === "running"
      ).length;
      const completedAnalyses = analysesData.filter(
        (a) => a.status === "completed"
      ).length;

      setStats({
        totalProjects: projectsData.length,
        totalAnalyses: analysesData.length,
        pendingAnalyses,
        completedAnalyses,
      });
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setError(
        "Failed to load dashboard data. The backend API might not be running."
      );
    } finally {
      setLoading(false);
    }
  };

  if (status === "loading" || loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
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
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {session.user?.name || session.username}!
          </h1>
          <p className="text-gray-600 mt-2">
            Here's an overview of your code security status.
          </p>
          {session.backendToken ? (
            <p className="text-sm text-green-600 mt-1">
              ✅ Connected to backend API
            </p>
          ) : (
            <p className="text-sm text-yellow-600 mt-1">
              ⚠️ Backend API connection pending...
            </p>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex">
              <FaExclamationTriangle className="h-5 w-5 text-red-400 mt-0.5" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Backend Connection Issue
                </h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
                <p className="text-sm text-red-600 mt-2">
                  Make sure the backend server is running on{" "}
                  <code>http://localhost:8000</code>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaCode className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Projects</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.totalProjects}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaShieldAlt className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">
                  Total Analyses
                </p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.totalAnalyses}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaCheckCircle className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Completed</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.completedAnalyses}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <FaExclamationTriangle className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Pending</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.pendingAnalyses}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Quick Actions
            </h2>
            <div className="space-y-3">
              <button
                onClick={() => router.push("/projects/new")}
                className="w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
              >
                <FaPlus className="mr-2 h-4 w-4" />
                Create New Project
              </button>
              <button
                onClick={() => router.push("/repositories")}
                className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                <FaGithub className="mr-2 h-4 w-4" />
                Import from GitHub
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Recent Projects
            </h2>
            {projects.length > 0 ? (
              <div className="space-y-3">
                {projects.slice(0, 3).map((project) => (
                  <div
                    key={project.id}
                    className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => router.push(`/projects/${project.id}`)}
                  >
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">
                        {project.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        {project.description || "No description"}
                      </p>
                    </div>
                    <span
                      className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        project.status === "active"
                          ? "bg-green-100 text-green-800"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {project.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">
                No projects yet. Create your first project to get started!
              </p>
            )}
          </div>
        </div>

        {/* Recent Analyses */}
        {analyses.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Recent Security Analyses
            </h2>
            <div className="space-y-3">
              {analyses.slice(0, 5).map((analysis) => (
                <div
                  key={analysis.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">
                      Analysis #{analysis.id.slice(0, 8)}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {new Date(analysis.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      analysis.status === "completed"
                        ? "bg-green-100 text-green-800"
                        : analysis.status === "running"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-yellow-100 text-yellow-800"
                    }`}
                  >
                    {analysis.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
