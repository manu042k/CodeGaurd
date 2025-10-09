"use client";

import { useSession, signIn, signOut } from "next-auth/react";
import Link from "next/link";
import { FaGithub, FaUser, FaSignOutAlt } from "react-icons/fa";

export default function Header() {
  const { data: session, status } = useSession();

  const handleSignIn = () => {
    signIn("github", { callbackUrl: "/dashboard" });
  };

  const handleSignOut = () => {
    signOut({ callbackUrl: "/" });
  };

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="text-2xl font-bold text-indigo-600">
                CodeGuard
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link
              href="/dashboard"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Dashboard
            </Link>
            <Link
              href="/projects"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Projects
            </Link>
            <Link
              href="/repositories"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Repositories
            </Link>
            <Link
              href="/analysis"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Analysis
            </Link>
            <Link
              href="/docs"
              className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Documentation
            </Link>
          </nav>

          {/* Authentication */}
          <div className="flex items-center space-x-4">
            {status === "loading" ? (
              <div className="animate-pulse bg-gray-200 h-8 w-20 rounded"></div>
            ) : session ? (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  {session.user?.image ? (
                    <img
                      src={session.user.image}
                      alt={session.user?.name || "User"}
                      className="h-8 w-8 rounded-full"
                    />
                  ) : (
                    <FaUser className="h-8 w-8 text-gray-400 bg-gray-100 rounded-full p-2" />
                  )}
                  <span className="text-sm font-medium text-gray-700">
                    {session.user?.name || session.username}
                  </span>
                </div>
                <button
                  onClick={handleSignOut}
                  className="inline-flex items-center space-x-1 text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  <FaSignOutAlt className="h-4 w-4" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <button
                onClick={handleSignIn}
                className="inline-flex items-center space-x-2 bg-gray-900 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-800 transition-colors duration-200"
              >
                <FaGithub className="h-4 w-4" />
                <span>Sign in with GitHub</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
