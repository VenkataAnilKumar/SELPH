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

interface TwinStats {
  total_messages: number;
  pending_drafts: number;
  processed_drafts: number;
  total_estimated_tokens: number;
  total_estimated_cost_usd: number;
  fallback_rate: number;
  approval_rate: number;
  generation_source_breakdown: Record<string, number>;
  model_breakdown: Record<string, number>;
  fallback_reason_breakdown: Record<string, number>;
}

interface Draft {
  id: string;
  content: string;
  status: string;
  confidence_score: number;
  confidence_label: string;
  confidence_reasoning?: string | null;
  generation_source?: string | null;
  llm_model?: string | null;
  fallback_reason?: string | null;
  estimated_total_tokens?: number | null;
  estimated_cost_usd?: number | null;
  created_at: string;
}

interface IdentityProfile {
  vocabulary_description?: string | null;
  communication_style?: string | null;
  topics_known: string[];
  topics_avoided: string[];
  profile_complete: boolean;
}

interface ConnectedChannel {
  channel: string;
  connected: boolean;
  scope?: string | null;
  updated_at: string;
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [twin, setTwin] = useState<Twin | null>(null);
  const [stats, setStats] = useState<TwinStats | null>(null);
  const [pendingDrafts, setPendingDrafts] = useState<Draft[]>([]);
  const [identityProfile, setIdentityProfile] = useState<IdentityProfile | null>(null);
  const [channels, setChannels] = useState<ConnectedChannel[]>([]);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [activeDraftId, setActiveDraftId] = useState<string | null>(null);
  const [editDraftId, setEditDraftId] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState<string>("");
  const [settingsDomain, setSettingsDomain] = useState<string>("");
  const [settingsTone, setSettingsTone] = useState<string>("");
  const [onboardingRole, setOnboardingRole] = useState<string>("");
  const [onboardingStyle, setOnboardingStyle] = useState<string>("friendly");
  const [onboardingAvoidedTopics, setOnboardingAvoidedTopics] = useState<string>("");
  const [onboardingLength, setOnboardingLength] = useState<string>("medium");
  const [onboardingAudienceTone, setOnboardingAudienceTone] = useState<string>("");
  const [onboardingThreeWords, setOnboardingThreeWords] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [twinResponse, statsResponse, draftsResponse, identityResponse, channelsResponse] = await Promise.all([
          apiClient.get("/twin/me"),
          apiClient.get("/twin/stats"),
          apiClient.get("/drafts/pending"),
          apiClient.get("/identity/profile"),
          apiClient.get("/channels/connected"),
        ]);

