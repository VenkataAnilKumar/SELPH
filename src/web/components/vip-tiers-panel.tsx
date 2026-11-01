"use client";

/**
 * VIP / relationship tiers: decide who your twin may answer.
 *   0 = bypass the twin (you are notified directly)
 *   1 = twin drafts, but you always review
 */

import React, { useCallback, useEffect, useState } from "react";
import { apiClient } from "@selph/shared";

export interface SenderTier {
  id: string;
  sender_id: string;
  platform: string;
  tier: number;
  tier_label?: string | null;
  notes?: string | null;
}

export const TIER_OPTIONS = [
  { value: 0, label: "VIP — bypass twin", description: "Never touched by the twin; you are notified directly" },
  { value: 1, label: "Review first", description: "Twin drafts, you always review" },
  { value: 2, label: "Standard", description: "Normal flow" },
  { value: 3, label: "Low priority", description: "Normal flow, lowest priority" },
];

const PLATFORMS = [
  { value: "instagram_dm", label: "Instagram DM" },
  { value: "gmail", label: "Gmail" },
];

export const VipTiersPanel = () => {
  const [items, setItems] = useState<SenderTier[]>([]);
  const [loading, setLoading] = useState(true);
  const [senderId, setSenderId] = useState("");
  const [platform, setPlatform] = useState("instagram_dm");
  const [tier, setTier] = useState(0);
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await apiClient.get("/identity/sender-tiers");
      setItems(response.data.items || []);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load sender tiers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const canSubmit = senderId.trim().length > 0 && !busy;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    setBusy(true);
    setError(null);
    try {
      await apiClient.put("/identity/sender-tiers", {
        sender_id: senderId.trim(),
        platform,
        tier,
        ...(label.trim() ? { tier_label: label.trim() } : {}),
      });
      setSenderId("");
      setLabel("");
      await load();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to save sender tier");
    } finally {
      setBusy(false);
    }
  };

  const remove = async (item: SenderTier) => {
    setError(null);
    try {
      await apiClient.delete(
        `/identity/sender-tiers/${encodeURIComponent(item.platform)}/${encodeURIComponent(item.sender_id)}`
      );
      await load();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to remove sender tier");
    }
  };

  const tierLabel = (value: number) => TIER_OPTIONS.find((t) => t.value === value)?.label ?? `Tier ${value}`;

  return (
    <section className="rounded-lg bg-white p-8 shadow" data-testid="vip-tiers-panel">
      <h2 className="text-2xl font-bold text-gray-900">VIP Senders</h2>
      <p className="mt-1 text-sm text-gray-600">
        Your closest relationships never get a templated reply. Use the sender ID exactly as the channel reports it.
      </p>

      <form onSubmit={submit} className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-2">
        <input
          aria-label="Sender ID"
          placeholder="Sender ID (e.g. james@cofounder.com)"
          value={senderId}
          onChange={(e) => setSenderId(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <select
          aria-label="Platform"
          value={platform}
          onChange={(e) => setPlatform(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        >
          {PLATFORMS.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
        <select
          aria-label="Tier"
          value={tier}
          onChange={(e) => setTier(Number(e.target.value))}
          className="rounded border border-gray-300 px-3 py-2"
        >
          {TIER_OPTIONS.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
        <input
          aria-label="Label"
          placeholder="Label (optional, e.g. Co-founder)"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          className="rounded border border-gray-300 px-3 py-2"
        />
        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={!canSubmit}
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {busy ? "Saving…" : "Save sender"}
          </button>
          {error && <span className="ml-4 text-sm text-red-700">{error}</span>}
        </div>
      </form>

      <div className="mt-6">
        {loading ? (
          <p className="text-sm text-gray-500">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-gray-500">No special senders yet. Everyone gets the standard flow.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((item) => (
              <li key={item.id} className="flex items-center justify-between rounded border border-gray-200 p-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {item.tier_label || item.sender_id}
                    <span
                      className={`ml-2 rounded px-2 py-0.5 text-xs ${
                        item.tier === 0 ? "bg-purple-50 text-purple-700" : "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {tierLabel(item.tier)}
                    </span>
                  </p>
                  <p className="text-xs text-gray-500">
                    {item.sender_id} · {item.platform}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => remove(item)}
                  aria-label={`Remove ${item.sender_id}`}
                  className="rounded border border-gray-300 px-3 py-1 text-xs text-gray-700 hover:bg-gray-50"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
};
