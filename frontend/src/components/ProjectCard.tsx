"use client";

import Link from "next/link";
import { Project } from "@/types/project";
import {
  FaGithub,
  FaStar,
  FaCodeBranch,
  FaLock,
  FaGlobe,
  FaCalendarAlt,
  FaPlay,
  FaEye,
  FaCog,
  FaTrash,
} from "react-icons/fa";
import { useState } from "react";

interface ProjectCardProps {
  project: Project;
  onAnalyze?: (projectId: string) => void;
  onDelete?: (projectId: string) => void;
}

export default function ProjectCard({
  project,
  onAnalyze,
  onDelete,
}: ProjectCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const getStatusBadge = (status: Project["status"]) => {
    const badges = {
      never_analyzed: "bg-gray-100 text-gray-800",
      analyzing: "bg-blue-100 text-blue-800 animate-pulse",
      completed: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
    };

    const labels = {
      never_analyzed: "Not Analyzed",
      analyzing: "Analyzing...",
      completed: "Completed",
      failed: "Failed",
    };

    return (
      <span
        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badges[status]}`}
      >
        {labels[status]}
      </span>
    );
  };

  const getLanguageColor = (language: string | null) => {
    if (!language) return "bg-gray-100 text-gray-800";

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const handleDelete = async () => {
    if (!onDelete) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete "${project.name}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setIsDeleting(true);
    try {
      await onDelete(project.id);
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
    setIsDeleting(false);
  };

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow duration-200 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            {project.repository.private ? (
              <FaLock className="h-4 w-4 text-yellow-600" />
            ) : (
              <FaGlobe className="h-4 w-4 text-green-600" />
            )}
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
              {project.repository.private ? "Private" : "Public"}
            </span>
            {getStatusBadge(project.status)}
          </div>

          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {project.name}
          </h3>

          <Link
            href={project.repository.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-600 hover:text-gray-900 flex items-center space-x-1"
          >
            <FaGithub className="h-4 w-4" />
            <span>{project.repository.full_name}</span>
          </Link>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="p-2 text-gray-400 hover:text-red-600 transition-colors duration-200"
            title="Delete project"
          >
            <FaTrash className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Description */}
      {project.description && (
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {project.description}
        </p>
      )}

      {/* Repository Stats */}
      <div className="flex items-center justify-between mb-4">
        {project.repository.language && (
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLanguageColor(
              project.repository.language
            )}`}
          >
            {project.repository.language}
          </span>
        )}

        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <div className="flex items-center space-x-1">
            <FaStar className="h-3 w-3" />
            <span>{project.repository.stargazers_count}</span>
          </div>
          <div className="flex items-center space-x-1">
            <FaCodeBranch className="h-3 w-3" />
            <span>{project.repository.forks_count}</span>
          </div>
        </div>
      </div>

      {/* Analysis Info */}
      {project.latestAnalysis && (
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">
                Latest Analysis
              </p>
              <p className="text-xs text-gray-500">
                {formatDate(
                  project.latestAnalysis.completedAt ||
                    project.latestAnalysis.startedAt
                )}
              </p>
            </div>
            {project.latestAnalysis.overallScore && (
              <div className="text-right">
                <p className="text-lg font-bold text-gray-900">
                  {project.latestAnalysis.overallScore}/100
                </p>
                <p className="text-xs text-gray-500">Score</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="flex items-center text-xs text-gray-500 mb-4">
        <FaCalendarAlt className="h-3 w-3 mr-1" />
        Repository updated {formatDate(project.repository.updated_at)}
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        <button
          onClick={() => onAnalyze?.(project.id)}
          disabled={project.status === "analyzing"}
          className="flex-1 inline-flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors duration-200 text-sm font-medium"
        >
          <FaPlay className="h-3 w-3" />
          <span>
            {project.status === "analyzing" ? "Analyzing..." : "Run Analysis"}
          </span>
        </button>

        {project.latestAnalysis && (
          <Link
            href={`/reports/${project.latestAnalysis.id}`}
            className="inline-flex items-center justify-center px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-sm font-medium"
          >
            <FaEye className="h-3 w-3 mr-2" />
            View Report
          </Link>
        )}

        <Link
          href={`/projects/${project.id}`}
          className="inline-flex items-center justify-center px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors duration-200 text-sm font-medium"
        >
          <FaCog className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
