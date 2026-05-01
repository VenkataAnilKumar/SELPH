# SELPH — Replit Agent Prompt: Dashboard UI Polish
# Target: src/web/
# Buildathon: Replit 10 — May 2, 2026
# Version: 2.0 (validated + fixed)

---

## Pre-flight checks (run before pasting prompt)

- Working directory: selph-ai/src/web/
- No new npm packages needed — everything uses Tailwind arbitrary values
- The existing dashboard logic is 100% correct — do NOT touch any function,
  state variable, useEffect, handler, or API call

---

## Known bug to fix

In the current dashboard/page.tsx, the Phase 10 Controls card (the large
card with buttons: "Refresh Phase 10 Snapshot", "Activate Crisis", etc.)
is incorrectly nested inside the <header> element, inside the right-side
flex div. This must be moved OUT of the header and placed as its own
card in the main content grid alongside the other cards. The card's
JSX and all its handlers are correct — just move its location.

---

## Prompt

You are restyling the SELPH dashboard at src/web/app/dashboard/page.tsx
to match the SELPH v3.0 design system. The page logic is complete and
correct — do NOT change any function, state, handler, useEffect, or API
call. Only update className values, fix the Phase 10 layout bug described
above, and update the three support files listed below.

Update these 4 files:
  1. src/web/app/layout.tsx          ← add Google Fonts
  2. src/web/app/globals.css         ← add design utilities + keyframes
  3. src/web/tailwind.config.ts      ← add SELPH color + font tokens
  4. src/web/app/dashboard/page.tsx  ← className-only redesign + Phase 10 fix

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 1 — src/web/app/layout.tsx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Replace the entire file with:

import type { Metadata } from 'next'
import { Plus_Jakarta_Sans, Inter } from 'next/font/google'
import { AuthProvider } from '@/lib/auth-context'
import './globals.css'

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '500', '600', '700', '800'],
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-body',
})

