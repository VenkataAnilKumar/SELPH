# SELPH — UI/UX Design System 2026

> Version: 3.0
> Created: 2026-04-27
> Folder: 07-design
> Status: Active — Light & Colorful 2026 Design Language

---

## Design Manifesto

> **"Your second self — bright, alive, and unmistakably you."**

SELPH is personal, warm, and full of energy.

Light backgrounds. Bold color. Joyful motion.

Every screen feels human — not cold or corporate.
Every color celebrates identity and individuality.
Every interaction feels effortless and alive.

---

## Design Principles

| Principle | Direction |
|---|---|
| **Light first** | White and soft off-white canvas. Color adds energy, not weight |
| **Colorful identity** | Each user's twin feels uniquely theirs — color as personality |
| **Warmth** | Rounded corners, soft shadows, generous padding — approachable |
| **Clarity** | High contrast text on light backgrounds. Zero ambiguity |
| **Joy** | Micro-animations that delight — bouncy, spring-physics |
| **Accessibility** | WCAG AA minimum on all color combinations |

---

## Color System — Vibrant Light

```
┌─────────────────────────────────────────────────────────────────┐
│                    SELPH LIGHT PALETTE                          │
│                                                                 │
│  CANVAS (backgrounds)                                           │
│  ├── Pure White        #FFFFFF   ← hero, main pages            │
│  ├── Warm White        #FAFAF9   ← page base                   │
│  ├── Soft Cloud        #F5F3FF   ← light violet tint sections  │
│  ├── Pearl             #F9FAFB   ← card surfaces               │
│  └── Mist              #F0F9FF   ← blue-tinted section areas   │
│                                                                 │
│  BRAND COLORS (the soul of SELPH)                              │
│  ├── SELPH Violet      #7C3AED   ← primary brand              │
│  ├── Electric Purple   #9333EA   ← hover / gradient end        │
│  ├── Sky Blue          #0EA5E9   ← trust, calm, data           │
│  ├── Coral Pink        #F43F5E   ← energy, creative            │
│  ├── Tangerine         #F97316   ← warm, social, creators      │
│  └── Emerald           #10B981   ← success, approve            │
│                                                                 │
│  GRADIENT PALETTE (SELPH signature gradients)                   │
│  ├── Violet → Sky      #7C3AED → #0EA5E9                       │
│  ├── Coral → Tangerine #F43F5E → #F97316                       │
│  ├── Purple → Pink     #9333EA → #EC4899                       │
│  └── Sky → Emerald     #0EA5E9 → #10B981                       │
│                                                                 │
│  TEXT                                                           │
│  ├── Title             #0F172A   ← near-black slate            │
│  ├── Body              #334155   ← readable slate              │
│  ├── Muted             #64748B   ← secondary text              │
│  └── Placeholder       #94A3B8   ← inputs, hints               │
│                                                                 │
│  SEMANTIC (actions — clear and confident)                       │
│  ├── Approve   #10B981  ← emerald green — positive             │
│  ├── Edit      #F59E0B  ← amber — considered change            │
│  ├── Reject    #EF4444  ← red — clear stop                     │
│  └── Flag      #F97316  ← orange — attention needed            │
└─────────────────────────────────────────────────────────────────┘
```

### Core Gradients (CSS)

```css
/* SELPH Primary — Violet to Sky */
background: linear-gradient(135deg, #7C3AED 0%, #0EA5E9 100%);

/* Energy — Coral to Tangerine (creators, social) */
background: linear-gradient(135deg, #F43F5E 0%, #F97316 100%);

/* Purple Haze — brand hero gradient */
background: linear-gradient(135deg, #9333EA 0%, #EC4899 100%);

/* Success glow */
background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);

/* Soft card tint — light violet wash */
background: linear-gradient(135deg,
  rgba(124,58,237,0.06) 0%,
  rgba(14,165,233,0.06) 100%
);

/* White glass card */
background: rgba(255,255,255,0.85);
backdrop-filter: blur(20px) saturate(150%);
border: 1px solid rgba(124,58,237,0.12);
box-shadow:
  0 4px 24px rgba(124,58,237,0.08),
  0 1px 4px rgba(0,0,0,0.04);
border-radius: 24px;

/* Colorful avatar ring — identity gradient */
background: conic-gradient(
  from 0deg,
  #7C3AED, #0EA5E9, #10B981, #F43F5E, #9333EA, #7C3AED
);
border-radius: 50%;
padding: 3px;
```

