# SELPH — Your Digital Self

> *"Be everywhere. Be SELPH."*

A universal Digital Twin AI that learns your voice, avatar, identity, and expertise — then acts on your behalf across any domain.

---

## What is SELPH?

SELPH is a **human-in-the-loop AI agent** that:

1. **Learns who you are** via onboarding, social content analysis, and voice/avatar recording
2. **Captures your communication style** — tone, vocabulary, length, emoji usage, greetings
3. **Drafts responses as YOU** to incoming messages on Instagram, Gmail, Twitter, WhatsApp, Slack, etc.
4. **Stays in control** — you review and approve every draft before it's sent (graduated autonomy)
5. **Gets better over time** — learns from your approvals, edits, and rejections

---

## Repository Structure

```
selph-ai/
├── docs/                           # Product, market, specs, safety, technical, implementation, design
├── src/
│   ├── backend/                    # FastAPI on Railway
│   ├── web/                        # Next.js dashboard on Vercel
│   ├── landing/                    # Next.js marketing site on Vercel
│   ├── mobile/                     # React Native + Expo (iOS + Android)
│   ├── shared/                     # TS types + API client
│   └── services/                   # Future microservices (stubs)
├── .github/workflows/              # CI/CD
└── README.md
```

---

## Quick Start

### Prerequisites

```bash
node --version        # 20+
python --version      # 3.11+
docker --version      # latest
npm install -g @railway/cli
pip install uv
npm install -g expo-cli
```

### Accounts Needed

- [ ] GitHub (create `selph-ai` private repo)
- [ ] Railway (railway.app)
- [ ] Vercel (vercel.com)
- [ ] Cloudflare (cloudflare.com)
- [ ] Anthropic (console.anthropic.com) — Claude API
- [ ] Firebase (console.firebase.google.com) — Push notifications

### Local Development

1. **Backend (FastAPI)**
   ```bash
   cd src/backend
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows PowerShell
   python -m pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   docker-compose up -d       # PostgreSQL + Redis
   alembic upgrade head       # Run migrations
   python -m uvicorn app.main:app --reload
   # Open http://localhost:8000/docs for API docs
   ```

2. **Web Dashboard (Next.js)**
   ```bash
   cd src/web
   npm install
   npm run dev
   # Open http://localhost:3000
   ```

3. **Mobile App (React Native)**
   ```bash
   cd src/mobile
   npm install
   npx expo start
   # Scan QR code with Expo Go app on phone
   ```

4. **Landing Page (Next.js Static)**
   ```bash
   cd src/landing
   npm install
   npm run dev
   # Open http://localhost:3001
   ```

---

## Build Timeline

| Phase | Weeks | Goal | Output |
|---|---|---|---|
| **Phase 0** | 1–2 | Foundation | Auth, DB, API shell |
| **Phase 1** | 2–5 | Identity Core | Profile, social ingestion, vectors |
| **Phase 1 Expansion** | 6–9 | Expansion Features | Twin Briefing, VIP Override, Batch Approval |
| **Phase 2** | 5–7 | Twin Engine | Draft generation, confidence scoring |
| **Phase 3** | 7–9 | Approval Loop | Notifications, mobile UI, feedback loop |
| **Phase 4** | 9–10 | Safety Layer | Moderation, audit, watermarking, anomaly detection |
| **Phase 5** | 10–13 | Channels | Instagram + Gmail live |
| **Phase 6** | 13–15 | Voice Clone | Voice cloning integration |
| **Phase 7** | 15–17 | Avatar Clone | Avatar generation integration |
| **Phase 8** | 17–19 | Beta Launch | Production hardening, beta rollout |

---

## Key Docs

- **Product:** [docs/01-product/PRODUCT_IDEA.md](docs/01-product/PRODUCT_IDEA.md)
- **PRD:** [docs/01-product/PRD.md](docs/01-product/PRD.md)
- **System Architecture:** [docs/05-technical/SELPH_System-Architecture.md](docs/05-technical/SELPH_System-Architecture.md)
- **Implementation Plan:** [docs/06-implementation/IMPLEMENTATION_PLAN.md](docs/06-implementation/IMPLEMENTATION_PLAN.md)
- **Safety & Policy:** [docs/04-safety/SELPH_Canonical-Policy-Matrix.md](docs/04-safety/SELPH_Canonical-Policy-Matrix.md)

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python + FastAPI |
| **Database** | PostgreSQL + pgvector |
| **LLM** | LiteLLM (default: Claude Sonnet 4.6) |
| **Queue** | Redis + Celery |
| **Mobile** | React Native + Expo |
| **Web** | Next.js 15 (App Router) |
| **Landing** | Next.js 15 (static) |
| **Auth** | JWT RS256 |
| **Hosting** | Railway (backend) + Vercel (frontend) + Cloudflare (DNS/R2) |

---

## Environment Variables

Create `.env` files in each service directory. See `.env.example` files for templates.

### Backend (.env)
```bash
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
FIREBASE_PROJECT_ID=selph
JWT_SECRET_KEY=...
```

### Web/Mobile
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_CONFIG={...}
```

---

## Running Tests

### Backend Tests
```bash
cd src/backend
. .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows PowerShell
pytest tests/ -v
```

### Web Tests
```bash
cd src/web
npm run test
```

### Mobile Tests
```bash
cd src/mobile
npm run test
```

---

## Deployment

### Backend (Railway)
```bash
railway up
```

### Web & Landing (Vercel)
```bash
# Auto-deploys on push to main via GitHub Actions
git push origin main
```

---

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Write tests and code
3. Commit with clear messages: `git commit -m "feat: add thing"`
4. Push and open a PR
5. Ensure CI passes (tests, lint, security)
6. Get approval and merge

---

## Safety & Compliance

All safety decisions reference the **Canonical Policy Matrix**:
- [SELPH_Canonical-Policy-Matrix.md](docs/04-safety/SELPH_Canonical-Policy-Matrix.md)

Key principles:
- ✅ **Human-in-the-loop always** — twin never acts autonomously
- ✅ **Graduated trust** — twin earns autonomy through feedback
- ✅ **Policy-driven** — all decisions derive from canonical policies
- ✅ **Audit trail** — immutable log of every action
- ✅ **Consent-first** — users explicitly opt into features

---

## Support

- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Email:** hello@selph.ai (coming soon)

---

## License

Proprietary — not open source (2026).

---

**Built by SELPH Team**
Last Updated: April 27, 2026