export const metadata: Metadata = {
  title: 'SELPH — Your Digital Twin',
  description: 'Your personal AI twin that acts on your behalf',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${plusJakarta.variable} ${inter.variable}`}>
      <body className="font-body antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  )
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 2 — src/web/app/globals.css
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Replace the entire file with:

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { scroll-behavior: smooth; }
  body {
    background-color: #FAFAF9;
    color: #334155;
    font-family: var(--font-body), -apple-system, sans-serif;
  }
}

@layer utilities {
  /* Gradient text — violet to sky */
  .gradient-text {
    background: linear-gradient(135deg, #7C3AED 0%, #0EA5E9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  /* Card shadows */
  .card-shadow {
    box-shadow: 0 4px 24px rgba(124, 58, 237, 0.08), 0 1px 4px rgba(0,0,0,0.04);
  }
  .card-shadow-lifted {
    box-shadow: 0 8px 40px rgba(124, 58, 237, 0.14), 0 2px 8px rgba(0,0,0,0.06);
  }

  /* Spinning conic identity ring */
  .conic-ring {
    background: conic-gradient(
      from 0deg,
      #7C3AED, #0EA5E9, #10B981, #F43F5E, #9333EA, #7C3AED
    );
    animation: spin-ring 8s linear infinite;
  }
}

/* Keyframes */
@keyframes spin-ring {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

@keyframes card-enter {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes ping-dot {
  0%   { transform: scale(1); opacity: 1; }
  75%, 100% { transform: scale(2); opacity: 0; }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 3 — src/web/tailwind.config.ts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Replace the entire file with:

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['var(--font-display)', 'system-ui', 'sans-serif'],
        body:    ['var(--font-body)',    'system-ui', 'sans-serif'],
      },
      colors: {
        selph: {
          violet:  '#7C3AED',
          purple:  '#9333EA',
          sky:     '#0EA5E9',
          coral:   '#F43F5E',
          orange:  '#F97316',
          emerald: '#10B981',
          amber:   '#F59E0B',
          warm:    '#FAFAF9',
          cloud:   '#F5F3FF',
          title:   '#0F172A',
          body:    '#334155',
          muted:   '#64748B',
          subtle:  '#94A3B8',
        },
        approve: '#10B981',
        edit:    '#F59E0B',
        reject:  '#EF4444',
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
    },
  },
  plugins: [],
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 4 — src/web/app/dashboard/page.tsx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Apply all className changes below. Keep every function, state variable,
handler, useEffect, and API call exactly as-is.

── PHASE 10 BUG FIX ──────────────────────────────────────────────────
The Phase 10 Controls card JSX is currently nested inside <header>.
Move it out: place it as the first card inside <main>, before the
twin profile grid. It becomes a full-width card:
  <section className="mb-8 bg-white rounded-3xl p-8 card-shadow
    border border-[rgba(124,58,237,0.08)]">
    [Phase 10 card contents — unchanged]
  </section>

── PAGE BACKGROUND ───────────────────────────────────────────────────
Replace: className="min-h-screen bg-gray-100"
With:    className="min-h-screen bg-[#FAFAF9]"

── HEADER BAR ────────────────────────────────────────────────────────
Replace: <header className="bg-white shadow">
With:    <header className="bg-white/90 backdrop-blur-sm sticky top-0 z-40
           border-b border-[rgba(124,58,237,0.08)]">

Inner wrapper — keep max-w-7xl, update:
  Replace: py-4 flex justify-between items-center
  With:    py-3 px-4 sm:px-6 lg:px-8 flex justify-between items-center

SELPH title:
  Replace: className="text-3xl font-bold text-gray-900"
  With:    className="text-2xl font-display font-extrabold gradient-text"

Subtitle "Your Digital Twin Dashboard":
  Replace: className="text-gray-600"
  With:    className="text-[#64748B] text-sm mt-0.5"

Right-side flex wrapper:
  Replace: className="flex items-center space-x-4"
  With:    className="flex items-center gap-3"

IDENTITY AVATAR — add before the user email div:
  Insert this JSX:
  <div className="conic-ring w-11 h-11 rounded-full p-[2.5px] flex-shrink-0">
    <div className="w-full h-full rounded-full bg-white flex items-center
      justify-center text-[#7C3AED] text-xs font-bold font-display">
      {user?.email?.slice(0, 2).toUpperCase() ?? 'ME'}
    </div>
  </div>

User email text:
  "Logged in as" label: className="text-xs text-[#94A3B8]"
  Email value: className="font-semibold text-[#0F172A] text-sm"

LOGOUT button:
  Replace: className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
  With:    className="px-4 py-2 bg-white border border-[rgba(239,68,68,0.40)]
             text-[#EF4444] rounded-xl text-sm font-semibold
             hover:bg-red-50 transition-colors"

── LOADING STATE ──────────────────────────────────────────────────────
Replace: className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"
With:    className="inline-block animate-spin rounded-full h-12 w-12
           border-b-2 border-[#7C3AED]"

Loading text:
  Replace: className="mt-4 text-gray-600"
  With:    className="mt-4 text-[#64748B]"

── FEEDBACK MESSAGES ─────────────────────────────────────────────────
Error (top-level):
  Replace: className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700"
  With:    className="p-4 rounded-2xl border border-[rgba(239,68,68,0.20)]
             bg-[rgba(239,68,68,0.06)] text-[#EF4444] font-medium"

Action success message:
  Replace: className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 text-green-700"
  With:    className="mb-6 rounded-2xl border border-[rgba(16,185,129,0.20)]
             bg-[rgba(16,185,129,0.06)] p-4 text-[#10B981] font-medium"

Action error message:
  Replace: className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700"
  With:    className="mb-6 rounded-2xl border border-[rgba(239,68,68,0.20)]
             bg-[rgba(239,68,68,0.06)] p-4 text-[#EF4444] font-medium"

── ALL CARD WRAPPERS ──────────────────────────────────────────────────
Replace all instances of:
  "bg-white rounded-lg shadow p-8"
With:
  "bg-white rounded-3xl p-8 card-shadow border border-[rgba(124,58,237,0.08)]"

Replace all instances of:
  "bg-white rounded-lg shadow p-8 md:col-span-2"
With:
  "bg-white rounded-3xl p-8 card-shadow border border-[rgba(124,58,237,0.08)] md:col-span-2"

── TWIN PROFILE CARD ─────────────────────────────────────────────────
H2 "Twin Profile":
  Replace: className="text-2xl font-bold text-gray-900 mb-6"
  With:    className="text-2xl font-display font-bold text-[#0F172A] mb-6"

Labels ("Twin ID", "Domain", "Tone", "Status"):
  Replace: className="text-sm text-gray-600"
  With:    className="text-[11px] uppercase tracking-wider font-semibold text-[#94A3B8]"

Values below labels:
  Replace: className="font-mono text-sm text-gray-900"  (Twin ID)
  With:    className="font-mono text-xs text-[#64748B] break-all"

  Replace: className="font-medium text-gray-900"  (Domain, Tone)
  With:    className="font-semibold text-[#0F172A] mt-0.5"

Status dot + text:
  Active dot:
    Replace: className="w-3 h-3 rounded-full bg-green-500"
    With:    className="relative w-3 h-3 flex-shrink-0"
             Add inside: two divs —
               <div className="absolute inset-0 rounded-full bg-[#10B981]" />
               <div className="absolute inset-0 rounded-full bg-[#10B981] opacity-75
                 animate-ping" style={{ animationDuration: '2s' }} />

  Paused dot:
    Replace: className="w-3 h-3 rounded-full bg-yellow-500"
    With:    className="w-3 h-3 rounded-full bg-[#F97316] flex-shrink-0"

  Status text:
    Replace: className="capitalize font-medium text-gray-900"
    With:    className={`capitalize font-semibold
               ${twin.status === 'active' ? 'text-[#10B981]' : 'text-[#F97316]'}`}

── APPROVAL LOOP / STATS CARD ────────────────────────────────────────
H2 "Approval Loop":
  Replace: className="text-2xl font-bold text-gray-900 mb-6"
  With:    className="text-2xl font-display font-bold text-[#0F172A] mb-6"

Stat cells — replace all:
  Replace: className="rounded-lg bg-slate-50 p-4"
  With:    className="rounded-xl bg-[#F5F3FF] border border-[rgba(124,58,237,0.08)] p-4"

Stat labels:
  Replace: className="text-sm text-gray-600"
  With:    className="text-[11px] uppercase tracking-wider text-[#94A3B8] font-semibold"

Stat numbers — apply per metric:
  "Pending Drafts":  className="mt-2 text-3xl font-bold text-[#7C3AED]"
  "Processed Drafts": className="mt-2 text-3xl font-bold text-[#0EA5E9]"
  "Messages Seen":   className="mt-2 text-3xl font-bold text-[#0F172A]"
  "Fallback Rate":   className="mt-2 text-3xl font-bold text-[#F97316]"

Approval Rate cell:
  Replace: className="rounded-lg bg-green-50 p-4 col-span-2"
  With:    className="rounded-xl bg-gradient-to-r
             from-[rgba(16,185,129,0.08)] to-[rgba(6,182,212,0.08)]
             border border-[rgba(16,185,129,0.15)] p-4 col-span-2"

  "Approval Rate" label:
    Replace: className="text-sm text-green-700 font-medium"
    With:    className="text-[11px] uppercase tracking-wider text-[#10B981] font-semibold"

  Number:
    Replace: className="mt-2 text-3xl font-bold text-green-800"
    With:    className="mt-2 text-3xl font-bold text-[#10B981]"

  Sub-label:
    Replace: className="mt-1 text-xs text-green-600"
    With:    className="mt-1 text-xs text-[#10B981] opacity-70"

── IDENTITY ONBOARDING SECTION ────────────────────────────────────────
Section wrapper:
  Replace: className="mt-8 rounded-lg bg-white p-8 shadow"
  With:    className="mt-8 rounded-3xl bg-gradient-to-br
             from-[rgba(124,58,237,0.04)] to-[rgba(14,165,233,0.04)]
             border border-[rgba(124,58,237,0.10)] p-8"

H2 "Identity Onboarding":
  Replace: className="text-2xl font-bold text-gray-900"
  With:    className="text-2xl font-display font-bold text-[#0F172A]"

Subtitle:
  Replace: className="mt-1 text-sm text-gray-600"
  With:    className="mt-1 text-sm text-[#64748B]"

All inputs in onboarding form:
  Replace: className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
  With:    className="rounded-xl border-2 border-[#E2E8F0] px-4 py-3 text-sm
             text-[#0F172A] placeholder:text-[#94A3B8]
             focus:border-[#7C3AED] focus:ring-4 focus:ring-[rgba(124,58,237,0.10)]
             outline-none transition-all"

All selects in onboarding form:
  Replace: className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
  With:    className="rounded-xl border-2 border-[#E2E8F0] px-4 py-3 text-sm
             text-[#0F172A] focus:border-[#7C3AED] focus:ring-4
             focus:ring-[rgba(124,58,237,0.10)] outline-none transition-all"

"Save Onboarding" button:
  Replace: className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
  With:    className="mt-4 bg-gradient-to-r from-[#7C3AED] to-[#0EA5E9]
             text-white rounded-xl px-6 py-3 text-sm font-semibold
             shadow-[0_4px_16px_rgba(124,58,237,0.30)]
             hover:-translate-y-0.5 hover:shadow-[0_8px_28px_rgba(124,58,237,0.40)]
             active:scale-[0.98] transition-all duration-150"

── CHANNEL CONNECTIONS SECTION ───────────────────────────────────────
H2 "Channel Connections":
  Replace: className="text-2xl font-bold text-gray-900"
  With:    className="text-2xl font-display font-bold text-[#0F172A]"

Channel row:
  Replace: className="flex items-center justify-between rounded-lg border border-gray-200 p-4"
  With:    className="flex items-center justify-between rounded-2xl
             border border-[rgba(124,58,237,0.08)] p-4
             hover:border-[rgba(124,58,237,0.20)] transition-colors"

Channel name:
  Replace: className="font-medium text-gray-900 capitalize"
  With:    className="font-semibold text-[#0F172A] capitalize"

Connected status text:
  Replace: className="text-xs text-gray-500"
  With:    className={`text-xs font-medium ${connected ? 'text-[#10B981]' : 'text-[#94A3B8]'}`}

Connect button:
  Replace: className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium text-white hover:bg-blue-700"
  With:    className="bg-gradient-to-r from-[#7C3AED] to-[#0EA5E9]
             text-white rounded-xl px-4 py-2 text-xs font-semibold
             shadow-[0_2px_8px_rgba(124,58,237,0.25)]
             hover:-translate-y-0.5 transition-all"

Disconnect button:
  Replace: className="rounded-lg bg-red-600 px-3 py-2 text-xs font-medium text-white hover:bg-red-700"
  With:    className="bg-white border border-[rgba(239,68,68,0.40)] text-[#EF4444]
             rounded-xl px-3 py-2 text-xs font-semibold
             hover:bg-red-50 transition-colors"

── SETTINGS CARD ──────────────────────────────────────────────────────
Both inputs (Domain, Tone):
  Replace: className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
  With:    className="w-full rounded-xl border-2 border-[#E2E8F0] px-4 py-3 text-sm
             text-[#0F172A] placeholder:text-[#94A3B8]
             focus:border-[#7C3AED] focus:ring-4 focus:ring-[rgba(124,58,237,0.10)]
             outline-none transition-all"

"Update Tone/Domain" button:
  Replace: className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
  With:    className="bg-gradient-to-r from-[#7C3AED] to-[#0EA5E9]
             text-white rounded-xl px-5 py-2.5 text-sm font-semibold
             shadow-[0_4px_16px_rgba(124,58,237,0.25)]
             hover:-translate-y-0.5 transition-all duration-150"

Pause Twin button:
  Replace: className containing "bg-amber-600 hover:bg-amber-700"
  With:    className="bg-gradient-to-r from-[#F59E0B] to-[#F97316]
             text-white rounded-xl px-4 py-2.5 text-sm font-semibold
             hover:-translate-y-0.5 transition-all duration-150"

Resume Twin button:
  Replace: className containing "bg-emerald-600 hover:bg-emerald-700"
  With:    className="bg-gradient-to-r from-[#10B981] to-[#06B6D4]
             text-white rounded-xl px-4 py-2.5 text-sm font-semibold
             hover:-translate-y-0.5 transition-all duration-150"

── PENDING DRAFTS SECTION ─────────────────────────────────────────────
H2 "Pending Drafts":
  Replace: className="text-2xl font-bold text-gray-900"
  With:    className="text-2xl font-display font-bold text-[#0F172A]"

Subtitle:
  Replace: className="mt-1 text-sm text-gray-600"
  With:    className="mt-1 text-sm text-[#64748B]"

Count badge:
  Replace: className="rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700"
  With:    className="rounded-full bg-[rgba(124,58,237,0.08)] px-4 py-1.5
             text-sm font-semibold text-[#7C3AED]"

Empty state:
  Replace: className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-8 text-center text-gray-600"
  With:    className="rounded-2xl border border-dashed border-[rgba(124,58,237,0.20)]
             bg-gradient-to-br from-[rgba(124,58,237,0.02)] to-[rgba(14,165,233,0.02)]
             p-10 text-center text-[#94A3B8] text-sm"

Draft article card:
  Replace: className="rounded-xl border border-gray-200 p-6"
  With:    className="rounded-2xl border border-[rgba(124,58,237,0.08)] p-6
             card-shadow border-l-4 border-l-[#7C3AED]
             hover:-translate-y-0.5 transition-all duration-200"

CONFIDENCE BADGE — replace the static className with a dynamic expression:
  Replace the span with className="rounded-full bg-blue-50 px-3 py-1..."
  With this JSX:
  <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide
    ${draft.confidence_label === 'high'
      ? 'bg-[rgba(16,185,129,0.10)] text-[#10B981]'
      : draft.confidence_label === 'medium'
      ? 'bg-[rgba(245,158,11,0.10)] text-[#F59E0B]'
      : 'bg-[rgba(239,68,68,0.10)] text-[#EF4444]'
    }`}>
    {draft.confidence_label} confidence
  </span>

