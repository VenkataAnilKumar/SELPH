# SELPH — Replit Agent Prompt: Landing Page
# Target: src/landing/
# Buildathon: Replit 10 — May 2, 2026
# Version: 2.0 (validated + fixed)

---

## Pre-flight checks (run before pasting prompt)

- Working directory must be: selph-ai/src/landing/
- Run `npm install` after Agent finishes to install lucide-react

---

## Prompt

You are building the SELPH marketing landing page inside src/landing/.
This is a standalone Next.js 15 App Router project. The package.json
already exists with next, react, tailwindcss, and typescript.

FIRST — install one additional package:
  npm install lucide-react

Then create all files listed below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILES TO CREATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. next.config.js
2. postcss.config.js
3. tailwind.config.js
4. tsconfig.json
5. app/layout.tsx
6. app/globals.css
7. app/page.tsx

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 1 — next.config.js
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
}
module.exports = nextConfig

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 2 — postcss.config.js
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

module.exports = {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 3 — tailwind.config.js
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        selph: {
          violet:  '#7C3AED',
          purple:  '#9333EA',
          sky:     '#0EA5E9',
          coral:   '#F43F5E',
          orange:  '#F97316',
          emerald: '#10B981',
          warm:    '#FAFAF9',
          cloud:   '#F5F3FF',
          mist:    '#F0F9FF',
          title:   '#0F172A',
          body:    '#334155',
          muted:   '#64748B',
          subtle:  '#94A3B8',
        },
      },
      animation: {
        'blob-float':  'blob-float 12s ease-in-out infinite',
        'blob-float2': 'blob-float 14s ease-in-out 2s infinite',
        'blob-float3': 'blob-float 16s ease-in-out 4s infinite',
        'card-enter':  'card-enter 0.6s ease-out 0.3s forwards',
        'spin-slow':   'spin 8s linear infinite',
        'pulse-ring':  'pulse-ring 2s ease-out infinite',
      },
      keyframes: {
        'blob-float': {
          '0%, 100%': { transform: 'translate(0, 0) scale(1)' },
          '33%':      { transform: 'translate(20px, -20px) scale(1.05)' },
          '66%':      { transform: 'translate(-15px, 15px) scale(0.97)' },
        },
        'card-enter': {
          from: { opacity: '0', transform: 'translateY(20px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-ring': {
          '0%':   { transform: 'scale(1)', opacity: '1' },
          '100%': { transform: 'scale(1.8)', opacity: '0' },
        },
      },
    },
  },
  plugins: [],
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 4 — tsconfig.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 5 — app/layout.tsx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use next/font/google to load fonts. Exact code:

import type { Metadata } from 'next'
import { Plus_Jakarta_Sans, Inter } from 'next/font/google'
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
  title: 'SELPH — Your Digital Twin AI',
  description:
    'SELPH learns who you are — your voice, expertise, and style — then acts on your behalf across every platform, 24/7.',
  openGraph: {
    title: 'SELPH — Your Digital Twin AI',
    description: 'Your second self, always available.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${plusJakarta.variable} ${inter.variable}`}>
      <body className="font-body antialiased">{children}</body>
    </html>
  )
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE 6 — app/globals.css
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --font-display: 'Plus Jakarta Sans', system-ui, sans-serif;
    --font-body: 'Inter', system-ui, sans-serif;
  }
  html { scroll-behavior: smooth; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
}