---

## Typography

```
FONTS:
  Display:   "Plus Jakarta Sans"   — friendly, modern, expressive
  Headings:  "Plus Jakarta Sans"   — consistent brand voice
  Body:      "Inter"               — clean, readable everywhere
  Mono/Data: "JetBrains Mono"     — code, IDs, precision data

TYPE SCALE:
  Hero Display:  72px / 80px  — Bold 800
  H1:            48px / 56px  — Bold 700
  H2:            36px / 44px  — SemiBold 600
  H3:            24px / 32px  — SemiBold 600
  Body Large:    18px / 28px  — Regular 400
  Body:          16px / 24px  — Regular 400
  Small:         14px / 20px  — Medium 500
  Caption:       12px / 16px  — Regular 400
  Label:         11px / 14px  — SemiBold 600, letter-spacing 0.08em, UPPERCASE

GRADIENT TEXT (SELPH brand titles):
  background: linear-gradient(135deg, #7C3AED, #0EA5E9);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
```

---

## Spacing & Shape

```
BORDER RADIUS:
  Small:    8px    ← tags, badges, small chips
  Medium:   12px   ← buttons, inputs
  Large:    16px   ← small cards
  XL:       24px   ← main cards, panels
  2XL:      32px   ← modals, sheets
  Full:     9999px ← pills, avatars

SPACING SCALE (4pt grid):
  4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128px

SHADOWS (colorful, soft):
  Soft:    0 2px 8px rgba(0,0,0,0.06)
  Card:    0 4px 24px rgba(124,58,237,0.08), 0 1px 4px rgba(0,0,0,0.04)
  Lifted:  0 8px 40px rgba(124,58,237,0.14), 0 2px 8px rgba(0,0,0,0.06)
  Float:   0 16px 64px rgba(124,58,237,0.20), 0 4px 16px rgba(0,0,0,0.08)
  Colored: 0 8px 24px rgba(249,115,22,0.25)   ← per semantic color
```

---

## Component Library

### Buttons

```css
/* Primary — gradient, bold */
.btn-primary {
  background: linear-gradient(135deg, #7C3AED 0%, #0EA5E9 100%);
  color: white;
  border-radius: 12px;
  padding: 14px 28px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  box-shadow: 0 4px 16px rgba(124,58,237,0.30);
  transition: transform 0.15s spring, box-shadow 0.15s;
}
.btn-primary:hover {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 8px 28px rgba(124,58,237,0.40);
}
.btn-primary:active { transform: scale(0.98); }

/* Secondary — outlined, colorful border */
.btn-secondary {
  background: white;
  color: #7C3AED;
  border: 2px solid #7C3AED;
  border-radius: 12px;
  padding: 12px 28px;
  font-weight: 600;
  transition: all 0.15s;
}
.btn-secondary:hover {
  background: rgba(124,58,237,0.06);
  transform: translateY(-1px);
}

/* Approve — twin action */
.btn-approve {
  background: linear-gradient(135deg, #10B981, #06B6D4);
  color: white;
  border-radius: 12px;
  padding: 14px 32px;
  font-size: 18px;
  font-weight: 700;
  box-shadow: 0 4px 16px rgba(16,185,129,0.30);
}
.btn-approve:hover { box-shadow: 0 8px 28px rgba(16,185,129,0.45); }

/* Edit — twin action */
.btn-edit {
  background: linear-gradient(135deg, #F59E0B, #F97316);
  color: white;
  border-radius: 12px;
  padding: 14px 32px;
  font-size: 18px;
  font-weight: 700;
}

/* Reject — twin action */
.btn-reject {
  background: white;
  color: #EF4444;
  border: 2px solid #EF4444;
  border-radius: 12px;
  padding: 12px 32px;
  font-weight: 700;
}
.btn-reject:hover { background: rgba(239,68,68,0.06); }
```