Generation source badge:
  Replace: className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
  With:    className="rounded-full bg-[rgba(14,165,233,0.08)] text-[#0EA5E9]
             px-3 py-1 text-xs font-medium"

Draft content text:
  Replace: className="mt-4 whitespace-pre-wrap text-gray-900"
  With:    className="mt-4 whitespace-pre-wrap text-[#0F172A] leading-relaxed text-sm"

Stats grid inside draft (confidence score, tokens, cost, fallback):
  Replace: className="mt-4 grid gap-3 text-sm text-gray-600 sm:grid-cols-2"
  With:    className="mt-4 grid gap-3 text-xs text-[#64748B] sm:grid-cols-2"

Confidence reasoning text:
  Replace: className="mt-3 text-sm text-gray-600"
  With:    className="mt-3 text-xs text-[#64748B] italic"

Edit textarea area:
  Replace: className="mt-4 rounded-lg bg-gray-50 p-4"
  With:    className="mt-4 rounded-2xl bg-[#FAFAF9] border border-[rgba(124,58,237,0.08)] p-4"

  Edit label:
    Replace: className="mb-2 block text-sm font-medium text-gray-900"
    With:    className="mb-2 block text-sm font-semibold text-[#0F172A]"

  Textarea:
    Replace: className="min-h-32 w-full rounded-lg border border-gray-300 p-3 text-sm text-gray-900 outline-none focus:border-blue-500"
    With:    className="min-h-32 w-full rounded-xl border-2 border-[#E2E8F0] p-3
               text-sm text-[#0F172A] outline-none
               focus:border-[#7C3AED] focus:ring-4 focus:ring-[rgba(124,58,237,0.10)]
               transition-all"

DRAFT ACTION BUTTONS:

  Approve:
    Replace: className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-green-300"
    With:    className="bg-gradient-to-r from-[#10B981] to-[#06B6D4]
               text-white rounded-xl px-5 py-2.5 text-sm font-bold
               shadow-[0_4px_16px_rgba(16,185,129,0.30)]
               hover:shadow-[0_8px_28px_rgba(16,185,129,0.45)] hover:-translate-y-0.5
               active:scale-[0.96] transition-all duration-150
               disabled:opacity-50 disabled:cursor-not-allowed disabled:translate-y-0 disabled:shadow-none"

  Edit:
    Replace: className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
    With:    className="bg-gradient-to-r from-[#F59E0B] to-[#F97316]
               text-white rounded-xl px-5 py-2.5 text-sm font-bold
               hover:-translate-y-0.5 active:scale-[0.96] transition-all duration-150
               disabled:opacity-50 disabled:cursor-not-allowed"

  Reject:
    Replace: className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:cursor-not-allowed disabled:bg-rose-300"
    With:    className="bg-white border-2 border-[#EF4444] text-[#EF4444]
               rounded-xl px-5 py-2.5 text-sm font-bold
               hover:bg-red-50 active:scale-[0.96] transition-all duration-150
               disabled:opacity-50 disabled:cursor-not-allowed"

  Skip:
    Replace: className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-900 hover:bg-gray-300 disabled:cursor-not-allowed disabled:bg-gray-100"
    With:    className="bg-white border border-[#E2E8F0] text-[#64748B]
               rounded-xl px-5 py-2.5 text-sm font-medium
               hover:bg-[#F8F9FA] active:scale-[0.96] transition-all duration-150
               disabled:opacity-50 disabled:cursor-not-allowed"

  Save Edit button:
    Replace: className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
    With:    className="bg-gradient-to-r from-[#7C3AED] to-[#0EA5E9]
               text-white rounded-xl px-5 py-2.5 text-sm font-semibold
               hover:-translate-y-0.5 active:scale-[0.98] transition-all duration-150
               disabled:opacity-50 disabled:cursor-not-allowed"

  Cancel button:
    Replace: className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-gray-700 ring-1 ring-gray-300 hover:bg-gray-50"
    With:    className="bg-white border border-[#E2E8F0] text-[#64748B]
               rounded-xl px-4 py-2.5 text-sm font-medium
               hover:bg-[#F8F9FA] transition-colors"

── MODEL SIGNALS SIDEBAR ──────────────────────────────────────────────
H2 "Model Signals":
  Replace: className="text-2xl font-bold text-gray-900"
  With:    className="text-2xl font-display font-bold text-[#0F172A]"

Section sub-headers (Generation Sources, Models, Fallback Reasons):
  Replace: className="font-semibold text-gray-900"
  With:    className="font-semibold text-[#0F172A] text-sm
             border-l-2 border-[#7C3AED] pl-3"

Row labels (source/model names):
  Replace: (inline span text-gray-700)
  With:    className="text-[#334155] text-sm"

Count values:
  Replace: className="font-medium text-gray-900"
  With:    className="font-bold text-[#7C3AED] text-sm"

"No fallbacks recorded":
  Replace: className="text-gray-500"
  With:    className="text-[#94A3B8] text-sm italic"

Estimated spend card:
  Replace: className="rounded-lg bg-gray-50 p-4"
  With:    className="rounded-2xl bg-gradient-to-br
             from-[rgba(124,58,237,0.06)] to-[rgba(14,165,233,0.06)]
             border border-[rgba(124,58,237,0.10)] p-4"

  "Estimated spend" label:
    Replace: className="text-sm text-gray-600"
    With:    className="text-[11px] uppercase tracking-wider text-[#94A3B8] font-semibold"

  Dollar amount:
    Replace: className="mt-2 text-2xl font-bold text-gray-900"
    With:    className="mt-2 text-2xl font-display font-bold text-[#0F172A]"

  Token count:
    Replace: className="mt-1 text-sm text-gray-600"
    With:    className="mt-1 text-xs text-[#64748B]"

── PHASE 10 CONTROLS CARD ─────────────────────────────────────────────
(After being moved out of header per the bug fix above)

H2 "Phase 10 Controls":
  Replace: className="text-2xl font-bold text-gray-900 mb-2"
  With:    className="text-2xl font-display font-bold text-[#0F172A] mb-2"

Subtitle:
  Replace: className="text-sm text-gray-600 mb-6"
  With:    className="text-sm text-[#64748B] mb-6"

Refresh Snapshot button:
  Replace: className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
  With:    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#7C3AED] to-[#0EA5E9]
             text-white font-semibold text-sm
             shadow-[0_4px_16px_rgba(124,58,237,0.25)]
             hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:translate-y-0"

Activate Crisis button:
  Replace: className="px-4 py-2 rounded-lg bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-60"
  With:    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#F59E0B] to-[#F97316]
             text-white font-semibold text-sm
             hover:-translate-y-0.5 transition-all disabled:opacity-50"

Manual Pause button:
  Replace: className="px-4 py-2 rounded-lg bg-orange-700 text-white hover:bg-orange-800 disabled:opacity-60"
  With:    className="px-5 py-2.5 rounded-xl bg-[#F97316] text-white font-semibold text-sm
             hover:bg-[#EA6C00] transition-colors disabled:opacity-50"

Resolve Crisis button:
  Replace: className="px-4 py-2 rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 disabled:opacity-60"
  With:    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#10B981] to-[#06B6D4]
             text-white font-semibold text-sm
             hover:-translate-y-0.5 transition-all disabled:opacity-50"

Toggle Privacy Mode button:
  Replace: className="px-4 py-2 rounded-lg bg-slate-700 text-white hover:bg-slate-800 disabled:opacity-60"
  With:    className="px-5 py-2.5 rounded-xl bg-[#0F172A] text-white font-semibold text-sm
             hover:bg-[#1E293B] transition-colors disabled:opacity-50"

Info tiles (Privacy Mode, Twin Certificate, Proactive Suggestions):
  Replace: className="rounded-lg border border-gray-200 p-4"
  With:    className="rounded-2xl bg-[#FAFAF9] border border-[rgba(124,58,237,0.08)] p-4"

  Labels ("Privacy Mode", "Twin Certificate", "Proactive Suggestions"):
    Replace: className="text-xs uppercase text-gray-500"
    With:    className="text-[11px] uppercase tracking-wider text-[#94A3B8] font-semibold"

  Values:
    Replace: className="text-lg font-semibold text-gray-900"
    With:    className="text-lg font-display font-semibold text-[#0F172A] mt-1"

    Certificate ID (mono):
    Replace: className="text-sm font-mono text-gray-900 break-all"
    With:    className="text-xs font-mono text-[#64748B] break-all mt-1"

── GETTING STARTED CARD ───────────────────────────────────────────────
Card wrapper:
  Replace: className="mt-12 bg-white rounded-lg shadow p-8"
  With:    className="mt-8 bg-gradient-to-br from-[rgba(124,58,237,0.03)]
             to-[rgba(14,165,233,0.03)] rounded-3xl border
             border-[rgba(124,58,237,0.08)] p-8"

H2 "Getting Started":
  Replace: className="text-2xl font-bold text-gray-900 mb-6"
  With:    className="text-2xl font-display font-bold text-[#0F172A] mb-6"

Step icon circles:
  Replace: className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white mb-4"
  With (per step):
    Step 1 Connect:   className="flex items-center justify-center h-12 w-12 rounded-2xl
                        bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9] text-white mb-4
                        shadow-[0_4px_12px_rgba(124,58,237,0.30)]"
    Step 2 Customize: className="flex items-center justify-center h-12 w-12 rounded-2xl
                        bg-gradient-to-br from-[#10B981] to-[#06B6D4] text-white mb-4
                        shadow-[0_4px_12px_rgba(16,185,129,0.30)]"
    Step 3 Review:    className="flex items-center justify-center h-12 w-12 rounded-2xl
                        bg-gradient-to-br from-[#9333EA] to-[#EC4899] text-white mb-4
                        shadow-[0_4px_12px_rgba(147,51,234,0.30)]"

Step titles:
  Replace: className="font-medium text-gray-900"
  With:    className="font-display font-semibold text-[#0F172A]"

Step descriptions:
  Replace: className="mt-2 text-sm text-gray-600"
  With:    className="mt-2 text-sm text-[#64748B] leading-relaxed"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULES — DO NOT VIOLATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Do NOT modify any function, handler, useEffect, or API call
2. Do NOT add or remove any state variables
3. Do NOT add new features or components
4. Do NOT install any new packages
5. Only className values, the Phase 10 layout fix, and the 3
   support files (layout.tsx, globals.css, tailwind.config.ts) may change
6. The "use client" directive must remain as the first line
7. All focus states must remain keyboard accessible
