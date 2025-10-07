"use client";

import { useEffect } from "react";
import {
  FaTimes,
  FaCheckCircle,
  FaExclamationTriangle,
  FaInfoCircle,
  FaTimesCircle,
  FaClock,
  FaCodeBranch,
  FaChartLine,
} from "react-icons/fa";

interface AnalysisReport {
  status: string;
  repository: {
    id: number;
    name: string;
    full_name: string;
    url: string;
    language: string;
  };
  clone: {
    success: boolean;
    duration: number;
    size_mb: number;
    commit_count?: number;
    shallow: boolean;
  };
  analysis: {
    files_analyzed: number;
    total_issues: number;
    summary: {
      overall_score: number;
      grade: string;
      by_severity: {
        critical?: number;
        high?: number;
        medium?: number;
        low?: number;
        info?: number;
      };
      by_category: Record<string, number>;
      by_agent: Record<string, number>;
    };
    issues: Array<{
      title: string;
      description: string;
      severity: string;
      category: string;
      file_path: string;
      line_number?: number;
      agent: string;
    }>;
    recommendations: Array<{
      title: string;
      description: string;
      priority?: string;
    }>;
  };
  timing: {
    total_duration: number;
    clone_duration: number;
    analysis_duration: number;
  };
}

interface AnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: AnalysisReport | null;
  loading: boolean;
  error: string | null;
}