### Cards

```css
/* Standard card — clean white + soft shadow */
.card {
  background: white;
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 4px 24px rgba(124,58,237,0.08), 0 1px 4px rgba(0,0,0,0.04);
  border: 1px solid rgba(124,58,237,0.08);
}

/* Colorful gradient card */
.card-gradient {
  background: linear-gradient(135deg,
    rgba(124,58,237,0.06) 0%,
    rgba(14,165,233,0.06) 100%
  );
  border-radius: 24px;
  padding: 28px;
  border: 1px solid rgba(124,58,237,0.12);
}

/* Avatar/identity card — colorful ring */
.identity-card {
  background: white;
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 8px 40px rgba(124,58,237,0.12);
  position: relative;
}
.identity-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 26px;
  background: conic-gradient(
    from 0deg, #7C3AED, #0EA5E9, #10B981, #F43F5E, #7C3AED
  );
  z-index: -1;
  animation: spin 8s linear infinite;
}
```

### Input Fields

```css
.input {
  background: white;
  border: 2px solid #E2E8F0;
  border-radius: 12px;
  padding: 14px 18px;
  font-size: 16px;
  color: #0F172A;
  width: 100%;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.input:focus {
  border-color: #7C3AED;
  box-shadow: 0 0 0 4px rgba(124,58,237,0.12);
  outline: none;
}
.input::placeholder { color: #94A3B8; }
```