@layer utilities {
  .gradient-text {
    background: linear-gradient(135deg, #7C3AED 0%, #0EA5E9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .gradient-text-energy {
    background: linear-gradient(135deg, #F43F5E 0%, #F97316 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .btn-primary {
    background: linear-gradient(135deg, #7C3AED 0%, #0EA5E9 100%);
    box-shadow: 0 4px 16px rgba(124, 58, 237, 0.30);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(124, 58, 237, 0.40);
  }
  .btn-primary:active { transform: scale(0.98); }

  .card-shadow {
    box-shadow: 0 4px 24px rgba(124, 58, 237, 0.08), 0 1px 4px rgba(0,0,0,0.04);
  }
  .card-shadow-lifted {
    box-shadow: 0 8px 40px rgba(124, 58, 237, 0.14), 0 2px 8px rgba(0,0,0,0.06);
  }
  .card-shadow-float {
    box-shadow: 0 16px 64px rgba(124, 58, 237, 0.20), 0 4px 16px rgba(0,0,0,0.08);
  }

  /* Bento card top-accent: use background-image trick since CSS border
     cannot render gradients directly */
  .border-top-gradient-violet {
    position: relative;
  }
  .border-top-gradient-violet::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 24px 24px 0 0;
    background: linear-gradient(135deg, #7C3AED 0%, #0EA5E9 100%);
  }
  .border-top-gradient-coral::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 24px 24px 0 0;
    background: linear-gradient(135deg, #F43F5E 0%, #F97316 100%);
  }
  .border-top-gradient-purple::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 24px 24px 0 0;
    background: linear-gradient(135deg, #9333EA 0%, #EC4899 100%);
  }
  .border-top-gradient-emerald::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 24px 24px 0 0;
    background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  }
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
FILE 7 — app/page.tsx
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"use client"

All sections in one file. Import at top:
  import { Mic, User, Sparkles, BarChart3, Inbox, Zap, Shield, Check,
           ArrowRight, Play, Menu, X } from 'lucide-react'
  import { useState } from 'react'

Structure the page as:
  <main>
    <Navbar />        ← sticky, z-50
    <HeroSection />
    <IdentitySection />
    <HowItWorksSection />
    <BentoSection />
    <PricingSection />
    <CtaSection />
    <Footer />
  </main>

Use React functional components (not separate files — all in page.tsx).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NAVBAR COMPONENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

State: const [mobileOpen, setMobileOpen] = useState(false)

Outer: <nav> sticky top-0 z-50 bg-white/90 backdrop-blur-sm
        border-b border-[rgba(124,58,237,0.08)]

Inner: max-w-7xl mx-auto px-6 h-16 flex items-center justify-between

Left — Logo:
  <span className="font-display font-extrabold text-xl gradient-text">SELPH</span>

Center — Desktop links (hidden on mobile: hidden md:flex gap-8):
  href="#features", href="#how-it-works", href="#pricing"
  className="text-[#64748B] text-sm font-medium hover:text-[#7C3AED] transition-colors"

Right — Desktop CTA (hidden md:flex gap-3 items-center):
  Login: text button, text-[#7C3AED] text-sm font-semibold hover:opacity-80
  Get Started: <button className="btn-primary text-white text-sm font-semibold
                px-5 py-2.5 rounded-xl">Get Started →</button>

Mobile — Hamburger (md:hidden):
  <button onClick={() => setMobileOpen(!mobileOpen)}>
    {mobileOpen ? <X size={24} /> : <Menu size={24} />}
  </button>

Mobile menu (mobileOpen && ...):
  absolute top-16 left-0 right-0 bg-white border-b border-[rgba(124,58,237,0.08)]
  px-6 py-4 flex flex-col gap-4 md:hidden
  Links + CTA buttons stacked vertically

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HERO SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<section> bg-white min-h-screen overflow-hidden relative pt-16

BLOBS — all position: absolute, pointer-events: none, rounded-full, z-0:
  Blob 1: w-[600px] h-[600px] top-[-100px] right-[-200px]
    bg-[rgba(124,58,237,0.12)] blur-[80px] animate-blob-float
  Blob 2: w-[400px] h-[400px] bottom-[0px] left-[-150px]
    bg-[rgba(14,165,233,0.10)] blur-[60px] animate-blob-float2
  Blob 3: w-[300px] h-[300px] top-[40%] right-[10%]
    bg-[rgba(244,63,94,0.08)] blur-[60px] animate-blob-float3

CONTENT wrapper: relative z-10 max-w-4xl mx-auto px-6
  pt-24 pb-16 flex flex-col items-center text-center

Tag chip:
  <span> inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-[13px]
    font-semibold text-[#7C3AED]
    bg-[rgba(124,58,237,0.08)] border border-[rgba(124,58,237,0.20)]
    mb-6
  "✦ Your Digital Self"

H1: text-5xl md:text-7xl font-display font-extrabold text-[#0F172A]
    leading-[1.1] tracking-tight mt-0 mb-6
  <span>"Your second self,"</span><br/>
  <span className="gradient-text">"always available."</span>

Subheadline: text-lg md:text-xl text-[#64748B] max-w-2xl leading-relaxed mb-10
  "SELPH learns who you are — your voice, expertise, and style —
   then acts on your behalf across every platform, 24/7."

CTA row: flex flex-col sm:flex-row gap-4 justify-center mb-10
  [Get Started Free]: <button className="btn-primary text-white font-semibold
    px-8 py-4 rounded-xl text-base">Get Started Free</button>

  [Watch Demo]: <button className="flex items-center gap-2 px-8 py-4 rounded-xl
    text-base font-semibold text-[#7C3AED] bg-white
    border-2 border-[#7C3AED] hover:bg-[rgba(124,58,237,0.04)]
    transition-colors">
    <Play size={18} fill="currentColor" /> Watch Demo
  </button>

Social proof: flex items-center gap-3 justify-center
  Avatar stack (5 circles, -space-x-2, each 36px rounded-full, different gradients):
    Bg gradients: violet→sky, coral→orange, emerald→sky, purple→pink, orange→coral
    Show 2-letter initials in white, text-xs font-bold
  Text: text-sm text-[#94A3B8] ml-2 "50,000+ creators trust SELPH"

TWIN PREVIEW CARD:
  mt-16 max-w-md w-full mx-auto
  bg-white rounded-3xl p-6 card-shadow-float
  border border-[rgba(124,58,237,0.10)]
  opacity-0 animate-card-enter  ← opacity-0 is initial state; animation fills to opacity-1

  Top row: flex items-center justify-between mb-4
    Left: flex items-center gap-2
      Pulsing dot: relative w-2.5 h-2.5
        Inner: absolute inset-0 rounded-full bg-[#10B981]
        Ping: absolute inset-0 rounded-full bg-[#10B981] animate-ping opacity-75
      "SELPH Twin" text-sm font-semibold text-[#0F172A]
    Right: "Online" pill — px-2.5 py-0.5 rounded-full text-xs font-semibold
      bg-[rgba(16,185,129,0.10)] text-[#10B981]

  Divider: h-px bg-[#F1F5F9] my-4

  Label: text-[11px] uppercase tracking-widest text-[#94A3B8] font-semibold mb-2
    "Incoming message"
  Message bubble: bg-[#F8F9FA] rounded-xl p-3 text-sm text-[#334155]
    "Can you review my proposal before Thursday?"

  Divider: h-px bg-[#F1F5F9] my-3

  "Draft ready · 2 min ago" — text-xs text-[#94A3B8]

  Action row: flex gap-2 mt-3
    [✓ Approve]: px-4 py-2 rounded-lg text-xs font-bold text-white
      bg-gradient-to-r from-[#10B981] to-[#06B6D4]
      shadow-[0_2px_8px_rgba(16,185,129,0.30)]
    [✎ Edit]: px-4 py-2 rounded-lg text-xs font-bold text-white
      bg-gradient-to-r from-[#F59E0B] to-[#F97316]
    [✕ Skip]: px-4 py-2 rounded-lg text-xs font-semibold text-[#64748B]
      bg-white border border-[#E2E8F0] hover:bg-[#F8F9FA] transition-colors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IDENTITY LAYERS SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<section id="features"> bg-[#F5F3FF] py-24 px-6

Header: max-w-3xl mx-auto text-center mb-16
  Label: text-[11px] uppercase tracking-[0.12em] font-semibold text-[#7C3AED] mb-3
    "WHAT SELPH CAPTURES"
  H2: text-4xl md:text-5xl font-display font-bold text-[#0F172A] mb-4
    "Every layer of who you are"
  Sub: text-lg text-[#64748B]
    "Voice, appearance, knowledge, and style — fully captured."

4 cards: max-w-6xl mx-auto
  grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6

Each card: bg-white rounded-3xl p-8 card-shadow
  border border-[rgba(124,58,237,0.08)]
  hover:-translate-y-1 hover:card-shadow-lifted transition-all duration-200

  Icon wrapper: w-[72px] h-[72px] rounded-[20px] flex items-center
    justify-center mb-5 mx-auto  ← gradient background per card
    Icon (Lucide, size=32, color="white") centered

  Title: text-lg font-display font-semibold text-[#0F172A] text-center mb-2
  Body: text-sm text-[#64748B] text-center leading-relaxed

Card 1 — Voice Clone:
  Icon bg: bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9]
  Icon: <Mic />
  Title: "Voice Clone"
  Body: "Your tone, accent, and speech pattern — captured and replicated perfectly."

Card 2 — Avatar Twin:
  Icon bg: bg-gradient-to-br from-[#F43F5E] to-[#F97316]
  Icon: <User />
  Title: "Avatar Twin"
  Body: "A video avatar that looks and sounds exactly like you for any screen."

Card 3 — Mind Clone:
  Icon bg: bg-gradient-to-br from-[#9333EA] to-[#EC4899]
  Icon: <Sparkles />
  Title: "Mind Clone"
  Body: "Your knowledge, opinions, and expertise embedded in every response."

Card 4 — Smart Analytics:
  Icon bg: bg-gradient-to-br from-[#10B981] to-[#0EA5E9]
  Icon: <BarChart3 />
  Title: "Smart Analytics"
  Body: "See how your twin performs, learns, and improves over time."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HOW IT WORKS SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<section id="how-it-works"> bg-white py-24 px-6

Header: same label/H2 pattern, centered, mb-16
  Label: "HOW IT WORKS"
  H2: "From zero to digital twin in minutes"
  Sub: "Three simple steps to your always-on AI self."

Steps: max-w-4xl mx-auto
  Wrapper: relative grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-4

  Connector line (desktop only, md:block hidden):
    absolute top-8 left-[calc(16.67%+32px)] right-[calc(16.67%+32px)] h-px
    bg-[rgba(124,58,237,0.15)] border-dashed
    (use border-t-2 border-dashed border-[rgba(124,58,237,0.20)] instead of bg)

  Each step: flex flex-col items-center text-center

    Circle: w-16 h-16 rounded-full flex items-center justify-center
      text-white text-2xl font-display font-bold
      Gradient per step:
        Step 1: bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9]
                shadow-[0_4px_16px_rgba(124,58,237,0.35)]
        Step 2: bg-gradient-to-br from-[#F43F5E] to-[#F97316]
                shadow-[0_4px_16px_rgba(244,63,94,0.35)]
        Step 3: bg-gradient-to-br from-[#10B981] to-[#0EA5E9]
                shadow-[0_4px_16px_rgba(16,185,129,0.35)]

    Title: text-lg font-display font-semibold text-[#0F172A] mt-6 mb-2
    Body: text-sm text-[#64748B] leading-relaxed max-w-[220px]

  Step 1: "1" / "Connect your world"
    "Link Instagram, Gmail, and your data sources in one click."

  Step 2: "2" / "SELPH learns your voice"
    "The twin engine analyzes your style, tone, and full knowledge base."

  Step 3: "3" / "Approve in one tap"
    "Review drafts and approve instantly. You stay in full control, always."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FEATURES BENTO GRID SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<section> bg-[#FAFAF9] py-24 px-6

Header: same pattern, centered, mb-16
  Label: "FEATURES"
  H2: "Everything your twin needs"
  Sub: "Built for creators who can't afford to go offline."

Bento grid: max-w-6xl mx-auto
  grid grid-cols-1 md:grid-cols-3 gap-4

IMPORTANT: Use the CSS pseudo-element classes for top gradient accents
  (border-top-gradient-violet etc.) defined in globals.css.
  Add overflow-hidden and rounded-3xl to each card.

Card A — Twin Feed (md:col-span-2):
  bg-gradient-to-br from-[rgba(124,58,237,0.05)] to-[rgba(14,165,233,0.05)]
  border border-[rgba(124,58,237,0.10)] rounded-3xl p-8 relative overflow-hidden
  hover:-translate-y-1 transition-all duration-200
  Icon circle: bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9] w-14 h-14
    rounded-2xl flex items-center justify-center
    <Inbox size={28} color="white" />
  Title: text-xl font-display font-semibold text-[#0F172A] mt-4 mb-2
    "Twin Feed"
  Body: text-sm text-[#64748B] leading-relaxed mb-4
    "Every incoming message and twin response in real time.
     Approve, edit, or reject with one click."
  Mini preview (mt-4 space-y-2):
    2 cards, each: bg-white rounded-xl p-3 flex items-center gap-3
      border-l-4 (card1: border-[#7C3AED], card2: border-[#F43F5E])
      dot (8px circle, matching border color) + text-xs text-[#64748B]
        "Sarah Kim · Instagram DM"  and  "Mark Lee · Gmail"

Card B — Voice Clone (md:col-span-1):
  bg-white border-top-gradient-violet rounded-3xl p-6 card-shadow
  hover:-translate-y-1 transition-all duration-200 relative overflow-hidden
  Icon: bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9] w-12 h-12 rounded-xl
    <Mic size={24} color="white" />
  Title: text-base font-display font-semibold text-[#0F172A] mt-4 mb-1 "Voice Clone"
  Body: text-sm text-[#64748B] "Clone your voice for audio and video responses."

Card C — Avatar Twin (md:col-span-1):
  bg-white border-top-gradient-coral rounded-3xl p-6 card-shadow
  hover:-translate-y-1 transition-all duration-200 relative overflow-hidden
  Icon: bg-gradient-to-br from-[#F43F5E] to-[#F97316] w-12 h-12 rounded-xl
    <User size={24} color="white" />
  Title: "Avatar Twin"
  Body: "Your face and expressions — rendered on demand."

Card D — Smart Reply (md:col-span-1):
  bg-white border-top-gradient-purple rounded-3xl p-6 card-shadow
  hover:-translate-y-1 transition-all duration-200 relative overflow-hidden
  Icon: bg-gradient-to-br from-[#9333EA] to-[#EC4899] w-12 h-12 rounded-xl
    <Zap size={24} color="white" />
  Title: "Smart Reply"
  Body: "Context-aware replies drafted in your exact voice."

Card E — 24/7 Active (md:col-span-2):
  bg-white rounded-3xl p-8 card-shadow
  hover:-translate-y-1 transition-all duration-200
  Title: text-xl font-display font-semibold text-[#0F172A] mb-2 "Always on, never tired"
  Body: text-sm text-[#64748B] mb-6
    "Your twin works across all channels while you sleep."
  Uptime visual: flex gap-1 items-end
    24 small bars (div each): w-2 rounded-full
      Height: random between h-2 and h-8 (hardcode varied heights)
      Color: alternate between bg-[#7C3AED]/60 and bg-[#0EA5E9]/60
      Last 3: full opacity (h-8 bg-[#10B981])

Card F — Privacy First (md:col-span-1):
  bg-gradient-to-br from-[rgba(16,185,129,0.06)] to-[rgba(6,182,212,0.06)]
  border border-[rgba(16,185,129,0.15)] rounded-3xl p-6
  hover:-translate-y-1 transition-all duration-200
  Icon: bg-gradient-to-br from-[#10B981] to-[#06B6D4] w-12 h-12 rounded-xl
    <Shield size={24} color="white" />
  Title: text-base font-display font-semibold text-[#0F172A] mt-4 mb-1 "Private by design"
  Body: text-sm text-[#64748B] "On-device mode available. Your data, your rules."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRICING SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<section id="pricing"> bg-white py-24 px-6

Header: same pattern, mb-16
  Label: "PRICING"
  H2: "Simple, transparent pricing"
  Sub: "Start free. Upgrade when you're ready."

Grid: max-w-5xl mx-auto
  grid grid-cols-1 md:grid-cols-3 gap-6 items-center

CARD 1 — Free:
  bg-white border-2 border-[#E2E8F0] rounded-3xl p-8
  Badge: inline-block px-3 py-1 rounded-full text-xs font-semibold
    bg-[#F1F5F9] text-[#64748B] mb-4 "Free forever"
  Price row: flex items-end gap-1 mb-6
    "$0" text-5xl font-display font-bold text-[#0F172A]
    "/month" text-lg text-[#64748B] mb-1
  Divider: h-px bg-[#F1F5F9] mb-6
  Features list (space-y-3):
    Each item: flex items-center gap-3
      <Check size={18} className="text-[#10B981] flex-shrink-0" />
      text-sm text-[#334155]
    Items: "1 channel connection", "50 AI drafts / month",
           "Basic identity setup", "Web dashboard"
  CTA (mt-8): w-full py-3 rounded-xl text-sm font-semibold
    bg-white border-2 border-[#7C3AED] text-[#7C3AED]
    hover:bg-[rgba(124,58,237,0.04)] transition-colors "Get Started"

CARD 2 — Pro (FEATURED):
  bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9] rounded-3xl p-8
  shadow-[0_16px_64px_rgba(124,58,237,0.35)]
  md:scale-105 md:z-10
  Badge: inline-block px-3 py-1 rounded-full text-xs font-semibold
    bg-[rgba(255,255,255,0.20)] text-white mb-4 "Most Popular"
  Price row: "$29" text-5xl font-display font-bold text-white
    "/month" text-lg text-white/75 mb-1
  Divider: h-px bg-white/20 mb-6
  Features list (text-white):
    <Check size={18} className="text-white flex-shrink-0" />
    Items: "Everything in Free", "Unlimited AI drafts",
           "Voice clone", "Avatar twin",
           "All channel integrations", "Priority support"
  CTA (mt-8): w-full py-3 rounded-xl text-sm font-semibold
    bg-white text-[#7C3AED] hover:bg-white/90 transition-colors
    "Get Started →"

CARD 3 — Creator:
  bg-white border-2 border-[rgba(244,63,94,0.30)] rounded-3xl p-8
  Badge: inline-block px-3 py-1 rounded-full text-xs font-semibold
    bg-[rgba(244,63,94,0.08)] text-[#F43F5E] mb-4 "For agencies"
  Price: "$99" + "/month"
  Divider: h-px bg-[#F1F5F9] mb-6
  Features (<Check> in text-[#F43F5E]):
    Items: "Everything in Pro", "5 twin profiles", "Team workspace",
           "API access", "Custom integrations", "Dedicated support"
  CTA: w-full py-3 rounded-xl text-sm font-semibold
    bg-white border-2 border-[rgba(244,63,94,0.50)] text-[#F43F5E]
    hover:bg-[rgba(244,63,94,0.04)] transition-colors "Contact Sales"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CTA BANNER SECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<section> relative overflow-hidden py-24 px-6
  bg-gradient-to-br from-[#7C3AED] to-[#0EA5E9]

Background blobs (absolute, pointer-events-none, rounded-full):
  w-[500px] h-[500px] top-[-200px] right-[-200px]
    bg-white/10 blur-[80px] animate-blob-float
  w-[300px] h-[300px] bottom-[-100px] left-[-100px]
    bg-white/8 blur-[60px] animate-blob-float2

Content: relative z-10 max-w-2xl mx-auto text-center
  H2: text-4xl md:text-5xl font-display font-bold text-white mb-4
    "Ready to meet your digital self?"
  Sub: text-lg text-white/75 mb-10
    "Join 50,000+ creators already using SELPH."
  Email form: flex flex-col sm:flex-row gap-3 max-w-md mx-auto
    Input state: const [email, setEmail] = useState('')
    <input type="email" value={email} onChange={e => setEmail(e.target.value)}
      placeholder="Enter your email"
      className="flex-1 px-5 py-4 rounded-xl text-[#0F172A] text-sm
        border-0 outline-none shadow-[0_2px_8px_rgba(0,0,0,0.10)]
        placeholder:text-[#94A3B8]" />
    <button className="px-6 py-4 rounded-xl text-sm font-semibold whitespace-nowrap
      bg-white text-[#7C3AED] hover:bg-white/90 transition-colors
      shadow-[0_4px_16px_rgba(0,0,0,0.15)] hover:-translate-y-0.5">
      Get Early Access
    </button>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOTER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

<footer> bg-white border-t border-[#F1F5F9] py-8 px-6

Inner: max-w-7xl mx-auto flex flex-col sm:flex-row items-center
  justify-between gap-4

Left:
  <span className="font-display font-extrabold text-xl gradient-text">SELPH</span>
  <p className="text-xs text-[#94A3B8] mt-1">
    © 2026 SELPH AI. All rights reserved.
  </p>

Right links: flex gap-6
  Each: text-sm text-[#94A3B8] hover:text-[#64748B] transition-colors
  "Privacy" · "Terms" · "Twitter" · "Discord"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULES — DO NOT VIOLATE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. NO dark backgrounds anywhere (no bg-gray-900, bg-slate-900, bg-black, etc.)
2. NO framer-motion (not installed)
3. All sections must be in a single app/page.tsx file
4. Use only: next, react, tailwindcss, typescript, lucide-react
5. All interactive elements (button, input) must have keyboard focus styles:
   focus:outline-none focus:ring-2 focus:ring-[#7C3AED] focus:ring-offset-2
6. All icon-only buttons must have aria-label
7. Use @media (prefers-reduced-motion: reduce) — already in globals.css
8. The "use client" directive must be the very first line of page.tsx