        setTwin(twinResponse.data);
        setSettingsDomain(twinResponse.data.domain || "");
        setSettingsTone(twinResponse.data.tone || "");
        setStats(statsResponse.data);
        setPendingDrafts(draftsResponse.data);
        setIdentityProfile(identityResponse.data);
        setChannels(channelsResponse.data);
        setError(null);
      } catch (err: any) {
        setError(
          err.response?.data?.detail || "Failed to load dashboard"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  const refreshDashboard = async () => {
    try {
      const [statsResponse, draftsResponse, channelsResponse] = await Promise.all([
        apiClient.get("/twin/stats"),
        apiClient.get("/drafts/pending"),
        apiClient.get("/channels/connected"),
      ]);

      setStats(statsResponse.data);
      setPendingDrafts(draftsResponse.data);
      setChannels(channelsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to refresh dashboard");
    }
  };

  // Auto-refresh: 30-second interval + visibility-change revalidation
  useEffect(() => {
    const intervalId = setInterval(() => {
      refreshDashboard();
    }, 30_000);

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        refreshDashboard();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      clearInterval(intervalId);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleDraftAction = async (
    draftId: string,
    action: "approve" | "reject" | "edit" | "skip",
    editedValue?: string
  ) => {
    setActionMessage(null);
    setActionError(null);
    setActiveDraftId(draftId);

    try {
      await apiClient.approveDraft(draftId, action, editedValue);
      await refreshDashboard();
      setActionMessage(
        action === "edit"
          ? "Draft updated and approved."
          : `Draft ${action}d successfully.`
      );

      if (action === "edit") {
        setEditDraftId(null);
        setEditedContent("");
      }
    } catch (err: any) {
      setActionError(
        err.response?.data?.detail || `Failed to ${action} draft`
      );
    } finally {
      setActiveDraftId(null);
    }
  };

  const handleCompleteOnboarding = async () => {
    try {
      setActionError(null);
      const avoided = onboardingAvoidedTopics
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);
      const threeWords = onboardingThreeWords
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);

      await apiClient.post("/identity/onboard", {
        role: onboardingRole,
        communication_style: onboardingStyle,
        topics_avoided: avoided,
        response_length: onboardingLength,
        audience_tone: onboardingAudienceTone,
        three_words: threeWords,
      });

      const [identityResponse, twinResponse] = await Promise.all([
        apiClient.get("/identity/profile"),
        apiClient.get("/twin/me"),
      ]);

      setIdentityProfile(identityResponse.data);
      setTwin(twinResponse.data);
      setSettingsDomain(twinResponse.data.domain || "");
      setSettingsTone(twinResponse.data.tone || "");
      setActionMessage("Onboarding saved. Your twin is now configured.");
    } catch (err: any) {
      setActionError(err.response?.data?.detail || "Failed to complete onboarding");
    }
  };

  const connectChannel = async (channel: "instagram" | "gmail") => {
    try {
      setActionError(null);
      const endpoint = channel === "instagram" ? "/channels/instagram/connect" : "/channels/gmail/connect";
      await apiClient.post(endpoint, {});
      await refreshDashboard();
      setActionMessage(`${channel} connected successfully.`);
    } catch (err: any) {
      setActionError(err.response?.data?.detail || `Failed to connect ${channel}`);
    }
  };

  const disconnectChannel = async (channel: string) => {
    try {
      setActionError(null);
      await apiClient.post(`/channels/${channel}/disconnect`);
      await refreshDashboard();
      setActionMessage(`${channel} disconnected.`);
    } catch (err: any) {
      setActionError(err.response?.data?.detail || `Failed to disconnect ${channel}`);
    }
  };

  const toggleTwinStatus = async () => {
    if (!twin) return;
    try {
      setActionError(null);
      const response = twin.status === "active"
        ? await apiClient.post("/twin/pause")
        : await apiClient.post("/twin/resume");
      setTwin(response.data);
      setActionMessage(
        response.data.status === "active"
          ? "Twin resumed and processing is active."
          : "Twin paused successfully."
      );
    } catch (err: any) {
      setActionError(err.response?.data?.detail || "Failed to update twin status");
    }
  };

  const updateTwinSettings = async () => {
    try {
      setActionError(null);
      const response = await apiClient.put("/twin/me", {
        domain: settingsDomain,
        tone: settingsTone,
      });
      setTwin(response.data);
      setActionMessage("Twin settings updated.");
    } catch (err: any) {
      setActionError(err.response?.data?.detail || "Failed to update twin settings");
    }
  };

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

          {actionMessage && (
            <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 text-green-700">
              {actionMessage}
            </div>
          )}

          {actionError && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
              {actionError}
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
                  Approval Loop
                </h2>
                {stats ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-sm text-gray-600">Pending Drafts</p>
                      <p className="mt-2 text-3xl font-bold text-gray-900">
                        {stats.pending_drafts}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-sm text-gray-600">Processed Drafts</p>
                      <p className="mt-2 text-3xl font-bold text-gray-900">
                        {stats.processed_drafts}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-sm text-gray-600">Messages Seen</p>
                      <p className="mt-2 text-3xl font-bold text-gray-900">
                        {stats.total_messages}
                      </p>
                    </div>
                    <div className="rounded-lg bg-slate-50 p-4">
                      <p className="text-sm text-gray-600">Fallback Rate</p>
                      <p className="mt-2 text-3xl font-bold text-gray-900">
                        {(stats.fallback_rate * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="col-span-2 rounded-lg bg-green-50 p-4">
                      <p className="text-sm text-green-700 font-medium">Approval Rate</p>
                      <p className="mt-2 text-3xl font-bold text-green-800">
                        {(stats.approval_rate * 100).toFixed(0)}%
                      </p>
                      <p className="mt-1 text-xs text-green-600">
                        Approved + edited vs total decided
                      </p>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-600">No stats available yet.</p>
                )}
              </div>
            </div>
          )}

          {identityProfile && !identityProfile.profile_complete && (
            <section className="mt-8 rounded-lg bg-white p-8 shadow">
              <h2 className="text-2xl font-bold text-gray-900">Identity Onboarding</h2>
              <p className="mt-1 text-sm text-gray-600">
                Configure your twin's voice before live channel usage.
              </p>
              <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                <input
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Role or domain"
                  value={onboardingRole}
                  onChange={(event) => setOnboardingRole(event.target.value)}
                />
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={onboardingStyle}
                  onChange={(event) => setOnboardingStyle(event.target.value)}
                >
                  <option value="formal">formal</option>
                  <option value="casual">casual</option>
                  <option value="friendly">friendly</option>
                  <option value="direct">direct</option>
                  <option value="humorous">humorous</option>
                </select>
                <input
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm md:col-span-2"
                  placeholder="Topics to avoid (comma separated)"
                  value={onboardingAvoidedTopics}
                  onChange={(event) => setOnboardingAvoidedTopics(event.target.value)}
                />
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={onboardingLength}
                  onChange={(event) => setOnboardingLength(event.target.value)}
                >
                  <option value="short">short</option>
                  <option value="medium">medium</option>
                  <option value="detailed">detailed</option>
                </select>
                <input
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Audience tone"
                  value={onboardingAudienceTone}
                  onChange={(event) => setOnboardingAudienceTone(event.target.value)}
                />
                <input
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm md:col-span-2"
                  placeholder="Three words describing you (comma separated)"
                  value={onboardingThreeWords}
                  onChange={(event) => setOnboardingThreeWords(event.target.value)}
                />
              </div>
              <button
                onClick={handleCompleteOnboarding}
                className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Save Onboarding
              </button>
            </section>
          )}

          <section className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
            <div className="rounded-lg bg-white p-8 shadow">
              <h2 className="text-2xl font-bold text-gray-900">Channel Connections</h2>
              <p className="mt-1 text-sm text-gray-600">Connect Instagram and Gmail to receive incoming messages.</p>
              <div className="mt-6 space-y-4">
                {["instagram", "gmail"].map((channel) => {
                  const current = channels.find((item) => item.channel === channel);
                  const connected = !!current?.connected;
                  return (
                    <div key={channel} className="flex items-center justify-between rounded-lg border border-gray-200 p-4">
                      <div>
                        <p className="font-medium text-gray-900 capitalize">{channel}</p>
                        <p className="text-xs text-gray-500">
                          {connected ? "Connected" : "Not connected"}
                        </p>
                      </div>
                      {connected ? (
                        <button
                          onClick={() => disconnectChannel(channel)}
                          className="rounded-lg bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-700"
                        >
                          Disconnect
                        </button>
                      ) : (
                        <button
                          onClick={() => connectChannel(channel as "instagram" | "gmail")}
                          className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700"
                        >
                          Connect
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="rounded-lg bg-white p-8 shadow">
              <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
              <p className="mt-1 text-sm text-gray-600">Pause/resume your twin and tune its profile.</p>
              <div className="mt-6 space-y-3">
                <input
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Domain"
                  value={settingsDomain}
                  onChange={(event) => setSettingsDomain(event.target.value)}
                />
                <input
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  placeholder="Tone"
                  value={settingsTone}
                  onChange={(event) => setSettingsTone(event.target.value)}
                />
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={updateTwinSettings}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    Update Tone/Domain
                  </button>
                  <button
                    onClick={toggleTwinStatus}
                    className={`rounded-lg px-4 py-2 text-sm font-medium text-white ${
                      twin?.status === "active" ? "bg-amber-600 hover:bg-amber-700" : "bg-emerald-600 hover:bg-emerald-700"
                    }`}
                  >
                    {twin?.status === "active" ? "Pause Twin" : "Resume Twin"}
                  </button>
                </div>
              </div>
            </div>
          </section>

          <div className="mt-12 grid grid-cols-1 gap-8 xl:grid-cols-[2fr_1fr]">
            <section className="rounded-lg bg-white p-8 shadow">
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    Pending Drafts
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">
                    Review generated replies before SELPH sends anything.
                  </p>
                </div>
                <span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700">
                  {pendingDrafts.length} awaiting review
                </span>
              </div>

              {pendingDrafts.length === 0 ? (
                <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-gray-600">
                  No drafts are waiting for approval.
                </div>
              ) : (
                <div className="space-y-6">
                  {pendingDrafts.map((draft) => {
                    const isEditing = editDraftId === draft.id;
                    const isSubmitting = activeDraftId === draft.id;

                    return (
                      <article
                        key={draft.id}
                        className="rounded-xl border border-gray-200 p-6"
                      >
                        <div className="flex flex-wrap items-center gap-3">
                          <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-700">
                            {draft.confidence_label} confidence
                          </span>
                          <span className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700">
                            {draft.generation_source || "unknown source"}
                          </span>
                          <span className="text-xs text-gray-500">
                            {draft.llm_model || "No model recorded"}
                          </span>
                        </div>

                        <p className="mt-4 whitespace-pre-wrap text-gray-900">
                          {draft.content}
                        </p>

                        <div className="mt-4 grid gap-3 text-sm text-gray-600 sm:grid-cols-2">
                          <p>
                            Confidence score: {draft.confidence_score.toFixed(2)}
                          </p>
                          <p>
                            Estimated tokens: {draft.estimated_total_tokens ?? 0}
                          </p>
                          <p>
                            Estimated cost: ${Number(draft.estimated_cost_usd ?? 0).toFixed(4)}
                          </p>
                          <p>
                            Fallback reason: {draft.fallback_reason || "None"}
                          </p>
                        </div>

                        {draft.confidence_reasoning && (
                          <p className="mt-3 text-sm text-gray-600">
                            {draft.confidence_reasoning}
                          </p>
                        )}

                        {isEditing && (
                          <div className="mt-4 rounded-lg bg-gray-50 p-4">
                            <label className="mb-2 block text-sm font-medium text-gray-900">
                              Edited response
                            </label>
                            <textarea
                              value={editedContent}
                              onChange={(event) => setEditedContent(event.target.value)}
                              className="min-h-32 w-full rounded-lg border border-gray-300 p-3 text-sm text-gray-900 outline-none focus:border-blue-500"
                            />
                            <div className="mt-3 flex gap-3">
                              <button
                                onClick={() =>
                                  handleDraftAction(
                                    draft.id,
                                    "edit",
                                    editedContent
                                  )
                                }
                                disabled={isSubmitting || editedContent.trim().length === 0}
                                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                              >
                                Save Edit
                              </button>
                              <button
                                onClick={() => {
                                  setEditDraftId(null);
                                  setEditedContent("");
                                }}
                                className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 ring-1 ring-gray-300 hover:bg-gray-50"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}

                        <div className="mt-5 flex flex-wrap gap-3">
                          <button
                            onClick={() => handleDraftAction(draft.id, "approve")}
                            disabled={isSubmitting}
                            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-300"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => {
                              setEditDraftId(draft.id);
                              setEditedContent(draft.content);
                            }}
                            disabled={isSubmitting}
                            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDraftAction(draft.id, "reject")}
                            disabled={isSubmitting}
                            className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-rose-300"
                          >
                            Reject
                          </button>
                          <button
                            onClick={() => handleDraftAction(draft.id, "skip")}
                            disabled={isSubmitting}
                            className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-300 disabled:cursor-not-allowed disabled:bg-gray-100"
                          >
                            Skip
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            <aside className="rounded-lg bg-white p-8 shadow">
              <h2 className="text-2xl font-bold text-gray-900">Model Signals</h2>
              {stats ? (
                <div className="mt-6 space-y-6 text-sm text-gray-700">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      Generation Sources
                    </h3>
                    <div className="mt-3 space-y-2">
                      {Object.entries(stats.generation_source_breakdown).map(
                        ([source, count]) => (
                          <div key={source} className="flex justify-between">
                            <span>{source}</span>
                            <span className="font-medium text-gray-900">{count}</span>
                          </div>
                        )
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900">Models</h3>
                    <div className="mt-3 space-y-2">
                      {Object.entries(stats.model_breakdown).map(([model, count]) => (
                        <div key={model} className="flex justify-between">
                          <span>{model}</span>
                          <span className="font-medium text-gray-900">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-gray-900">Fallback Reasons</h3>
                    <div className="mt-3 space-y-2">
                      {Object.keys(stats.fallback_reason_breakdown).length === 0 ? (
                        <p className="text-gray-500">No fallbacks recorded.</p>
                      ) : (
                        Object.entries(stats.fallback_reason_breakdown).map(
                          ([reason, count]) => (
                            <div key={reason} className="flex justify-between">
                              <span>{reason}</span>
                              <span className="font-medium text-gray-900">{count}</span>
                            </div>
                          )
                        )
                      )}
                    </div>
                  </div>

                  <div className="rounded-lg bg-gray-50 p-4">
                    <p className="text-sm text-gray-600">Estimated spend</p>
                    <p className="mt-2 text-2xl font-bold text-gray-900">
                      ${stats.total_estimated_cost_usd.toFixed(4)}
                    </p>
                    <p className="mt-1 text-sm text-gray-600">
                      {stats.total_estimated_tokens} tokens processed so far
                    </p>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-gray-600">Stats will appear after draft activity.</p>
              )}
            </aside>
          </div>

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