### Badges & Tags

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
}
.badge-violet  { background: rgba(124,58,237,0.10); color: #7C3AED; }
.badge-sky     { background: rgba(14,165,233,0.10);  color: #0EA5E9; }
.badge-emerald { background: rgba(16,185,129,0.10);  color: #10B981; }
.badge-coral   { background: rgba(244,63,94,0.10);   color: #F43F5E; }
.badge-orange  { background: rgba(249,115,22,0.10);  color: #F97316; }
```

---

## Screen Designs

### 1. Landing Page — selph.ai

#### Hero Section
```
Background: Pure White #FFFFFF

Layout:
  ┌────────────────────────────────────────────────┐
  │  Nav: SELPH logo  [Features] [Pricing] [Login] │
  │       [Get Started →]                           │
  ├────────────────────────────────────────────────┤
  │                                                │
  │   Colorful gradient blob (violet+sky, blur     │
  │   120px, opacity 0.25) behind hero text        │
  │                                                │
  │   [Tag chip: ✦ Your Digital Self]              │
  │                                                │
  │   Your second self,                            │  ← 72px Bold, #0F172A
  │   ─────────────────                            │
  │   always available.                            │
  │   ─────────────────                            │
  │   (gradient underline: violet → sky)           │
  │                                                │
  │   Subheadline:                                 │  ← 20px, #64748B
  │   SELPH learns who you are — your voice,       │
  │   expertise, and style — then acts on your     │
  │   behalf across every platform, 24/7.          │
  │                                                │
  │   [Get Started Free]  [Watch Demo ▶]           │
  │   Gradient btn        Ghost btn                │
  │                                                │
  │   ── 50,000+ people have a SELPH twin ──       │  ← #94A3B8
  │   [Avatar stack] [Avatar stack] [Avatar stack] │
  │                                                │
  ├────────────────────────────────────────────────┤
  │                                                │
  │   Twin Preview Card (floating, soft shadow):   │
  │   ┌──────────────────────────────────────┐     │
  │   │ 🟣 SELPH Twin — Online               │     │
  │   │ ─────────────────────────────────── │     │
  │   │ Incoming: "Can you review my       │     │
  │   │ proposal before Thursday?"          │     │
  │   │ ─────────────────────────────────── │     │
  │   │ Draft ready · 2 min ago             │     │
  │   │ [✓ Approve] [✎ Edit] [✕ Skip]      │     │
  │   └──────────────────────────────────── ┘     │
  └────────────────────────────────────────────────┘

Floating blobs:
  - Large: rgba(124,58,237,0.15), 600px, blur(80px), top-right
  - Medium: rgba(14,165,233,0.12), 400px, blur(60px), bottom-left
  - Small: rgba(244,63,94,0.10), 300px, blur(60px), mid-right
```

#### Identity Layers Section
```
Background: Soft Cloud #F5F3FF (light violet wash)

4-card row — each card:
  ┌─────────────────────┐
  │  [Gradient icon]    │  ← 48px emoji / icon in gradient circle
  │                     │
  │  Voice Clone        │  ← 20px SemiBold #0F172A
  │  ─────────────────  │
  │  Your tone, accent, │  ← 15px #64748B
  │  and speech pattern │
  │  captured perfectly │
  └─────────────────────┘

Card 1 — Voice: gradient #7C3AED → #0EA5E9, icon 🎙️
Card 2 — Avatar: gradient #F43F5E → #F97316, icon 🎭
Card 3 — Mind: gradient #9333EA → #EC4899, icon 🧠
Card 4 — Data: gradient #10B981 → #0EA5E9, icon 📊
```

#### How It Works — 3 Steps
```
Background: White

Step chips (numbered, gradient circle):
  ① Your Device + Your Data + Your Voice
    → Large: gradient violet → sky, 64px circle, white number

  ② SELPH Twin analyzes and drafts
    → Large: gradient coral → orange, 64px circle

  ③ You approve in one tap
    → Large: gradient emerald → sky, 64px circle

Connector lines between steps: dashed, gradient stroke
```

#### Features Bento Grid
```
Background: Warm White #FAFAF9

Grid layout (3 columns, mixed sizes):
  ┌───────────────┬───────┬───────┐
  │               │       │       │
  │  Twin Feed    │ Voice │Avatar │
  │  (large card) │ Clone │ Clone │
  │               │       │       │
  ├───────┬───────┴───────┬───────┤
  │ Smart │ 24/7 Active   │  Stats│
  │ Reply │               │       │
  └───────┴───────────────┴───────┘

Each card: white bg, 24px radius, colorful icon, gradient accent strip at top
Large card gets gradient bg (light violet wash)
```

#### Pricing Section
```
Background: White

3 cards in a row:
  Free     →  white card, violet border
  Pro      →  gradient card (violet→sky), white text — FEATURED — lifted shadow
  Creator  →  white card, coral border

Pricing card style:
  ┌───────────────────────────┐
  │ [Badge: Most Popular]     │
  │ Pro                       │
  │ $29/month                 │
  │ ─────────────────────── │
  │ ✓ Full voice clone        │
  │ ✓ Avatar twin             │
  │ ✓ All integrations        │
  │ ✓ Private mode            │
  │ ─────────────────────── │
  │ [Get Started →]           │
  └───────────────────────────┘
```

---

### 2. Web App — app.selph.ai Dashboard

```
Layout: White sidebar (left 240px) + White main content

SIDEBAR:
  Background: White
  Border-right: 1px solid #F1F5F9
  ─────────────────────────
  SELPH logo (gradient)
  ─────────────────────────
  [Avatar: User photo + spinning gradient ring]
  Alex Chen               ← 14px SemiBold
  alex@email.com          ← 12px #94A3B8
  Twin: Active 🟢         ← badge emerald
  ─────────────────────────
  🏠 Dashboard
  📬 Twin Feed  [3]        ← badge violet = pending count
  🎙️  Voice
  🎭  Avatar
  🧠  Mind Clone
  🔗  Integrations
  ⚙️  Settings
  ─────────────────────────
  [Upgrade to Pro ✦]       ← gradient button, bottom

MAIN CONTENT:
  Background: Warm White #FAFAF9
  Padding: 40px

  Top row:
    "Good morning, Alex 👋"  ← 28px Bold
    "Your twin handled 12 messages today"  ← 16px #64748B

  Stats row (4 cards):
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ 📬 12    │ │ ✓  9     │ │ 🔥  94%  │ │ ⚡ 1.2s  │
    │ Incoming │ │ Approved │ │ Accuracy │ │ Avg resp │
    └──────────┘ └──────────┘ └──────────┘ └──────────┘
    Card: white, 16px radius, violet-tinted top border 3px

  Twin Feed (pending approvals):
    Section header: "Needs Your Attention" + [View All]

    Feed item card:
    ┌──────────────────────────────────────────────────────┐
    │ 🟣 Instagram DM · Sarah Kim · 2 min ago  [Pending]  │
    │ ──────────────────────────────────────────────────── │
    │ RECEIVED:                                            │
    │ "Hey! Love your content. Can you do a               │
    │  collaboration on..."                                │
    │ ──────────────────────────────────────────────────── │
    │ TWIN DRAFT:                                 [98% ●] │
    │ "Hi Sarah! Thank you so much — I'd love to          │
    │  explore a collab! My niche is..."                  │
    │ ──────────────────────────────────────────────────── │
    │    [✓ Approve]      [✎ Edit]      [✕ Reject]       │
    └──────────────────────────────────────────────────────┘
    Card: white, shadow lifted, left border 4px violet

    Confidence ring (98%):
      background: conic-gradient(#10B981 98%, #F1F5F9 0%)
      36px circle, emerald green fill

  Activity chart:
    "Twin Activity — Last 7 Days"
    Soft gradient area chart (violet fill, 20% opacity)
    White card, 24px radius
```

---

### 3. Mobile App

#### Onboarding Flow

```
Screen 1 — Welcome
  Background: White
  Large animated gradient blob (violet → sky) centered, 400px, blur 80px, opacity 0.20

  SELPH logo (gradient)       ← center top
  ─────────────────────────
  "Meet your                  ← 40px Bold #0F172A
   digital self"
  ─────────────────────────
  "SELPH learns who you are   ← 16px #64748B
   and acts on your behalf."
  ─────────────────────────
  [Get Started]               ← gradient button, full-width, 56px height
  [I already have an account] ← text link, violet

Screen 2 — Identity Setup
  Background: White with soft top wave gradient (violet 8% opacity)

  Progress bar (gradient violet → sky, 4px height)
  "Let's build your twin" ← 28px Bold

  4 setup cards (tappable):
    [🎙️  Voice Sample]    Completed ✓  → border emerald
    [🎭  Avatar Scan]     In Progress  → border violet + spinner
    [🧠  Mind Training]   Pending      → border #E2E8F0
    [📊  Connect Apps]    Pending      → border #E2E8F0

Screen 3 — Voice Recording
  Background: White
  Center: Large circle (gradient conic border, 160px)
    inside: mic icon 48px
    pulsing ring animation on active recording

  Waveform visualization: colorful bars (violet → sky gradient)
  "Speak naturally for 30 seconds" ← 16px #64748B
  Progress arc: gradient violet → sky
```

#### Home Screen (Mobile Dashboard)

```
Background: White
Status bar: light

TOP SECTION:
  "Hey Alex 👋"            ← 24px Bold
  "Twin is active"          ← 14px #64748B
  [Avatar + spinning conic ring]   ← 56px, right side

  Active chip:
    [🟢 Twin Active · 12 tasks handled]
    background: rgba(16,185,129,0.10), border: #10B981, radius: 999px

PENDING CARDS (horizontal scroll):
  Each card: white, 20px radius, shadow
  Color left border per platform:
    Instagram  → #F43F5E (coral)
    Email      → #7C3AED (violet)
    Slack      → #F97316 (orange)
    GitHub     → #0F172A (slate)

  Card layout:
    [Platform icon] [Name] [time]   ← top row
    Message preview (2 lines)       ← #334155
    Twin draft chip                 ← gradient, truncated
    [✓ Approve] [✎] [✕]            ← action row, compact

QUICK STATS ROW:
  3 inline stat chips (horizontal scroll):
    [📬 12 incoming]    violet bg
    [✓ 9 approved]      emerald bg
    [🔥 94% accuracy]   coral bg

TWIN ACTIVITY CHART:
  Compact area chart (3-day view)
  Gradient fill violet → sky, 12% opacity
  White card, 20px radius, colorful x-axis labels
```

#### Draft Review Screen (Full Screen)

```
Background: White

TOP: Platform + contact info, time badge
  [Instagram icon] Sarah Kim · 2 min ago

RECEIVED MESSAGE:
  Pale violet pill label: "RECEIVED"
  Light gray bubble (left aligned, 16px radius):
    Message text in full

TWIN DRAFT:
  Gradient pill label (violet → sky): "TWIN DRAFT"
  Confidence badge: [● 98%] emerald
  Light violet bubble (right aligned, 16px radius):
    Draft text, editable inline

BOTTOM ACTION BAR:
  ┌───────────────────────────────────────────┐
  │  [✓ Approve]   [✎ Edit]   [✕ Reject]    │
  │  Gradient-grn   Gradient-amb  White/red  │
  │  56px          56px           56px       │
  └───────────────────────────────────────────┘
  Background: white with top shadow
  Safe area padding
```

---

## Motion Design

### Animation Tokens

```css
/* Easing */
--ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1);   /* bouncy buttons */
--ease-smooth:     cubic-bezier(0.4, 0, 0.2, 1);         /* standard */
--ease-enter:      cubic-bezier(0, 0, 0.2, 1);           /* items entering */
--ease-exit:       cubic-bezier(0.4, 0, 1, 1);           /* items leaving */

/* Durations */
--duration-micro:  100ms;   /* hover state changes */
--duration-fast:   200ms;   /* buttons, chips */
--duration-base:   300ms;   /* cards, panels */
--duration-slow:   500ms;   /* page transitions, reveals */
--duration-gentle: 800ms;   /* hero elements, blobs */
```

### Key Animations

```css
/* Card entrance — slides up + fades in */
@keyframes card-enter {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Blob float — slow ambient movement */
@keyframes blob-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33%       { transform: translate(20px, -20px) scale(1.05); }
  66%       { transform: translate(-15px, 15px) scale(0.97); }
}
animation: blob-float 12s ease-in-out infinite;

/* Twin ring pulse */
@keyframes ring-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.6; transform: scale(1.08); }
}

/* Spin (identity conic ring) */
@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
animation: spin 8s linear infinite;

/* Waveform bar (voice recording) */
@keyframes wave-bar {
  0%, 100% { height: 8px; }
  50%       { height: 40px; }
}
/* Each bar staggered: animation-delay: calc(var(--i) * 80ms) */

/* Stagger reveal (feature cards) */
.card:nth-child(1) { animation-delay: 0ms; }
.card:nth-child(2) { animation-delay: 80ms; }
.card:nth-child(3) { animation-delay: 160ms; }
.card:nth-child(4) { animation-delay: 240ms; }
```

### Framer Motion (Web — Next.js)

```tsx
// Page hero — stagger children
const heroVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.10 } }
}
const heroItem = {
  hidden:  { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0,0,0.2,1] } }
}

