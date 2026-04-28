"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { ProtectedRoute } from "@/components/protected-route";
import { apiClient } from "@selph/shared";

interface Twin {
  id: string;
  user_id: string;
  domain: string;
  tone: string;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [twin, setTwin] = useState<Twin | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTwin = async () => {
      try {
        const response = await apiClient.get("/twin/me");
        setTwin(response.data);
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "Failed to load twin profile"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTwin();
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-100">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">SELPH</h1>
              <p className="text-gray-600">Your Digital Twin Dashboard</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm text-gray-600">Logged in as</p>
                <p className="font-medium text-gray-900">{user?.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading twin profile...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              {error}
            </div>
          )}

          {twin && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Twin Profile Card */}
              <div className="bg-white rounded-lg shadow p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Twin Profile
                </h2>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-600">Twin ID</p>
                    <p className="font-mono text-sm text-gray-900">{twin.id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Domain</p>
                    <p className="font-medium text-gray-900">{twin.domain}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Tone</p>
                    <p className="font-medium text-gray-900">{twin.tone}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Status</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          twin.status === "active"
                            ? "bg-green-500"
                            : "bg-yellow-500"
                        }`}
                      ></div>
                      <p className="capitalize font-medium text-gray-900">
                        {twin.status}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-white rounded-lg shadow p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  Quick Actions
                </h2>
                <div className="space-y-3">
                  <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
                    View Messages
                  </button>
                  <button className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium">
                    Approve Drafts
                  </button>
                  <button className="w-full px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium">
                    Update Twin Profile
                  </button>
                  <button className="w-full px-4 py-3 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 font-medium">
                    View Settings
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Getting Started Guide */}
          <div className="mt-12 bg-white rounded-lg shadow p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Getting Started
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white mb-4">
                  <span className="text-lg font-bold">1</span>
                </div>
                <h3 className="font-medium text-gray-900">Connect Channels</h3>
                <p className="mt-2 text-sm text-gray-600">
                  Link your Instagram, Gmail, or other communication channels to
                  start receiving messages.
                </p>
              </div>
              <div>
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-green-500 text-white mb-4">
                  <span className="text-lg font-bold">2</span>
                </div>
                <h3 className="font-medium text-gray-900">Customize Your Twin</h3>
                <p className="mt-2 text-sm text-gray-600">
                  Set your twin's domain, tone, vocabulary, and communication
                  style.
                </p>
              </div>
              <div>
                <div className="flex items-center justify-center h-12 w-12 rounded-md bg-purple-500 text-white mb-4">
                  <span className="text-lg font-bold">3</span>
                </div>
                <h3 className="font-medium text-gray-900">Review & Approve</h3>
                <p className="mt-2 text-sm text-gray-600">
                  Your twin will generate responses, and you'll review and approve
                  before they're sent.
                </p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
}
