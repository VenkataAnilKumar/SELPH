"use client";

/**
 * Twin Briefings: tell your twin something once and every draft reflects it
 * (e.g. "at a conference this week, keep replies short").
 */

import React, { useCallback, useEffect, useState } from "react";
import { apiClient } from "@selph/shared";

export interface Briefing {
  id: string;
  briefing_type: string;
  topic: string;
  content: string;
  priority: number;
  is_active: boolean;
  expires_at?: string | null;
  max_uses?: number | null;
  use_count: number;
  cleared_at?: string | null;
}

export const BRIEFING_TYPES = [
  { value: "availability", label: "Availability", hint: "Added to drafts as a heads-up" },
  { value: "instruction", label: "Instruction", hint: "How to reply right now" },
  { value: "fact", label: "Fact", hint: "Something true the twin should know" },
  { value: "opinion", label: "Opinion", hint: "A stance to reflect" },
  { value: "boundary", label: "Boundary", hint: "Something to stay away from" },
];

export const BriefingsPanel = () => {
  const [items, setItems] = useState<Briefing[]>([]);
  const [loading, setLoading] = useState(true);
  const [type, setType] = useState("availability");
  const [topic, setTopic] = useState("");
  const [content, setContent] = useState("");
  const [priority, setPriority] = useState(5);
  const [expiresInHours, setExpiresInHours] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await apiClient.get("/identity/briefings");
      setItems(response.data.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load briefings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const canSubmit = topic.trim().length > 0 && content.trim().length > 0 && !busy;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      const hours = Number(expiresInHours);
      await apiClient.post("/identity/briefings", {
        briefing_type: type,
        topic: topic.trim(),
        content: content.trim(),
        priority,
        ...(hours > 0 ? { expires_at: new Date(Date.now() + hours * 3600_000).toISOString() } : {}),
      });
      setTopic("");
      setContent("");
      setExpiresInHours("");
      await load();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to save briefing");
    } finally {
      setBusy(false);
    }
  };

  const clear = async (id: string) => {
    setError(null);
    try {
      await apiClient.post(`/identity/briefings/${id}/clear`);
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to clear briefing");
    }
  };

  const active = items.filter((b) => b.is_active && !b.cleared_at);

  return (
    <section className="rounded-lg bg-white p-8 shadow" data-testid="briefings-panel">
      <h2 className="text-2xl font-bold text-gray-900">Twin Briefings</h2>
      <p className="mt-1 text-sm text-gray-600">
        Tell your twin something once; every draft reflects it until it expires or you clear it.
      </p>

      <form onSubmit={submit} className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-2">
        <select
          aria-label="Briefing type"
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        >
          {BRIEFING_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <p className="-mt-1 text-xs text-gray-500 md:col-span-2" data-testid="briefing-type-hint">
          {BRIEFING_TYPES.find((t) => t.value === type)?.hint}
        </p>
        <input
          aria-label="Briefing topic"
          placeholder="Topic (e.g. conference week)"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <textarea
          aria-label="Briefing content"
          placeholder="What should your twin know? (e.g. I'm traveling, replies may be slower)"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={2}
          className="rounded border border-gray-300 px-3 py-2 md:col-span-2"
        />
        <label className="flex items-center gap-2 text-sm text-gray-700">
          Priority
          <input
            aria-label="Briefing priority"
            type="number"
            min={1}
            max={10}
            value={priority}
            onChange={(e) => setPriority(Math.min(10, Math.max(1, Number(e.target.value) || 1)))}
            className="w-20 rounded border border-gray-300 px-2 py-1"
          />
        </label>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          Expires in (hours)
          <input
            aria-label="Expires in hours"
            type="number"
            min={1}
            placeholder="never"
            value={expiresInHours}
            onChange={(e) => setExpiresInHours(e.target.value)}
            className="w-24 rounded border border-gray-300 px-2 py-1"
          />
        </label>
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Saving…" : "Add briefing"}
          </button>
          {error && <span className="ml-4 text-sm text-red-700">{error}</span>}
        </div>
      </form>

      <div className="mt-6">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Active ({active.length})
        </h3>
        {loading ? (
          <p className="mt-2 text-sm text-gray-500">Loading…</p>
        ) : active.length === 0 ? (
          <p className="mt-2 text-sm text-gray-500">No active briefings. Your twin is using only your profile.</p>
        ) : (
          <ul className="mt-2 space-y-3">
            {active.map((b) => (
              <li key={b.id} className="flex items-start justify-between rounded border border-gray-200 p-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    <span className="mr-2 rounded bg-blue-50 px-2 py-0.5 text-xs uppercase text-blue-700">
                      {b.briefing_type}
                    </span>
                    {b.topic}
                    <span className="ml-2 text-xs font-normal text-gray-500">P{b.priority}</span>
                  </p>
                  <p className="mt-1 text-sm text-gray-700">{b.content}</p>
                  <p className="mt-1 text-xs text-gray-500">
                    Used {b.use_count}
                    {b.max_uses ? ` / ${b.max_uses}` : ""} times
                    {b.expires_at ? ` · expires ${new Date(b.expires_at).toLocaleString()}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => clear(b.id)}
                  aria-label={`Clear briefing ${b.topic}`}
                  className="rounded border border-gray-300 px-3 py-1 text-xs text-gray-700 hover:bg-gray-50"
                >
                  Clear
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
};