// Card hover — spring lift
const cardHover = {
  whileHover: { y: -4, scale: 1.01, transition: { type: 'spring', stiffness: 400, damping: 20 } },
  whileTap:   { scale: 0.98 }
}

// Approve button — bouncy
const approveBtn = {
  whileTap: { scale: 0.94, transition: { type: 'spring', stiffness: 600, damping: 15 } }
}

// Confidence ring draw
<motion.circle
  initial={{ pathLength: 0 }}
  animate={{ pathLength: confidence }}
  transition={{ duration: 1, ease: 'easeOut', delay: 0.4 }}
/>
```

### React Native / Reanimated 3 (Mobile)

```tsx
// Card swipe to approve
const translateX = useSharedValue(0);
const gestureHandler = useAnimatedGestureHandler({
  onActive: (e) => { translateX.value = e.translationX; },
  onEnd: (e) => {
    if (e.translationX > 120) {
      translateX.value = withSpring(500);
      runOnJS(handleApprove)();
    } else {
      translateX.value = withSpring(0);
    }
  }
});
// Background reveal: emerald on right-swipe, red on left-swipe

// Blob animation
const blobScale = useSharedValue(1);
useEffect(() => {
  blobScale.value = withRepeat(
    withSequence(
      withTiming(1.08, { duration: 4000 }),
      withTiming(1.0,  { duration: 4000 })
    ), -1, true
  );
}, []);
```

---

## Illustration & Icon System

```
ICONS:
  Library:    Lucide React (stroke style, 1.5px, rounded caps)
  Size scale: 16px, 20px, 24px, 32px, 48px
  Color:      Inherit from parent or explicit brand color
  Style:      Stroke icons only — no filled icon mixing

