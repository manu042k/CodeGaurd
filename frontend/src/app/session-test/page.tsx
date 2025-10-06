"use client";

import { useSession } from "next-auth/react";
import { forceLogout } from "@/lib/auth-utils";
import { backendAPI } from "@/lib/backend-api";
import { useState } from "react";

export default function SessionTestPage() {
  const { data: session, status } = useSession();
  const [testResult, setTestResult] = useState<string>("");

  const testSessionExpiry = async () => {
    try {
      setTestResult("Testing session with invalid token...");
      // This should trigger a 401 and auto-logout
      await backendAPI.getProjects();
      setTestResult("❌ Test failed - should have triggered logout");
    } catch (error) {
      setTestResult(`✅ Auto-logout triggered: ${error}`);
    }
  };

  const manualLogout = () => {
    forceLogout("Manual test logout");
  };

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (!session) {
    return <div>Not authenticated</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">Session Test Page</h1>
      
      <div className="space-y-4">
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-semibold mb-2">Current Session Status</h2>
          <p>Status: {status}</p>
          <p>User: {session.user?.email}</p>
          <p>Backend Token: {session.backendToken ? "Present" : "Missing"}</p>
        </div>

        <div className="space-x-4">
          <button
            onClick={testSessionExpiry}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Test Session Expiry (401)
          </button>
          
          <button
            onClick={manualLogout}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Manual Logout
          </button>
        </div>

        {testResult && (
          <div className="bg-yellow-100 p-4 rounded">
            <p>{testResult}</p>
          </div>
        )}
      </div>
    </div>
  );
}
