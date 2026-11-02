"use client";

/**
 * Simulate an incoming message so the full message -> draft -> approve loop
 * can be tried locally without connecting Instagram or Gmail.
 */

import React, { useState } from "react";
import { apiClient } from "@selph/shared";

interface SimulateMessageProps {
  onIngested: () => void | Promise<void>;
}

const CHANNELS = [
  { value: "instagram_dm", label: "Instagram DM" },
  { value: "gmail", label: "Gmail" },
  { value: "manual", label: "Manual" },
];

export const SimulateMessage = ({ onIngested }: SimulateMessageProps) => {
  const [channel, setChannel] = useState("instagram_dm");
  const [senderName, setSenderName] = useState("");
  const [senderId, setSenderId] = useState("");
  const [content, setContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = content.trim().length > 0 && !busy;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const name = senderName.trim() || "Test Sender";
      const response = await apiClient.post("/messages/ingest", {
        channel,
        sender_name: name,
        sender_id: senderId.trim() || name.toLowerCase().replace(/\s+/g, "_"),
        content: content.trim(),
      });
      const data = response.data;
      // Refresh the dashboard first so the message never points at a list that does not show the draft yet.
      setContent("");
      await onIngested();
      if (data.draft_id) {
        setResult("Draft created — review it under Pending Drafts.");
      } else if (data.routing_action === "direct_notify") {
        setResult("VIP sender: routed straight to you, no draft created.");
      } else if (data.routing_action === "skipped_manual_pause") {
        setResult("Twin is paused: no draft created.");
      } else {
        setResult(`Message received (${data.routing_action || data.status}).`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to send test message");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="mt-8 rounded-lg bg-white p-8 shadow" data-testid="simulate-message">
      <h2 className="text-2xl font-bold text-gray-900">Simulate Incoming Message</h2>
      <p className="mt-1 text-sm text-gray-600">
        Try your twin without connecting a channel. Nothing is ever sent externally.
      </p>
      <form onSubmit={submit} className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
        <select
          aria-label="Channel"
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        >
          {CHANNELS.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
        <input
          aria-label="Sender name"
          placeholder="Sender name (e.g. Priya)"
          value={senderName}
          onChange={(e) => setSenderName(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <input
          aria-label="Sender ID"
          placeholder="Sender ID (use a VIP's ID to test bypass)"
          value={senderId}
          onChange={(e) => setSenderId(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <textarea
          aria-label="Message"
          placeholder="Write the message your twin should reply to…"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          maxLength={10000}
          rows={3}
          className="rounded border border-gray-300 px-3 py-2 md:col-span-3"
        />
        <div className="flex items-center gap-4 md:col-span-3">
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Generating…" : "Send to my twin"}
          </button>
          {result && <span className="text-sm text-green-700">{result}</span>}
          {error && <span className="text-sm text-red-700">{error}</span>}
        </div>
      </form>
    </section>
  );
};
