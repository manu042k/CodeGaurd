"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";

interface AnalysisResult {
  analysis_id: string;
  success: boolean;
  overall_score?: number;
  agents_executed: string[];
  category_breakdown: Record<string, number>;
  all_issues: Array<{
    file: string;
    line?: number;
    desc: string;
    severity: string;
    category: string;
  }>;
  summary: string;
  timestamp: string;
  error?: string;
}

interface AnalysisRequest {
  repo_url: string;
  branch?: string;
  agents?: string[];
}

function AnalysisContent() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);

  const searchParams = useSearchParams();
  const analysisId = searchParams.get("id");

  const availableAgents = [
    "code_quality",
    "security",
    "architecture",
    "documentation",
    "testing",
    "dependency",
    "static_tool",
  ];

  useEffect(() => {
    if (analysisId) {
      fetchAnalysisResult(analysisId);
    }
  }, [analysisId]);

  const fetchAnalysisResult = async (id: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/analysis/analyze/${id}`);

      if (!response.ok) {
        throw new Error("Failed to fetch analysis result");
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const startAnalysis = async () => {
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const request: AnalysisRequest = {
        repo_url: repoUrl,
        branch: branch || "main",
        agents: selectedAgents.length > 0 ? selectedAgents : undefined,
      };

      const response = await fetch("/api/analysis/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error("Failed to start analysis");
      }

      const data = await response.json();

      if (data.success && data.result_id) {
        // Poll for results
        pollForResults(data.result_id);
      } else {
        throw new Error(data.error || "Analysis failed to start");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setLoading(false);
    }
  };

  const pollForResults = async (id: string) => {
    const maxAttempts = 60; // 5 minutes with 5-second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/analysis/analyze/${id}`);

        if (response.ok) {
          const data = await response.json();
          setResult(data);
          setLoading(false);
          return;
        }

        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else {
          throw new Error("Analysis timed out");
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Polling failed");
        setLoading(false);
      }
    };

    poll();
  };

  const toggleAgent = (agent: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agent) ? prev.filter((a) => a !== agent) : [...prev, agent]
    );
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return "text-red-600 bg-red-100";
      case "medium":
        return "text-yellow-600 bg-yellow-100";
      case "low":
        return "text-blue-600 bg-blue-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Static Code Analysis</h1>

        {/* Analysis Form */}
        {!result && (
          <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Start New Analysis</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Repository URL
                </label>
                <input
                  type="url"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/user/repo.git"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Branch</label>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">
                  Select Agents (leave empty for all)
                </label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {availableAgents.map((agent) => (
                    <label key={agent} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(agent)}
                        onChange={() => toggleAgent(agent)}
                        className="mr-2"
                      />
                      <span className="text-sm capitalize">
                        {agent.replace("_", " ")}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <button
                onClick={startAnalysis}
                disabled={loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? "Analyzing..." : "Start Analysis"}
              </button>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="bg-white shadow-lg rounded-lg p-6 mb-8">
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">
                Analyzing repository...
              </span>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <div className="flex">
              <div className="text-red-400">
                <svg
                  className="w-5 h-5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Summary Card */}
            <div className="bg-white shadow-lg rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Analysis Summary</h2>
                <span className="text-sm text-gray-500">
                  {new Date(result.timestamp).toLocaleDateString()}
                </span>
              </div>

              {result.success ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="text-center">
                    <div
                      className={`text-3xl font-bold ${getScoreColor(
                        result.overall_score || 0
                      )}`}
                    >
                      {result.overall_score || 0}
                    </div>
                    <div className="text-sm text-gray-600">Overall Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {result.agents_executed.length}
                    </div>
                    <div className="text-sm text-gray-600">Agents Run</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-orange-600">
                      {result.all_issues.length}
                    </div>
                    <div className="text-sm text-gray-600">Issues Found</div>
                  </div>
                </div>
              ) : (
                <div className="text-red-600 font-medium">
                  Analysis failed: {result.error}
                </div>
              )}

              {result.summary && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <p className="text-gray-700">{result.summary}</p>
                </div>
              )}
            </div>

            {/* Category Breakdown */}
            {Object.keys(result.category_breakdown).length > 0 && (
              <div className="bg-white shadow-lg rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">
                  Category Breakdown
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(result.category_breakdown).map(
                    ([category, score]) => (
                      <div key={category} className="text-center">
                        <div
                          className={`text-2xl font-bold ${getScoreColor(
                            score
                          )}`}
                        >
                          {score}
                        </div>
                        <div className="text-sm text-gray-600 capitalize">
                          {category.replace("_", " ")}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* Issues List */}
            {result.all_issues.length > 0 && (
              <div className="bg-white shadow-lg rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">
                  Issues Found ({result.all_issues.length})
                </h3>
                <div className="space-y-3">
                  {result.all_issues.slice(0, 50).map((issue, index) => (
                    <div
                      key={index}
                      className="border border-gray-200 rounded-lg p-3"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">
                            {issue.file}
                            {issue.line && (
                              <span className="text-gray-500">
                                :{issue.line}
                              </span>
                            )}
                          </div>
                          <p className="text-gray-700 mt-1">{issue.desc}</p>
                        </div>
                        <div className="ml-4 flex items-center space-x-2">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(
                              issue.severity
                            )}`}
                          >
                            {issue.severity}
                          </span>
                          <span className="text-xs text-gray-500 capitalize">
                            {issue.category}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                  {result.all_issues.length > 50 && (
                    <div className="text-center text-gray-500 text-sm">
                      Showing first 50 of {result.all_issues.length} issues
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Start New Analysis Button */}
            <div className="text-center">
              <button
                onClick={() => {
                  setResult(null);
                  setError(null);
                  setRepoUrl("");
                  setBranch("main");
                  setSelectedAgents([]);
                }}
                className="bg-gray-600 text-white py-2 px-6 rounded-md hover:bg-gray-700"
              >
                Start New Analysis
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingFallback() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Static Code Analysis</h1>
        <div className="bg-white shadow-lg rounded-lg p-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading...</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <AnalysisContent />
    </Suspense>
  );
}
