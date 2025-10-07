"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { getAnalysis, Analysis } from "@/lib/backend-api";
import { useNotifications } from "@/hooks/useNotifications";
import { Notification } from "@/components/ui/Notification";
import {
  FaArrowLeft,
  FaCheckCircle,
  FaExclamationCircle,
  FaInfoCircle,
  FaTimesCircle,
  FaClock,
  FaCode,
  FaShieldAlt,
  FaSitemap,
  FaBook,
} from "react-icons/fa";
import Link from "next/link";

export default function ReportPage() {
  const router = useRouter();
  const params = useParams();
  const analysisId = params.id as string;

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { notifications, showError, removeNotification } = useNotifications();

  useEffect(() => {
    loadAnalysis();
  }, [analysisId]);

  const loadAnalysis = async () => {
    try {
      setIsLoading(true);
      const data = await getAnalysis(analysisId);

      // Log the full API response to console
      console.log("=== ANALYSIS REPORT API RESPONSE ===");
      console.log("Analysis ID:", analysisId);
      console.log("Full Response:", JSON.stringify(data, null, 2));
      console.log("Status:", data.status);
      console.log("Overall Score:", data.overall_score);
      console.log("Agent Results:", data.agent_results?.length || 0);
      console.log(
        "Total Issues:",
        data.agent_results?.reduce(
          (sum, agent) => sum + (agent.issues?.length || 0),
          0
        ) || 0
      );
      console.log("====================================");

      setAnalysis(data);
    } catch (error) {
      showError("Failed to load analysis report");
      console.error("=== ERROR LOADING ANALYSIS ===");
      console.error(error);
      console.error("==============================");
    } finally {
      setIsLoading(false);
    }
  };

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case "CodeQuality":
        return <FaCode className="h-5 w-5" />;
      case "Security":
        return <FaShieldAlt className="h-5 w-5" />;
      case "Architecture":
        return <FaSitemap className="h-5 w-5" />;
      case "Documentation":
        return <FaBook className="h-5 w-5" />;
      default:
        return <FaCode className="h-5 w-5" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <FaCheckCircle className="text-green-500" />;
      case "failed":
        return <FaTimesCircle className="text-red-500" />;
      case "running":
        return <FaClock className="text-blue-500 animate-spin" />;
      default:
        return <FaClock className="text-gray-500" />;
    }
  };

  const getIssueIcon = (type: string) => {
    switch (type) {
      case "error":
        return <FaTimesCircle className="text-red-500" />;
      case "warning":
        return <FaExclamationCircle className="text-yellow-500" />;
      case "info":
        return <FaInfoCircle className="text-blue-500" />;
      case "suggestion":
        return <FaCheckCircle className="text-green-500" />;
      default:
        return <FaInfoCircle className="text-gray-500" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const badges = {
      critical: "bg-red-100 text-red-800 border-red-300",
      high: "bg-orange-100 text-orange-800 border-orange-300",
      medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
      low: "bg-blue-100 text-blue-800 border-blue-300",
    };
    return badges[severity as keyof typeof badges] || badges.medium;
  };

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-500";
    if (score >= 0.8) return "text-green-600";
    if (score >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
              <div className="space-y-4">
                <div className="h-32 bg-gray-200 rounded"></div>
                <div className="h-32 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Report Not Found
            </h2>
            <p className="text-gray-600 mb-6">
              The analysis report you're looking for doesn't exist or you don't
              have access to it.
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
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/projects"
            className="inline-flex items-center text-indigo-600 hover:text-indigo-800 mb-4 transition-colors"
          >
            <FaArrowLeft className="mr-2" />
            Back to Projects
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">
                Analysis Report
              </h1>
              <p className="text-gray-600 mt-2">
                Started: {new Date(analysis.started_at).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {getStatusIcon(analysis.status)}
              <span className="text-lg font-medium capitalize">
                {analysis.status}
              </span>
            </div>
          </div>
        </div>

        {/* Overall Score Card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2">Overall Score</div>
              <div
                className={`text-4xl font-bold ${getScoreColor(
                  analysis.overall_score
                )}`}
              >
                {analysis.overall_score
                  ? `${(analysis.overall_score * 100).toFixed(1)}%`
                  : "N/A"}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2">Duration</div>
              <div className="text-4xl font-bold text-gray-900">
                {analysis.duration ? `${analysis.duration}s` : "N/A"}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2">Agents Run</div>
              <div className="text-4xl font-bold text-gray-900">
                {analysis.agent_results.length}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-600 mb-2">Total Issues</div>
              <div className="text-4xl font-bold text-gray-900">
                {analysis.agent_results.reduce(
                  (sum, agent) => sum + agent.issues.length,
                  0
                )}
              </div>
            </div>
          </div>

          {analysis.summary && (
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-gray-700">{analysis.summary}</p>
            </div>
          )}

          {analysis.error && (
            <div className="mt-6 p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center text-red-800 mb-2">
                <FaTimesCircle className="mr-2" />
                <span className="font-semibold">Error</span>
              </div>
              <p className="text-red-700">{analysis.error}</p>
            </div>
          )}
        </div>

        {/* Agent Results */}
        <div className="space-y-6">
          {analysis.agent_results.map((agent) => (
            <div
              key={agent.id}
              className="bg-white rounded-xl shadow-lg overflow-hidden"
            >
              <div className="p-6 bg-gradient-to-r from-indigo-50 to-blue-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getAgentIcon(agent.agent_name)}
                    <h2 className="text-2xl font-semibold text-gray-900">
                      {agent.agent_name}
                    </h2>
                    {getStatusIcon(agent.status)}
                  </div>
                  <div className="text-right">
                    {agent.score !== null && agent.score !== undefined && (
                      <div
                        className={`text-3xl font-bold ${getScoreColor(
                          agent.score
                        )}`}
                      >
                        {(agent.score * 100).toFixed(1)}%
                      </div>
                    )}
                    {agent.duration && (
                      <div className="text-sm text-gray-600">
                        {agent.duration}s
                      </div>
                    )}
                  </div>
                </div>

                {agent.summary && (
                  <p className="mt-4 text-gray-700">{agent.summary}</p>
                )}

                {agent.error && (
                  <div className="mt-4 p-3 bg-red-50 rounded-lg border border-red-200">
                    <p className="text-red-700 text-sm">{agent.error}</p>
                  </div>
                )}
              </div>

              {/* Issues */}
              {agent.issues.length > 0 && (
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Issues Found ({agent.issues.length})
                  </h3>
                  <div className="space-y-4">
                    {agent.issues.map((issue) => (
                      <div
                        key={issue.id}
                        className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3">
                          <div className="mt-1">{getIssueIcon(issue.type)}</div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h4 className="font-semibold text-gray-900">
                                {issue.title}
                              </h4>
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium border ${getSeverityBadge(
                                  issue.severity
                                )}`}
                              >
                                {issue.severity}
                              </span>
                            </div>
                            <p className="text-gray-700 mb-2">
                              {issue.description}
                            </p>
                            {(issue.file_path || issue.rule) && (
                              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                                {issue.file_path && (
                                  <span className="font-mono">
                                    📄 {issue.file_path}
                                    {issue.line_number &&
                                      `:${issue.line_number}`}
                                    {issue.column_number &&
                                      `:${issue.column_number}`}
                                  </span>
                                )}
                                {issue.rule && (
                                  <span className="font-mono">
                                    📋 Rule: {issue.rule}
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {agent.issues.length === 0 && agent.status === "completed" && (
                <div className="p-6 text-center text-gray-500">
                  <FaCheckCircle className="inline-block h-8 w-8 text-green-500 mb-2" />
                  <p>No issues found</p>
                </div>
              )}
            </div>
          ))}
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
