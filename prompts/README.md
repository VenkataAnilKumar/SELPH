# SELPH — Replit Agent Prompts
# Buildathon: Replit 10 — May 2, 2026 (24hrs, 5am PT → 5am PT)
# Prompt versions: v2.0 (validated + fixed)

---

## Prompts

| # | File | Target | Priority |
|---|---|---|---|
| 1 | `01-landing-page.md` | `src/landing/` — full marketing site | HIGH — judges see this first |
| 2 | `02-dashboard-polish.md` | `src/web/` — v3.0 visual redesign | HIGH — demo wow factor |

---

## Fixes applied in v2.0

### Prompt 01 (Landing)
- Fixed: `lucide-react` install instruction added (was missing from package.json)
- Fixed: Google Fonts now uses `next/font/google` (not a raw `<link>` tag)
- Fixed: `fontFamily` added to `tailwind.config.js` so `font-display` / `font-body` work
- Fixed: `next.config.js` uses `output: 'export'` (`next export` deprecated in Next.js 15)
- Fixed: `"use client"` directive added to `page.tsx` (interactive elements require it)
- Fixed: Responsive grid classes added for all sections (sm: / md: / lg: breakpoints)
- Fixed: `border-top gradient` on bento cards — CSS cannot gradient a border directly;
         replaced with `::before` pseudo-element utility classes in `globals.css`
- Fixed: `card-enter` animation — `opacity: 0` initial state now set via `animate-card-enter`
         with Tailwind's `animation` config (fill-mode: forwards handled in keyframe)

### Prompt 02 (Dashboard)
- Fixed: `layout.tsx` updated to load Plus Jakarta Sans via `next/font/google`
- Fixed: `gradient-text`, `spin-ring`, `card-shadow` classes added to `globals.css`
- Fixed: Phase 10 Controls card layout bug — it was nested inside `<header>`;
         prompt now explicitly moves it to the main content area
- Fixed: Confidence badge colors — prompt now gives the exact JSX conditional expression
- Fixed: `tailwind.config.ts` updated with `fontFamily` CSS variable references
- Fixed: `conic-ring` spin uses a CSS class (`conic-ring` in globals.css) not Tailwind
         arbitrary values (conic-gradient not supported as Tailwind arbitrary syntax)

---

## How to use on May 2

1. Open Replit Agent in your SELPH project
2. Navigate to `src/landing/` working directory
3. Copy the full content of `01-landing-page.md` → paste into Replit Agent
4. After landing is done → navigate to `src/web/` working directory
5. Copy the full content of `02-dashboard-polish.md` → paste into Replit Agent

---

## Build order for May 2

```
Hour 1–3   → Run prompt 01 (landing page) in src/landing/
Hour 3–4   → Review + fix landing (check mobile, font rendering, blobs)
Hour 4–6   → Run prompt 02 (dashboard polish) in src/web/
Hour 6–7   → Review dashboard (check Phase 10 card position, gradients, spin ring)
Hour 7–8   → Deploy: landing → Vercel, backend → Railway
Hour 8+    → Record demo video, submit at buildathons.replit.app
```

---

## Submission checklist

- [ ] Landing page live (Vercel preview URL)
- [ ] Dashboard live (Vercel preview URL)
- [ ] Backend API responding on Railway
- [ ] Demo video: landing → signup → onboarding → approve a draft (< 60 sec)
- [ ] Registered + submitted at buildathons.replit.app
