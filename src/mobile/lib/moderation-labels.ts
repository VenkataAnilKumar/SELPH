/**
 * Human-readable reasons for moderation flags returned on drafts (`moderation_flags[].category`).
 */

export interface ModerationFlag {
  pattern?: string | null;
  risk?: number | null;
  category?: string | null;
}

const LABELS: Record<string, string> = {
  prompt_injection: "The message tries to override your twin's instructions",
  sensitive_incoming: "Sensitive request: self-harm, medical, legal or financial. Reply yourself",
  hard_block_financial: "Draft touches money or financial direction",
  hard_block_legal: "Draft touches legal direction",
  hard_block_medical: "Draft touches medical direction",
  violence: "Contains violent language",
  self_harm: "Mentions self-harm",
  illegal: "Mentions illegal activity",
  adult: "Contains adult content",
  discrimination: "Contains discriminatory language",
};

/** Unique, readable reasons for a draft's flags (unknown categories fall back to a generic note). */
export function moderationReasons(flags?: ModerationFlag[] | null): string[] {
  if (!flags || flags.length === 0) return [];
  const reasons = new Set<string>();
  for (const flag of flags) {
    const category = flag?.category || "";
    reasons.add(LABELS[category] || "Flagged by safety checks");
  }
  return Array.from(reasons);
}
