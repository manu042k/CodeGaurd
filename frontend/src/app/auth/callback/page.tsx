"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useSession } from "next-auth/react";

function AuthCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { data: session, status } = useSession();
  const [message, setMessage] = useState("Processing authentication...");
  const [isSuccess, setIsSuccess] = useState(false);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const error = searchParams.get("error");
        
        if (error) {
          setIsError(true);
          setMessage("Authentication failed. Redirecting...");
          setTimeout(() => {
            router.push(`/auth/error?error=${error}`);
          }, 2000);
          return;
        }

        if (status === "authenticated" && session) {
          setIsSuccess(true);
          setMessage("Authentication successful! Redirecting...");
          setTimeout(() => {
            router.push("/dashboard");
          }, 1500);
        } else if (status === "unauthenticated") {
          setIsError(true);
          setMessage("Authentication failed. Redirecting...");
          setTimeout(() => {
            router.push("/auth/signin");
          }, 2000);
        }
      } catch (error) {
        console.error("Authentication callback error:", error);
        setIsError(true);
        setMessage("Authentication failed. Redirecting...");
        setTimeout(() => {
          router.push("/auth/signin");
        }, 2000);
      }
    };

    if (status !== "loading") {
      handleCallback();
    }
  }, [searchParams, router, status, session]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-6">
          {status === "loading" && (
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
          )}
          {isSuccess && (
            <div className="text-green-500">
              <svg
                className="w-12 h-12 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          )}
          {isError && (
            <div className="text-red-500">
              <svg
                className="w-12 h-12 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </div>
          )}
        </div>

        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {status === "loading" && "Authenticating..."}
          {isSuccess && "Success!"}
          {isError && "Authentication Failed"}
        </h2>

        <p className="text-gray-600">{message}</p>
      </div>
    </div>
  );
}

export default function AuthCallback() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-xl shadow-lg">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
              <h2 className="mt-6 text-3xl font-bold text-gray-900">
                Loading...
              </h2>
              <p className="text-gray-600">Processing authentication...</p>
            </div>
          </div>
        </div>
      }
    >
      <AuthCallbackContent />
    </Suspense>
  );
}