export default function AnalysisModal({
  isOpen,
  onClose,
  report,
  loading,
  error,
}: AnalysisModalProps) {
  const getGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      "A+": "text-green-600",
      A: "text-green-600",
      "B+": "text-blue-600",
      B: "text-blue-600",
      "C+": "text-yellow-600",
      C: "text-yellow-600",
      "D+": "text-orange-600",
      D: "text-orange-600",
      F: "text-red-600",
    };
    return colors[grade] || "text-gray-600";
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return <FaTimesCircle className="text-red-600" />;
      case "high":
        return <FaExclamationTriangle className="text-orange-600" />;
      case "medium":
        return <FaExclamationTriangle className="text-yellow-600" />;
      case "low":
        return <FaInfoCircle className="text-blue-600" />;
      default:
        return <FaInfoCircle className="text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      critical: "bg-red-100 text-red-800 border-red-300",
      high: "bg-orange-100 text-orange-800 border-orange-300",
      medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
      low: "bg-blue-100 text-blue-800 border-blue-300",
      info: "bg-gray-100 text-gray-800 border-gray-300",
    };
    return (
      colors[severity.toLowerCase()] ||
      "bg-gray-100 text-gray-800 border-gray-300"
    );
  };

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-6xl bg-white rounded-2xl shadow-xl p-6 max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-2xl font-bold leading-6 text-gray-900">
              Repository Analysis
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <FaTimes className="h-6 w-6" />
            </button>
          </div>

          {loading && (
            <div className="flex flex-col items-center justify-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mb-4"></div>
              <p className="text-lg text-gray-600">Analyzing repository...</p>
              <p className="text-sm text-gray-500 mt-2">
                This may take a few moments
              </p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <FaTimesCircle className="h-5 w-5 text-red-600 mt-0.5 mr-3" />
                <div>
                  <h4 className="text-red-800 font-semibold">
                    Analysis Failed
                  </h4>
                  <p className="text-red-600 text-sm mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {report &&
            report.analysis &&
            report.analysis.summary &&
            !loading &&
            !error && (
              <div className="space-y-6">
                {/* Repository Info */}
                <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900">
                        {report.repository?.name || "Unknown Repository"}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {report.repository?.full_name || ""}
                      </p>
                    </div>
                    <div className="text-right">
                      <div
                        className={`text-4xl font-bold ${getGradeColor(
                          report.analysis.summary.grade
                        )}`}
                      >
                        {report.analysis.summary.grade}
                      </div>
                      <div className="text-sm text-gray-600">
                        Score: {report.analysis.summary.overall_score}/100
                      </div>
                    </div>
                  </div>
                </div>

                {/* Statistics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Files Analyzed</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {report.analysis.files_analyzed || 0}
                        </p>
                      </div>
                      <FaCodeBranch className="h-8 w-8 text-indigo-600" />
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Total Issues</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {report.analysis.total_issues || 0}
                        </p>
                      </div>
                      <FaExclamationTriangle className="h-8 w-8 text-yellow-600" />
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Repository Size</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {report.clone?.size_mb?.toFixed(2) || "0.00"} MB
                        </p>
                      </div>
                      <FaChartLine className="h-8 w-8 text-green-600" />
                    </div>
                  </div>

                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Analysis Time</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {report.timing?.total_duration?.toFixed(2) || "0.00"}s
                        </p>
                      </div>
                      <FaClock className="h-8 w-8 text-blue-600" />
                    </div>
                  </div>
                </div>

                {/* Issues by Severity */}
                {report.analysis.total_issues > 0 &&
                  report.analysis.summary?.by_severity && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">
                        Issues by Severity
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        {Object.entries(
                          report.analysis.summary.by_severity
                        ).map(
                          ([severity, count]) =>
                            count > 0 && (
                              <div
                                key={severity}
                                className={`border rounded-lg p-3 ${getSeverityColor(
                                  severity
                                )}`}
                              >
                                <div className="flex items-center justify-between">
                                  {getSeverityIcon(severity)}
                                  <span className="text-2xl font-bold">
                                    {count}
                                  </span>
                                </div>
                                <p className="text-xs font-medium mt-1 capitalize">
                                  {severity}
                                </p>
                              </div>
                            )
                        )}
                      </div>
                    </div>
                  )}

                {/* Top Issues */}
                {report.analysis.issues &&
                  report.analysis.issues.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">
                        Top Issues ({report.analysis.issues.length})
                      </h4>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {report.analysis.issues
                          .slice(0, 10)
                          .map((issue, index) => (
                            <div
                              key={index}
                              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                            >
                              <div className="flex items-start space-x-3">
                                <div className="flex-shrink-0 mt-1">
                                  {getSeverityIcon(issue.severity)}
                                </div>
                                <div className="flex-grow">
                                  <div className="flex items-center justify-between">
                                    <h5 className="font-semibold text-gray-900">
                                      {issue.title}
                                    </h5>
                                    <span
                                      className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(
                                        issue.severity
                                      )}`}
                                    >
                                      {issue.severity}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600 mt-1">
                                    {issue.description}
                                  </p>
                                  <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                                    <span>📁 {issue.file_path}</span>
                                    {issue.line_number && (
                                      <span>Line {issue.line_number}</span>
                                    )}
                                    <span className="px-2 py-0.5 bg-gray-100 rounded">
                                      {issue.category}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                {/* Recommendations */}
                {report.analysis.recommendations &&
                  report.analysis.recommendations.length > 0 && (
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 mb-3">
                        💡 Recommendations
                      </h4>
                      <div className="space-y-2">
                        {report.analysis.recommendations
                          .slice(0, 5)
                          .map((rec, index) => (
                            <div
                              key={index}
                              className="bg-blue-50 border border-blue-200 rounded-lg p-3"
                            >
                              <div className="flex items-start space-x-2">
                                <FaInfoCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                <div>
                                  <h6 className="font-medium text-blue-900">
                                    {rec.title}
                                  </h6>
                                  <p className="text-sm text-blue-700 mt-1">
                                    {rec.description}
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  )}

                {/* Success Message with No Issues */}
                {report.analysis.total_issues === 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                    <FaCheckCircle className="h-12 w-12 text-green-600 mx-auto mb-3" />
                    <h4 className="text-lg font-semibold text-green-900">
                      Excellent! No Issues Found
                    </h4>
                    <p className="text-green-700 mt-2">
                      Your repository passed all security and quality checks.
                    </p>
                  </div>
                )}
              </div>
            )}

          {/* Close Button */}
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              className="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              onClick={onClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
