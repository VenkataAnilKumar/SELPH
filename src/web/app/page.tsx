"use client";

import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'

export default function Home() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (err) {
      console.error('Logout failed:', err)
    }
  }

  return (
    <main className="min-h-screen bg-white">
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-4xl font-bold mb-4">SELPH</h1>
          <p className="text-xl text-gray-600 mb-8">Your Digital Twin AI</p>
          <p className="text-gray-500 mb-8">"Be everywhere. Be SELPH."</p>
          
          <div className="space-x-4 mb-8">
            {user ? (
              <>
                <Link
                  href="/dashboard"
                  className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Go to Dashboard
                </Link>
                <button
                  onClick={handleLogout}
                  className="inline-block px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/auth/login"
                  className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Log In
                </Link>
                <Link
                  href="/auth/signup"
                  className="inline-block px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
          
          {user && (
            <p className="text-gray-600 mb-8">
              Welcome back, <span className="font-medium">{user.email}</span>!
            </p>
          )}
          
          <p className="text-gray-400 mt-16 text-sm">
            Phase 0 — Authentication & Core Dashboard Ready
          </p>
        </div>
      </div>
    </main>
  )
}
