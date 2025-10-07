"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  getProjectById,
  Project,
  startAnalysis,
  Analysis,
} from "@/lib/backend-api";
import { useNotifications } from "@/hooks/useNotifications";
import { Notification } from "@/components/ui/Notification";
import {
  FaGithub,
  FaArrowLeft,
  FaPlay,
  FaEye,
  FaCog,
  FaTrash,
  FaCalendarAlt,
  FaStar,
  FaCodeBranch,
} from "react-icons/fa";
import Link from "next/link";

export default function ProjectDetailPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const { notifications, showSuccess, showError, removeNotification } =
    useNotifications();

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const loadProject = async () => {
    try {
      setIsLoading(true);
      const data = await getProjectById(projectId);
      setProject(data);
    } catch (error) {
      showError("Failed to load project");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      const analysis = await startAnalysis(projectId);
      showSuccess("Analysis started successfully!");

      // Refresh project to show updated status
      setTimeout(() => {
        loadProject();
      }, 1000);

      // Navigate to the report page after a short delay
      setTimeout(() => {
        router.push(`/reports/${analysis.id}`);
      }, 2000);
    } catch (error) {
      showError("Failed to start analysis");
      console.error(error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getStatusBadge = (status: Project["status"]) => {
    const badges = {
      never_analyzed: "bg-gray-100 text-gray-800",
      analyzing: "bg-blue-100 text-blue-800 animate-pulse",
      completed: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
    };

    const labels = {
      never_analyzed: "Never Analyzed",
      analyzing: "Analyzing...",
      completed: "Completed",
      failed: "Failed",
    };

    return (
      <span
        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${badges[status]}`}
      >
        {labels[status]}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
              <div className="space-y-4">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Project Not Found
            </h2>
            <p className="text-gray-600 mb-6">
              The project you're looking for doesn't exist or you don't have
              access to it.
            </p>
            <Link
              href="/projects"
              className="inline-flex items-center px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <FaArrowLeft className="mr-2" />
              Back to Projects
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/projects"
            className="inline-flex items-center text-indigo-600 hover:text-indigo-800 mb-4 transition-colors"
          >
            <FaArrowLeft className="mr-2" />
            Back to Projects
          </Link>
          <h1 className="text-4xl font-bold text-gray-900">{project.name}</h1>
          {project.description && (
            <p className="text-gray-600 mt-2">{project.description}</p>
          )}
        </div>

        {/* Project Info Card */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden mb-6">
          <div className="p-6">
            <div className="flex items-start justify-between mb-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-2xl font-semibold text-gray-900">
                    Project Details
                  </h2>
                  {getStatusBadge(project.status)}
                </div>

                <div className="space-y-3 text-sm">
                  <div className="flex items-center text-gray-600">
                    <FaGithub className="mr-2 h-4 w-4" />
                    <a
                      href={project.github_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-800 hover:underline"
                    >
                      {project.github_full_name}
                    </a>
                  </div>

                  <div className="flex items-center text-gray-600">
                    <FaCalendarAlt className="mr-2 h-4 w-4" />
                    Created on{" "}
                    {new Date(project.created_at).toLocaleDateString()}
                  </div>

                  <div className="flex items-center text-gray-600">
                    <FaStar className="mr-2 h-4 w-4" />
                    {project.analysis_count}{" "}
                    {project.analysis_count === 1 ? "analysis" : "analyses"} run
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <button
                  onClick={handleRunAnalysis}
                  disabled={isAnalyzing || project.status === "analyzing"}
                  className={`inline-flex items-center px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                    isAnalyzing || project.status === "analyzing"
                      ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                      : "bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-lg"
                  }`}
                >
                  <FaPlay className="mr-2 h-4 w-4" />
                  {isAnalyzing || project.status === "analyzing"
                    ? "Analyzing..."
                    : "Run Analysis"}
                </button>

                {project.latest_analysis && (
                  <Link
                    href={`/reports/${project.latest_analysis.id}`}
                    className="inline-flex items-center px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <FaEye className="mr-2 h-4 w-4" />
                    View Latest Report
                  </Link>
                )}
              </div>
            </div>

            {/* Latest Analysis Info */}
            {project.latest_analysis && (
              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  Latest Analysis
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Status</div>
                    <div className="font-semibold text-gray-900 capitalize">
                      {project.status}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Score</div>
                    <div className="font-semibold text-gray-900">
                      {project.latest_analysis.overallScore
                        ? `${(
                            project.latest_analysis.overallScore * 100
                          ).toFixed(1)}%`
                        : "N/A"}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Started</div>
                    <div className="font-semibold text-gray-900">
                      {new Date(
                        project.latest_analysis.startedAt
                      ).toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <div className="text-sm text-gray-600 mb-1">Completed</div>
                    <div className="font-semibold text-gray-900">
                      {project.latest_analysis.completedAt
                        ? new Date(
                            project.latest_analysis.completedAt
                          ).toLocaleString()
                        : "In Progress"}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Settings Card */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="p-6">
            <div className="flex items-center mb-6">
              <FaCog className="mr-2 h-5 w-5 text-gray-600" />
              <h3 className="text-xl font-semibold text-gray-900">
                Analysis Configuration
              </h3>
            </div>

            {project.settings && (
              <div className="space-y-6">
                {/* Enabled Agents */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Enabled Agents
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {project.settings.analysisConfig?.enabledAgents?.map(
                      (agent: string) => (
                        <span
                          key={agent}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                        >
                          {agent}
                        </span>
                      )
                    )}
                  </div>
                </div>

                {/* Exclude Patterns */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Exclude Patterns
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {project.settings.analysisConfig?.excludePatterns?.map(
                      (pattern: string, index: number) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 font-mono"
                        >
                          {pattern}
                        </span>
                      )
                    )}
                  </div>
                </div>

                {/* Include Paths */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Include Paths
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {project.settings.analysisConfig?.includePaths?.map(
                      (path: string, index: number) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 font-mono"
                        >
                          {path}
                        </span>
                      )
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Notifications */}
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          message={notification.message}
          type={notification.type}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
}
