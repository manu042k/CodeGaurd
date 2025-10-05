'use client'

import { useSession } from 'next-auth/react'
import Header from '@/components/Header'
import Link from 'next/link'
import { FaShieldAlt, FaCode, FaLock, FaGithub } from 'react-icons/fa'

export default function Home() {
  const { data: session } = useSession()

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="py-20 text-center">
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-center mb-8">
              <FaShieldAlt className="h-16 w-16 text-indigo-600" />
            </div>
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Secure Your Code with <span className="text-indigo-600">CodeGuard</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Protect your applications with advanced security analysis, vulnerability detection, 
              and automated code protection powered by AI.
            </p>
            
            {session ? (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center px-8 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors duration-200"
                >
                  Go to Dashboard
                </Link>
                <Link
                  href="/projects"
                  className="inline-flex items-center px-8 py-3 bg-white text-gray-900 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition-colors duration-200"
                >
                  View Projects
                </Link>
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  href="/auth/signin"
                  className="inline-flex items-center space-x-2 px-8 py-3 bg-gray-900 text-white rounded-lg font-semibold hover:bg-gray-800 transition-colors duration-200"
                >
                  <FaGithub className="h-5 w-5" />
                  <span>Get Started with GitHub</span>
                </Link>
                <Link
                  href="#features"
                  className="inline-flex items-center px-8 py-3 bg-white text-gray-900 border border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition-colors duration-200"
                >
                  Learn More
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why Choose CodeGuard?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Comprehensive security solutions for modern development teams
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-xl shadow-lg">
              <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-lg mb-6">
                <FaShieldAlt className="h-6 w-6 text-indigo-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Advanced Security Analysis
              </h3>
              <p className="text-gray-600">
                Real-time vulnerability detection and security analysis powered by AI 
                to keep your code safe from threats.
              </p>
            </div>

            <div className="bg-white p-8 rounded-xl shadow-lg">
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-6">
                <FaCode className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Code Quality Monitoring
              </h3>
              <p className="text-gray-600">
                Continuous monitoring of code quality with detailed reports and 
                actionable insights for improvement.
              </p>
            </div>

            <div className="bg-white p-8 rounded-xl shadow-lg">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-6">
                <FaLock className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Automated Protection
              </h3>
              <p className="text-gray-600">
                Automatic security patches and protection mechanisms to safeguard 
                your applications without manual intervention.
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        {!session && (
          <div className="py-20 text-center">
            <div className="bg-white rounded-2xl shadow-xl p-12 max-w-3xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Ready to Secure Your Code?
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Join thousands of developers who trust CodeGuard to protect their applications.
              </p>
              <Link
                href="/auth/signin"
                className="inline-flex items-center space-x-2 px-8 py-4 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors duration-200 text-lg"
              >
                <FaGithub className="h-5 w-5" />
                <span>Start Free with GitHub</span>
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
            href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Image
              className="dark:invert"
              src="/vercel.svg"
              alt="Vercel logomark"
              width={20}
              height={20}
            />
            Deploy now
          </a>
          <a
            className="rounded-full border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto md:w-[158px]"
            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            Read our docs
          </a>
        </div>
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/file.svg"
            alt="File icon"
            width={16}
            height={16}
          />
          Learn
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
          />
          Examples
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://nextjs.org?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/globe.svg"
            alt="Globe icon"
            width={16}
            height={16}
          />
          Go to nextjs.org →
        </a>
      </footer>
    </div>
  );
}