FEATURE ICONS (large, 48px+):
  Display in gradient circle:
    width: 72px, height: 72px, border-radius: 20px
    background: linear-gradient(135deg, color1, color2)
    icon: white, 32px, centered

ILLUSTRATIONS (hero, onboarding):
  Style: Colorful, rounded, flat with soft shadows
  Palette: SELPH brand colors only
  Characters: Diverse, friendly, modern
  No dark backgrounds in illustrations

AVATARS:
  Border: conic-gradient ring (spinning, 3px)
  Fallback: Initials in gradient circle
  Status dot: solid color (green=active, gray=offline)
```

---

## Accessibility

| Requirement | Implementation |
|---|---|
| **Contrast ratio** | Min 4.5:1 for body text, 3:1 for large text and UI elements |
| **Focus states** | 4px ring, color: #7C3AED, offset 2px — always visible |
| **Touch targets** | Min 44×44px on mobile |
| **Motion sensitivity** | `prefers-reduced-motion` — disable all animations, keep layout |
| **Color blind safe** | Never use color alone as the only signal — always add icon or label |
| **Screen reader** | All icons have `aria-label`, all interactive elements have roles |

---

## Implementation Stack

| Layer | Technology |
|---|---|
| **Web framework** | Next.js 15 (App Router) |
| **Styling** | Tailwind CSS v4 |
| **Animations** | Framer Motion 12 |
| **Components** | Radix UI (headless, accessible) |
| **Fonts** | Plus Jakarta Sans + Inter + JetBrains Mono (Google Fonts) |
| **Icons** | Lucide React |
| **Charts** | Recharts (area chart, confidence ring) |
| **Mobile** | React Native (Expo) |
| **Mobile style** | NativeWind (Tailwind for React Native) |
| **Mobile animation** | Reanimated 3 + Gesture Handler |
| **Scroll** | Lenis smooth scroll (web) |

---

## Design Token Reference (Tailwind v4)

```css
/* tailwind.config — extend */
colors: {
  selph: {
    violet:  '#7C3AED',
    purple:  '#9333EA',
    sky:     '#0EA5E9',
    coral:   '#F43F5E',
    orange:  '#F97316',
    emerald: '#10B981',
    white:   '#FFFFFF',
    warm:    '#FAFAF9',
    cloud:   '#F5F3FF',
    mist:    '#F0F9FF',
    title:   '#0F172A',
    body:    '#334155',
    muted:   '#64748B',
    subtle:  '#94A3B8',
  },
  approve: '#10B981',
  edit:    '#F59E0B',
  reject:  '#EF4444',
  flag:    '#F97316',
}
borderRadius: {
  sm:   '8px',
  md:   '12px',
  lg:   '16px',
  xl:   '24px',
  '2xl':'32px',
}
```

---

*Document version: 3.0 — Light & Colorful 2026*
*Previous: v2.0 Cinematic Dark (deprecated)*
*Created: 2026-04-27*
