# SELPH — Implementation Plan

> Version: 1.2
> Created: 2026-04-27
> Updated: 2026-04-30
> Status: Complete — Phases 0–10 built and CI-validated (v1.0.0-rc)
> Reference: [MVP_BUILD_PLAN.md](./MVP_BUILD_PLAN.md) — high-level phases
> Next: [DEPLOYMENT_PLAN.md](./DEPLOYMENT_PLAN.md) — Phases 11–16, infra to pilot
> This doc: hands-on, file-level, command-level execution guide for the build phase
>
> **v1.1 changes:** API versioning (/v1/), channel adapter pattern, service registry,
> feature flags, voice/avatar queue placeholders, microservice extraction boundaries
>
> **v1.2 changes:** Status updated to Complete. All 14 routers, 8 migrations, and Phase 10
> end-to-end features are built and passing CI (287 backend + 23 web + 32 mobile tests).

---

## How to Use This Document

- Follow sections in order — each section depends on the previous
- Every `[ ]` checkbox = one concrete action
- Code blocks are the actual code to write, not pseudocode
- Commands are bash — run in your terminal

---

## Prerequisites

Before writing any code, set up these accounts and tools:

### Accounts Needed
- [ ] **GitHub** — create repo `selph-ai` (private)
- [ ] **Railway** — railway.app account (backend hosting)
- [ ] **Vercel** — vercel.com account (frontend hosting)
- [ ] **Cloudflare** — cloudflare.com account (R2 + DNS)
- [ ] **Anthropic** — console.anthropic.com (Claude API key)
- [ ] **Firebase** — console.firebase.google.com (push notifications)

### Local Dev Tools
```bash
# Required
node --version        # 20+
python --version      # 3.11+
docker --version      # latest
railway --version     # install: npm i -g @railway/cli

# Install Railway CLI
npm install -g @railway/cli

# Install Python tools
pip install uv        # fast Python package manager

# Install React Native
npm install -g expo-cli
```

---

## Repository Structure

```
selph-ai/
│
├── docs/                           # All documentation
│   ├── 01-product/
│   ├── 02-market/
│   ├── 03-specs/
│   ├── 04-safety/
│   ├── 05-technical/
│   ├── 06-implementation/
│   └── 07-design/
│
├── src/                            # All source code
│   │
│   ├── backend/                    # FastAPI — Railway
│   │   ├── app/                    # Python package (from app.x imports)
│   │   │   ├── __init__.py
│   │   │   ├── main.py             # FastAPI entry point + /v1/ prefix
│   │   │   ├── config.py           # Settings + feature flags
│   │   │   ├── database.py         # DB connection + session
│   │   │   │
│   │   │   ├── models/             # SQLAlchemy models (table ownership map)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py         # [OWNED BY: Auth]
│   │   │   │   ├── twin.py         # [OWNED BY: Twin Engine]
│   │   │   │   ├── message.py      # [OWNED BY: Channel]
│   │   │   │   ├── identity_samples.py  # [OWNED BY: Identity] pgvector
│   │   │   │   └── audit.py        # [OWNED BY: Audit]
│   │   │   │
│   │   │   ├── schemas/
│   │   │   │   ├── auth.py
│   │   │   │   ├── twin.py
│   │   │   │   └── message.py
│   │   │   │
│   │   │   ├── routers/            # All under /v1/
│   │   │   │   ├── auth.py         # /v1/auth/*
│   │   │   │   ├── twin.py         # /v1/twin/*
│   │   │   │   ├── messages.py     # /v1/messages/*
│   │   │   │   ├── drafts.py       # /v1/drafts/*
│   │   │   │   └── channels.py     # /v1/channels/*
│   │   │   │
│   │   │   ├── channels/           # Channel adapter pattern
│   │   │   │   ├── base.py         # Abstract ChannelAdapter interface
│   │   │   │   ├── instagram.py
│   │   │   │   ├── gmail.py
│   │   │   │   └── registry.py
│   │   │   │
│   │   │   ├── services/           # Business logic (microservice boundaries)
│   │   │   │   ├── registry.py     # Service registry (interface layer)
│   │   │   │   ├── twin_engine.py  # run_twin_pipeline() extraction boundary
│   │   │   │   ├── identity.py
│   │   │   │   ├── confidence.py
│   │   │   │   ├── moderation.py
│   │   │   │   └── notifications.py
│   │   │   │
│   │   │   ├── workers/            # Celery tasks
│   │   │   │   ├── celery_app.py   # 4 queues: drafts, channels, voice, avatar
│   │   │   │   ├── draft_tasks.py
│   │   │   │   ├── channel_tasks.py
│   │   │   │   ├── voice_tasks.py  # placeholder — Phase 6
│   │   │   │   └── avatar_tasks.py # placeholder — Phase 7
│   │   │   │
│   │   │   └── middleware/
│   │   │       └── auth.py         # JWT RS256 verification
│   │   │
│   │   ├── migrations/             # Alembic — outside app/, not in Docker image
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   │       └── 001_initial_schema.py
│   │   ├── tests/                  # Outside app/ — excluded from Docker image
│   │   │   ├── test_auth.py
│   │   │   ├── test_twin_engine.py
│   │   │   └── test_drafts.py
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml      # Local dev: API + worker + postgres + redis
│   │   ├── requirements.txt
│   │   ├── alembic.ini
│   │   └── .env.example
│   │
│   ├── web/                        # Next.js 15 — app.selph.ai (Vercel)
│   │   ├── app/                    # App Router — dashboard only
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Redirect → /dashboard
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── signup/page.tsx
│   │   │   └── dashboard/
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx        # Twin feed + stats
│   │   │       ├── feed/page.tsx
│   │   │       ├── identity/page.tsx
│   │   │       └── settings/page.tsx
│   │   ├── components/
│   │   │   ├── ui/                 # Button, Card, Badge, Input, ConfidenceRing
│   │   │   ├── twin/               # DraftCard, TwinStatusChip, ActivityChart
│   │   │   └── layout/             # Sidebar, TopBar
│   │   ├── lib/
│   │   │   └── auth.ts             # Token storage + route guard
│   │   ├── public/
│   │   ├── tailwind.config.ts
│   │   ├── next.config.ts
│   │   └── package.json
│   │
│   ├── landing/                    # Next.js 15 static — selph.ai (Vercel)
│   │   ├── app/                    # App Router — marketing only
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Hero, features, pricing
│   │   │   └── verify/
│   │   │       └── [id]/page.tsx   # Twin verification page
│   │   ├── components/
│   │   │   ├── Hero.tsx
│   │   │   ├── IdentityLayers.tsx
│   │   │   ├── HowItWorks.tsx
│   │   │   ├── Features.tsx
│   │   │   └── Pricing.tsx
│   │   ├── public/
│   │   ├── tailwind.config.ts
│   │   ├── next.config.ts          # output: 'export' for static generation
│   │   └── package.json
│   │
│   ├── mobile/                     # React Native — Expo (iOS + Android)
│   │   ├── app/                    # Expo Router
│   │   │   ├── _layout.tsx
│   │   │   ├── index.tsx
│   │   │   ├── (auth)/
│   │   │   │   ├── login.tsx
│   │   │   │   └── signup.tsx
│   │   │   └── (tabs)/
│   │   │       ├── _layout.tsx
│   │   │       ├── home.tsx
│   │   │       ├── feed.tsx
│   │   │       └── settings.tsx
│   │   ├── components/
│   │   │   ├── DraftCard.tsx
│   │   │   ├── TwinStatusBanner.tsx
│   │   │   └── ConfidenceBar.tsx
│   │   ├── lib/
│   │   │   └── notifications.ts    # Expo push token registration
│   │   ├── app.json
│   │   └── package.json
│   │
│   ├── shared/                     # Shared code — web + mobile consume this
│   │   ├── api/
│   │   │   ├── client.ts           # Base fetch wrapper (/v1/ prefix)
│   │   │   ├── auth.ts             # Auth endpoints
│   │   │   ├── twin.ts             # Twin endpoints
│   │   │   ├── drafts.ts           # Drafts endpoints
│   │   │   └── channels.ts         # Channel endpoints
│   │   ├── types/
│   │   │   ├── twin.ts             # Twin, Draft, Message types
│   │   │   ├── auth.ts             # User, Token types
│   │   │   └── channel.ts          # Channel types
│   │   ├── constants/
│   │   │   └── index.ts            # CHANNEL_COLORS, CONFIDENCE_THRESHOLDS
│   │   └── package.json            # name: "@selph/shared"
│   │
│   └── services/                   # Future microservices (empty stubs)
│       ├── twin-engine/            # Extract from src/backend/ — Phase 3
│       │   ├── app/
│       │   ├── Dockerfile
│       │   └── requirements.txt
│       ├── identity/               # Extract from src/backend/ — Phase 3
│       │   ├── app/
│       │   ├── Dockerfile
│       │   └── requirements.txt
│       ├── voice/                  # GPU worker — Phase 6
│       │   ├── app/
│       │   ├── Dockerfile.gpu
│       │   └── requirements.txt
│       └── avatar/                 # GPU worker — Phase 7
│           ├── app/
│           ├── Dockerfile.gpu
│           └── requirements.txt
│
├── .github/
│   └── workflows/
│       ├── backend-test.yml        # pytest on PR to main
│       ├── web-deploy.yml          # Vercel deploy src/web on push to main
│       └── landing-deploy.yml      # Vercel deploy src/landing on push to main
│
├── package.json                    # Root workspace (npm workspaces)
└── README.md
```

**Root `package.json` — workspace config**
```json
{
  "name": "selph-ai",
  "private": true,
  "workspaces": [
    "src/web",
    "src/landing",
    "src/mobile",
    "src/shared"
  ],
  "scripts": {
    "dev:web":     "npm -w src/web run dev",
    "dev:landing": "npm -w src/landing run dev",
    "dev:mobile":  "npm -w src/mobile run start"
  }
}
```

**How `shared` is consumed**
```typescript
// src/web/lib/api.ts — no duplicate code
export { api } from '@selph/shared/api'

// src/mobile/lib/api.ts
import { api } from '@selph/shared/api'
```

> **Microservice extraction rule:** when a service causes real pain,
> lift code from `src/backend/app/services/<name>.py` into `src/services/<name>/`
> and point Railway at its Dockerfile. Nothing else changes.

---

## Step 0 — Project Setup
**Time: 2–3 hours**

### 0.1 Create GitHub Repo
```bash
# Create repo on GitHub (UI), then:
git clone https://github.com/YOUR_USERNAME/selph-ai.git
cd selph-ai
mkdir -p src/backend src/web src/mobile src/services .github/workflows
```

### 0.2 Backend — Python Setup
```bash
cd src/backend
uv init --python 3.11
uv add fastapi uvicorn sqlalchemy asyncpg alembic pydantic pydantic-settings
uv add python-jose[cryptography] passlib[bcrypt] python-multipart
uv add celery redis httpx litellm
uv add pgvector sentence-transformers
uv add firebase-admin cloudflare boto3
uv add pytest pytest-asyncio httpx --dev

# Generate requirements.txt for Docker
uv pip compile pyproject.toml -o requirements.txt
```

### 0.3 Backend — FastAPI Entry Point

**`src/backend/app/main.py`**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, twin, messages, drafts, channels
from app.database import engine, check_db_connection, check_redis_connection
from app.config import settings
from app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SELPH API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.selph.ai", "https://selph.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routes under /v1/ — mobile app + web app clients must use this prefix
# Adding /v2/ later is safe; /v1/ clients continue working unchanged
app.include_router(auth.router,     prefix="/v1/auth",     tags=["auth"])
app.include_router(twin.router,     prefix="/v1/twin",     tags=["twin"])
app.include_router(messages.router, prefix="/v1/messages", tags=["messages"])
app.include_router(drafts.router,   prefix="/v1/drafts",   tags=["drafts"])
app.include_router(channels.router, prefix="/v1/channels", tags=["channels"])

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "selph-api",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "db": check_db_connection(),
        "redis": check_redis_connection(),
    }
```

### 0.4 Backend — Config

**`src/backend/app/config.py`**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # Auth
    JWT_PRIVATE_KEY: str        # RS256 private key (PEM)
    JWT_PUBLIC_KEY: str         # RS256 public key (PEM)
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # LLM
    ANTHROPIC_API_KEY: str
    LITELLM_DEFAULT_MODEL: str = "claude-sonnet-4-6"

    # Storage
    CLOUDFLARE_R2_ACCESS_KEY: str
    CLOUDFLARE_R2_SECRET_KEY: str
    CLOUDFLARE_R2_BUCKET: str
    CLOUDFLARE_R2_ENDPOINT: str

    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_SERVICE_ACCOUNT_JSON: str  # JSON string

    # App
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:3000"

    # Feature flags — toggle via Railway env vars, no code deploys needed
    # All off by default; enable per environment as features are ready
    FEATURE_VOICE_CLONE:      bool = False   # Phase 6
    FEATURE_AVATAR_CLONE:     bool = False   # Phase 7
    FEATURE_BATCH_APPROVAL:   bool = False   # Phase 1 expansion
    FEATURE_TWIN_BRIEFING:    bool = False   # Phase 1 expansion
    FEATURE_VIP_OVERRIDE:     bool = False   # Phase 1 expansion
    FEATURE_INSTAGRAM_DM:     bool = False   # Phase 5
    FEATURE_GMAIL:            bool = False   # Phase 5

    class Config:
        env_file = ".env"

settings = Settings()
```

### 0.5 Backend — Database Connection

**`src/backend/app/database.py`**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 0.6 Backend — Dockerfile

**`backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 0.7 Local Docker Compose

**`backend/docker-compose.yml`**
```yaml
version: "3.9"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://selph:selph@postgres:5432/selph
      - REDIS_URL=redis://redis:6379/0
    env_file: .env
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://selph:selph@postgres:5432/selph
      - REDIS_URL=redis://redis:6379/0
    env_file: .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.workers.celery_app worker --loglevel=info -Q default,drafts,channels

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: selph
      POSTGRES_PASSWORD: selph
      POSTGRES_DB: selph
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 0.8 Start Local Dev
```bash
cd src/backend
cp .env.example .env   # fill in your keys
docker-compose up -d
# Visit http://localhost:8000/health → {"status": "ok"}
# Visit http://localhost:8000/docs  → Swagger UI
```

---

## Step 1 — Database Schema
**Time: 3–4 hours**

### 1.1 Setup Alembic
```bash
cd src/backend
alembic init migrations
# Edit migrations/env.py — point to your models and DATABASE_URL
```

**`backend/migrations/env.py`** (key lines to add)
```python
from app.database import Base
from app import models  # imports all models to register them

target_metadata = Base.metadata
```

### 1.2 SQLAlchemy Models

**`src/backend/app/models/user.py`**
```python
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email      = Column(String(255), unique=True, nullable=False, index=True)
    name       = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active  = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**`src/backend/app/models/twin.py`**
```python
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Twin(Base):
    __tablename__ = "twins"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id     = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    is_active   = Column(Boolean, default=True)
    mode        = Column(String(20), default="transparent")  # transparent | private
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

class IdentityProfile(Base):
    __tablename__ = "identity_profiles"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    domain          = Column(String(100))                   # "content creator"
    tone            = Column(String(255))                   # "casual, friendly, humorous"
    vocabulary      = Column(JSON)                          # List[str]
    avg_response_length = Column(Integer, default=80)       # words
    emoji_usage     = Column(Float, default=0.3)            # 0.0-1.0
    topics_known    = Column(JSON)                          # List[str]
    topics_avoided  = Column(JSON)                          # List[str]
    greeting_style  = Column(String(100))                   # "Hey!"
    sign_off_style  = Column(String(100))                   # "Cheers"
    sample_responses = Column(JSON)                         # List[str] - real examples
    voice_model_id  = Column(String(255))                   # Chatterbox model ID (default)
    voice_provider  = Column(String(50), default="chatterbox")
    avatar_model_id = Column(String(255))                   # Linly-Talker model ID (default)
    avatar_provider = Column(String(50), default="linly")
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
```

**`src/backend/app/models/message.py`**
```python
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Message(Base):
    __tablename__ = "messages"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id     = Column(UUID(as_uuid=True), ForeignKey("twins.id"), nullable=False, index=True)
    channel     = Column(String(50), nullable=False)        # instagram_dm | gmail | slack
    sender_id   = Column(String(255))                       # platform-specific sender ID
    sender_name = Column(String(255))
    content     = Column(Text, nullable=False)
    status      = Column(String(50), default="pending")     # pending | processed | expired
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

class Draft(Base):
    __tablename__ = "drafts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id      = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    twin_id         = Column(UUID(as_uuid=True), ForeignKey("twins.id"), nullable=False, index=True)
    content         = Column(Text, nullable=False)
    confidence      = Column(Float, nullable=False)          # 0.0-1.0
    confidence_label = Column(String(20))                   # high | medium | low
    status          = Column(String(50), default="pending_approval")
    # pending_approval | approved | edited | rejected | expired
    edited_content  = Column(Text)                          # if user edited before sending
    rejection_reason = Column(Text)
    expires_at      = Column(DateTime(timezone=True))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
```

**`src/backend/app/models/audit.py`**
```python
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    twin_id         = Column(UUID(as_uuid=True), ForeignKey("twins.id"), nullable=False, index=True)
    action          = Column(String(100), nullable=False)    # draft_generated | approved | edited | rejected
    channel         = Column(String(50))
    sender_id_hash  = Column(String(64))                    # SHA-256, not raw
    incoming_hash   = Column(String(64))                    # SHA-256
    draft_hash      = Column(String(64))                    # SHA-256
    confidence      = Column(Float)
    user_action     = Column(String(50))                    # approved | edited | rejected | skipped
    twin_version    = Column(String(50))                    # profile snapshot ID
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
```

**`src/backend/app/models/identity_samples.py`**
```python
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.sql import func
from app.database import Base
import uuid

class IdentitySample(Base):
    __tablename__ = "identity_samples"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    profile_id  = Column(UUID(as_uuid=True), ForeignKey("identity_profiles.id"), nullable=False, index=True)
    channel     = Column(String(50))                        # instagram | gmail | questionnaire
    incoming    = Column(Text)                              # what was received
    response    = Column(Text)                              # what they replied
    source      = Column(String(50))                        # historical | approved | style_aggregate
    quality_score = Column(Float, default=0.5)
    embedding   = Column(Vector(1536))                      # text-embedding-3-small
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
```

### 1.3 Enable pgvector & Run Migration
```bash
# Enable pgvector in PostgreSQL (run once via psql or migration)
# Add to your first migration file:
# op.execute("CREATE EXTENSION IF NOT EXISTS vector")

alembic revision --autogenerate -m "initial_schema"
alembic upgrade head

# Verify tables exist
docker-compose exec postgres psql -U selph -d selph -c "\dt"
```

---

## Step 2 — Auth System
**Time: 4–5 hours**

### 2.1 JWT RS256 Key Generation
```bash
# Generate RSA key pair (run once, store in .env)
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# Copy these into .env as single-line strings (replace newlines with \n)
```

### 2.2 Auth Router

**`src/backend/app/routers/auth.py`**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.database import get_db
from app.models.user import User
from app.models.twin import Twin
from app.config import settings
from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"])

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.JWT_PRIVATE_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=req.email,
        name=req.name,
        password_hash=pwd_context.hash(req.password)
    )
    db.add(user)
    db.flush()  # get user.id

    # Create twin record automatically
    twin = Twin(user_id=user.id)
    db.add(twin)
    db.commit()

    return {"token": create_token(str(user.id)), "user_id": str(user.id), "name": user.name}

@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not pwd_context.verify(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": create_token(str(user.id)), "user_id": str(user.id), "name": user.name}
```

### 2.3 Auth Middleware

**`src/backend/app/middleware/auth.py`**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings

bearer = HTTPBearer()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

---

## Step 3 — Twin Engine
**Time: 6–8 hours**

### 3.1 Celery Setup

**`src/backend/app/workers/celery_app.py`**
```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "selph",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_routes={
        # Each queue can be scaled independently on Railway
        # or extracted into its own worker service later
        "app.workers.draft_tasks.*":   {"queue": "drafts"},    # text LLM work
        "app.workers.channel_tasks.*": {"queue": "channels"},  # I/O bound, API calls
        "app.workers.voice_tasks.*":   {"queue": "voice"},     # Phase 6: GPU, slow
        "app.workers.avatar_tasks.*":  {"queue": "avatar"},    # Phase 7: GPU, slow
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_acks_late=True,             # don't lose tasks on worker crash
    worker_prefetch_multiplier=1,    # one task at a time per worker (safe for GPU)
)
```

### 3.2 Draft Generation Task

**`src/backend/app/workers/draft_tasks.py`**
```python
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models.message import Message, Draft
from app.models.twin import IdentityProfile
from app.services.twin_engine import run_twin_pipeline
from app.services.moderation import moderate_draft
from app.services.confidence import score_confidence
from app.services.notifications import send_draft_ready
from datetime import datetime, timedelta, timezone
import uuid

@celery_app.task(queue="drafts", max_retries=3, default_retry_delay=30)
def process_message(message_id: str):
    db = SessionLocal()
    try:
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            return

        profile = db.query(IdentityProfile).filter(
            IdentityProfile.user_id == message.twin.user_id
        ).first()

        # Generate draft — calls run_twin_pipeline() boundary, not generate_draft() directly
        draft_content = run_twin_pipeline(message, profile)

        # Moderate
        mod_result = moderate_draft(draft_content)
        if not mod_result.passed:
            message.status = "moderation_failed"
            db.commit()
            return

        # Score confidence
        confidence = score_confidence(draft_content, profile, message.content)
        label = "high" if confidence >= 0.85 else "medium" if confidence >= 0.65 else "low"

        # Store draft
        draft = Draft(
            id=uuid.uuid4(),
            message_id=message.id,
            twin_id=message.twin_id,
            content=draft_content,
            confidence=confidence,
            confidence_label=label,
            status="pending_approval",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(draft)
        message.status = "processed"
        db.commit()

        # Notify user
        send_draft_ready(message.twin.user_id, draft.id, message.sender_name, message.channel)

    except Exception as e:
        db.rollback()
        raise process_message.retry(exc=e)
    finally:
        db.close()
```

### 3.3 Twin Engine Service

**`src/backend/app/services/twin_engine.py`**
```python
import litellm
from app.config import settings
from app.models.message import Message, Draft
from app.models.twin import IdentityProfile

litellm.set_verbose = False

# ─── Microservice extraction boundary ────────────────────────────────────────
# Celery tasks call run_twin_pipeline() only — never generate_draft() directly.
# When Twin Engine becomes its own service, this function becomes an HTTP call.
# Celery task code stays identical.
def run_twin_pipeline(message: Message, profile: IdentityProfile) -> str:
    """
    MVP: single LiteLLM call.
    Phase 3: replace internals with LangGraph StateGraph.
    Phase 4: replace entire function body with HTTP call to twin-engine service.
    Callers never change.
    """
    return generate_draft(message, profile)
# ─────────────────────────────────────────────────────────────────────────────

def generate_draft(message: Message, profile: IdentityProfile) -> str:
    CHANNEL_CONTEXT = {
        "instagram_dm": {"style": "casual, short, emoji-friendly", "max_len": 150},
        "gmail":        {"style": "professional, structured",       "max_len": 300},
    }
    channel_ctx = CHANNEL_CONTEXT.get(message.channel, {"style": "natural", "max_len": 200})

    emoji_desc = "frequent" if (profile.emoji_usage or 0) > 0.5 else "minimal"
    samples = "\n".join(
        [f'  - "{s}"' for s in (profile.sample_responses or [])[:5]]
    )

    system_prompt = f"""You are the digital twin of {profile.user.name if hasattr(profile, 'user') else 'the user'}.

Your communication style:
- Tone: {profile.tone or 'friendly and natural'}
- Average response length: {profile.avg_response_length or 80} words
- Emoji usage: {emoji_desc}
- Greeting style: {profile.greeting_style or 'Hey!'}
- Topics you know well: {', '.join(profile.topics_known or [])}
- Topics you never discuss: {', '.join(profile.topics_avoided or [])}
- Channel style: {channel_ctx['style']}
- Max length: {channel_ctx['max_len']} words

Real examples of how they respond:
{samples or '  (No examples yet — use the style description above)'}

RULES:
1. Write ONLY the response — no explanations, no meta-commentary
2. Match their natural voice exactly — do not sound like AI
3. Keep within the max length for this channel
4. Never discuss topics marked as avoided
5. If genuinely unsure, say "Let me check and get back to you!"
6. Match the energy level of the incoming message"""

    user_prompt = f"""Incoming message from {message.sender_name} on {message.channel}:
"{message.content}"

Draft a response."""

    response = litellm.completion(
        model=settings.LITELLM_DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt}
        ],
        max_tokens=500,
        temperature=0.7,
        api_key=settings.ANTHROPIC_API_KEY
    )

    return response.choices[0].message.content.strip()
```

### 3.4 Confidence Scoring

**`src/backend/app/services/confidence.py`**
```python
def score_confidence(draft: str, profile, incoming: str) -> float:
    scores = {}

    # 1. Length match (0-1)
    target = profile.avg_response_length or 80
    draft_words = len(draft.split())
    length_ratio = min(draft_words, target) / max(draft_words, target)
    scores["length"] = length_ratio * 0.20

    # 2. No avoided topics (0-1)
    avoided = [t.lower() for t in (profile.topics_avoided or [])]
    draft_lower = draft.lower()
    avoided_hit = any(t in draft_lower for t in avoided)
    scores["no_avoided"] = 0.0 if avoided_hit else 0.25

    # 3. Known topics confidence (0-1)
    known = [t.lower() for t in (profile.topics_known or [])]
    incoming_lower = incoming.lower()
    topic_match = any(t in incoming_lower for t in known) if known else True
    scores["known_topic"] = 0.25 if topic_match else 0.10

    # 4. Sample vocabulary overlap (0-1)
    vocab = set((profile.vocabulary or []))
    draft_words_set = set(draft.lower().split())
    overlap = len(vocab & draft_words_set) / max(len(vocab), 1)
    scores["vocab"] = min(overlap * 5, 1.0) * 0.15

    # 5. Tone detection placeholder (0-1) — full NLP in Phase 3
    scores["tone"] = 0.15

    return round(sum(scores.values()), 3)
```

### 3.5 Moderation Service

**`src/backend/app/services/moderation.py`**
```python
from dataclasses import dataclass
from typing import List

BLOCKED_PATTERNS = [
    ("financial_advice", ["invest in", "buy stock", "guaranteed return", "financial advice"]),
    ("legal_advice",     ["legal advice", "you should sue", "consult a lawyer"]),
    ("medical_advice",   ["take this medication", "medical advice", "diagnosis"]),
    ("harmful_content",  ["kill", "harm", "attack", "violence"]),
]

@dataclass
class ModerationResult:
    passed: bool
    flags: List[str]

def moderate_draft(draft: str) -> ModerationResult:
    draft_lower = draft.lower()
    flags = []

    for category, patterns in BLOCKED_PATTERNS:
        if any(p in draft_lower for p in patterns):
            flags.append(category)

    return ModerationResult(passed=len(flags) == 0, flags=flags)
```

---

## Step 3b — Channel Adapters
**Time: 2 hours**

### 3b.1 Abstract Base

**`src/backend/app/channels/base.py`**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

@dataclass
class NormalizedMessage:
    """Platform-agnostic message — twin engine never sees raw platform payloads."""
    channel: str
    sender_id: str
    sender_name: str
    content: str
    platform_message_id: str
    raw: dict           # original payload, stored for debugging

class ChannelAdapter(ABC):
    """
    One adapter per integration. Adding a new channel = one new file.
    Twin engine, workers, and routers never change.
    """
    @abstractmethod
    def parse_incoming(self, raw_payload: dict) -> Optional[NormalizedMessage]:
        """Parse raw webhook payload into NormalizedMessage. Return None to ignore."""
        ...

    @abstractmethod
    def send_reply(self, sender_id: str, content: str, credentials: dict) -> bool:
        """Send approved draft back to sender on the platform."""
        ...

    @abstractmethod
    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        """Verify the webhook signature from the platform."""
        ...
```

### 3b.2 Instagram Adapter

**`src/backend/app/channels/instagram.py`**
```python
import hmac, hashlib
from app.channels.base import ChannelAdapter, NormalizedMessage
import httpx

class InstagramAdapter(ChannelAdapter):
    GRAPH_API = "https://graph.instagram.com/v21.0"

    def parse_incoming(self, raw_payload: dict):
        try:
            entry  = raw_payload["entry"][0]
            msg    = entry["messaging"][0]
            sender = msg["sender"]["id"]
            text   = msg.get("message", {}).get("text")
            if not text:
                return None
            return NormalizedMessage(
                channel="instagram_dm",
                sender_id=sender,
                sender_name=sender,       # resolved separately if needed
                content=text,
                platform_message_id=msg["message"]["mid"],
                raw=raw_payload,
            )
        except (KeyError, IndexError):
            return None

    def send_reply(self, sender_id: str, content: str, credentials: dict) -> bool:
        r = httpx.post(
            f"{self.GRAPH_API}/me/messages",
            params={"access_token": credentials["page_access_token"]},
            json={"recipient": {"id": sender_id}, "message": {"text": content}},
        )
        return r.status_code == 200

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        sig = headers.get("x-hub-signature-256", "").removeprefix("sha256=")
        secret = headers.get("_app_secret", "")   # injected by router, not from client
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)
```

### 3b.3 Gmail Adapter

**`src/backend/app/channels/gmail.py`**
```python
import base64
from app.channels.base import ChannelAdapter, NormalizedMessage
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

class GmailAdapter(ChannelAdapter):

    def parse_incoming(self, raw_payload: dict):
        """raw_payload is the Pub/Sub push message body."""
        try:
            data = base64.b64decode(raw_payload["message"]["data"]).decode()
            # data = JSON with emailAddress + historyId
            # Full email fetched separately via Gmail API
            return NormalizedMessage(
                channel="gmail",
                sender_id=raw_payload.get("emailAddress", ""),
                sender_name=raw_payload.get("emailAddress", ""),
                content="",            # populated after Gmail API fetch
                platform_message_id=str(raw_payload.get("historyId", "")),
                raw=raw_payload,
            )
        except Exception:
            return None

    def send_reply(self, sender_id: str, content: str, credentials: dict) -> bool:
        creds = Credentials(token=credentials["access_token"])
        service = build("gmail", "v1", credentials=creds)
        # Build RFC 2822 email + send via Gmail API
        import email.mime.text, base64
        msg = email.mime.text.MIMEText(content)
        msg["to"] = sender_id
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True

    def verify_webhook(self, headers: dict, body: bytes) -> bool:
        # Pub/Sub push subscriptions use OIDC token auth — verified at router level
        return True
```

### 3b.4 Channel Registry

**`src/backend/app/channels/registry.py`**
```python
from app.channels.base import ChannelAdapter
from app.channels.instagram import InstagramAdapter
from app.channels.gmail import GmailAdapter

_registry: dict[str, ChannelAdapter] = {
    "instagram_dm": InstagramAdapter(),
    "gmail":        GmailAdapter(),
    # "whatsapp":  WhatsAppAdapter(),   # Phase 2 — add one line here
    # "slack":     SlackAdapter(),      # Phase 2
    # "github":    GitHubAdapter(),     # Wave 3
}

def get_adapter(channel: str) -> ChannelAdapter:
    adapter = _registry.get(channel)
    if not adapter:
        raise ValueError(f"No adapter registered for channel: {channel}")
    return adapter
```

---

## Step 3c — Service Registry
**Time: 1 hour**

This is the internal interface layer. When a service is extracted to a microservice,
only `registry.py` changes — no other file needs updating.

**`src/backend/app/services/registry.py`**
```python
"""
Service Registry — internal interface layer.

All cross-service calls go through here, never via direct import.

MVP: all calls are local function calls (fast, zero overhead).
Future: swap individual service entries for HTTP clients when extracted.

Usage:
    from app.services.registry import services
    profile = services.identity.get_profile(user_id)
"""
from app.services import identity, twin_engine, moderation, notifications

class _IdentityService:
    def get_profile(self, user_id: str):
        return identity.get_profile(user_id)

    def update_from_feedback(self, profile_id: str, action: str, diff: dict):
        return identity.update_from_feedback(profile_id, action, diff)

class _TwinEngineService:
    def run_pipeline(self, message, profile):
        return twin_engine.run_twin_pipeline(message, profile)

class _ModerationService:
    def check(self, draft: str):
        return moderation.moderate_draft(draft)

class _NotificationService:
    def draft_ready(self, user_id: str, draft_id: str, sender_name: str, channel: str):
        return notifications.send_draft_ready(user_id, draft_id, sender_name, channel)

class ServiceRegistry:
    identity     = _IdentityService()
    twin_engine  = _TwinEngineService()
    moderation   = _ModerationService()
    notification = _NotificationService()

services = ServiceRegistry()
```

---

## Step 3d — Voice & Avatar Placeholders
**Time: 30 minutes**

Queues defined now, tasks wired up in Phase 6 & 7. No-ops until then.

**`src/backend/app/workers/voice_tasks.py`**
```python
"""
Voice processing tasks — Phase 6.

Queue: voice
Worker: can run on GPU Railway instance independently of API/draft workers.

Extraction path:
  Phase 6: implement tasks here (Chatterbox / ElevenLabs)
  Phase 6+: if voice needs GPU isolation, move this file to services/voice/
            and update celery_app.py broker URL to point at voice service Redis
"""
from app.workers.celery_app import celery_app

@celery_app.task(queue="voice")
def generate_voice_response(draft_id: str, user_id: str):
    """Generate audio from approved draft text using user's voice model."""
    # TODO Phase 6: implement Chatterbox (default) / ElevenLabs (premium) call
    raise NotImplementedError("Voice clone — Phase 6")

@celery_app.task(queue="voice")
def train_voice_model(user_id: str, audio_r2_key: str):
    """Train user's voice model from uploaded recording."""
    # TODO Phase 6: implement Chatterbox training pipeline
    raise NotImplementedError("Voice training — Phase 6")
```

**`src/backend/app/workers/avatar_tasks.py`**
```python
"""
Avatar processing tasks — Phase 7.

Queue: avatar
Worker: GPU required — separate Railway service with GPU instance.

Extraction path:
  Phase 7: implement tasks here (Linly-Talker / HeyGen)
  Phase 7+: move to services/avatar/ with its own Dockerfile.gpu
"""
from app.workers.celery_app import celery_app

@celery_app.task(queue="avatar")
def generate_avatar_video(draft_id: str, user_id: str):
    """Generate talking-head video from approved draft text."""
    # TODO Phase 7: implement Linly-Talker (default) / HeyGen (premium) call
    raise NotImplementedError("Avatar video — Phase 7")

@celery_app.task(queue="avatar")
def train_avatar_model(user_id: str, video_r2_key: str):
    """Train user's avatar model from uploaded video."""
    # TODO Phase 7: implement Linly-Talker training pipeline
    raise NotImplementedError("Avatar training — Phase 7")
```

---

## Step 4 — API Routes
**Time: 4–5 hours**

### 4.1 Twin Router

**`src/backend/app/routers/twin.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.models.twin import Twin, IdentityProfile

router = APIRouter()

@router.get("/me")
def get_my_twin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    twin = db.query(Twin).filter(Twin.user_id == user_id).first()
    if not twin:
        raise HTTPException(status_code=404, detail="Twin not found")
    return {
        "id": str(twin.id),
        "is_active": twin.is_active,
        "mode": twin.mode,
        "created_at": twin.created_at.isoformat()
    }

@router.post("/pause")
def pause_twin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    twin = db.query(Twin).filter(Twin.user_id == user_id).first()
    twin.is_active = False
    db.commit()
    return {"status": "paused"}

@router.post("/resume")
def resume_twin(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    twin = db.query(Twin).filter(Twin.user_id == user_id).first()
    twin.is_active = True
    db.commit()
    return {"status": "active"}
```

### 4.2 Drafts Router

**`src/backend/app/routers/drafts.py`**
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.models.message import Draft, Message
from app.models.twin import Twin
from app.models.audit import AuditLog
from pydantic import BaseModel
from typing import Optional
import hashlib, uuid

router = APIRouter()

class DraftActionRequest(BaseModel):
    action: str             # approve | edit | reject | skip
    edited_content: Optional[str] = None
    rejection_reason: Optional[str] = None

@router.get("/pending")
def get_pending_drafts(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    twin = db.query(Twin).filter(Twin.user_id == user_id).first()
    drafts = db.query(Draft).filter(
        Draft.twin_id == twin.id,
        Draft.status == "pending_approval"
    ).all()
    return [_format_draft(d, db) for d in drafts]

@router.post("/{draft_id}/action")
def act_on_draft(
    draft_id: str,
    req: DraftActionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if req.action == "approve":
        draft.status = "approved"
    elif req.action == "edit":
        if not req.edited_content:
            raise HTTPException(status_code=400, detail="edited_content required")
        draft.status = "edited"
        draft.edited_content = req.edited_content
    elif req.action == "reject":
        draft.status = "rejected"
        draft.rejection_reason = req.rejection_reason
    elif req.action == "skip":
        draft.status = "skipped"

    # Audit log
    message = db.query(Message).filter(Message.id == draft.message_id).first()
    log = AuditLog(
        id=uuid.uuid4(),
        twin_id=draft.twin_id,
        action=req.action,
        channel=message.channel if message else None,
        sender_id_hash=hashlib.sha256((message.sender_id or "").encode()).hexdigest() if message else None,
        incoming_hash=hashlib.sha256((message.content or "").encode()).hexdigest() if message else None,
        draft_hash=hashlib.sha256(draft.content.encode()).hexdigest(),
        confidence=draft.confidence,
        user_action=req.action,
        twin_version="1.0"
    )
    db.add(log)
    db.commit()

    return {"status": "ok", "draft_status": draft.status}

def _format_draft(draft: Draft, db: Session) -> dict:
    message = db.query(Message).filter(Message.id == draft.message_id).first()
    return {
        "id": str(draft.id),
        "content": draft.content,
        "confidence": draft.confidence,
        "confidence_label": draft.confidence_label,
        "status": draft.status,
        "channel": message.channel if message else None,
        "sender_name": message.sender_name if message else None,
        "incoming_message": message.content if message else None,
        "created_at": draft.created_at.isoformat(),
        "expires_at": draft.expires_at.isoformat() if draft.expires_at else None,
    }
```

---

## Step 5 — Web App (Next.js)
**Time: 8–10 hours**

### 5.1 Create Next.js App
```bash
cd selph-ai/src
npx create-next-app@latest web \
  --typescript --tailwind --app --src-dir=false --import-alias="@/*"
cd web
npm install framer-motion lucide-react @radix-ui/react-dialog
npm install recharts clsx tailwind-merge
```

### 5.2 Tailwind Config — Design Tokens

**`web/tailwind.config.ts`** (extend section)
```typescript
extend: {
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
    },
    approve: '#10B981',
    edit:    '#F59E0B',
    reject:  '#EF4444',
  },
  borderRadius: {
    '4': '16px', '6': '24px', '8': '32px',
  },
  boxShadow: {
    'card':    '0 4px 24px rgba(124,58,237,0.08), 0 1px 4px rgba(0,0,0,0.04)',
    'lifted':  '0 8px 40px rgba(124,58,237,0.14), 0 2px 8px rgba(0,0,0,0.06)',
    'float':   '0 16px 64px rgba(124,58,237,0.20), 0 4px 16px rgba(0,0,0,0.08)',
  },
  fontFamily: {
    sans: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
}
```

### 5.3 API Client

**`src/web/lib/api.ts`**
```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('selph_token')
  // All API calls go to /v1/* — matches backend router prefix
  const res = await fetch(`${BASE_URL}/v1${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const api = {
  auth: {
    // request() prepends /v1/ automatically — paths here are relative to /v1/
    signup: (data: { name: string; email: string; password: string }) =>
      request('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  },
  twin: {
    getMe:  () => request('/twin/me'),
    pause:  () => request('/twin/pause',  { method: 'POST' }),
    resume: () => request('/twin/resume', { method: 'POST' }),
  },
  drafts: {
    getPending: () => request('/drafts/pending'),
    action: (id: string, action: string, editedContent?: string, reason?: string) =>
      request(`/drafts/${id}/action`, {
        method: 'POST',
        body: JSON.stringify({ action, edited_content: editedContent, rejection_reason: reason }),
      }),
  },
  channels: {
    connect:    (channel: string) => request(`/channels/${channel}/connect`,    { method: 'POST' }),
    disconnect: (channel: string) => request(`/channels/${channel}/disconnect`, { method: 'POST' }),
  },
}
```

### 5.4 Dashboard Page

**`src/web/app/dashboard/page.tsx`**
```tsx
'use client'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '@/lib/api'
import DraftCard from '@/components/twin/DraftCard'

export default function Dashboard() {
  const [drafts, setDrafts] = useState([])
  const [twin, setTwin]     = useState<any>(null)

  useEffect(() => {
    api.twin.getMe().then(setTwin)
    api.drafts.getPending().then(setDrafts)
  }, [])

  const handleAction = async (id: string, action: string, edited?: string) => {
    await api.drafts.action(id, action, edited)
    setDrafts(prev => prev.filter((d: any) => d.id !== id))
  }

  return (
    <div className="min-h-screen bg-[#FAFAF9] p-10">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-slate-900">
          Good morning 👋
        </h1>
        <p className="text-slate-500 mt-1">
          {drafts.length > 0
            ? `${drafts.length} draft${drafts.length > 1 ? 's' : ''} need your attention`
            : 'Your twin is all caught up'}
        </p>
      </motion.div>

      {/* Twin status chip */}
      {twin && (
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full
          bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm font-medium mb-8">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Twin {twin.is_active ? 'Active' : 'Paused'}
        </div>
      )}

      {/* Draft Feed */}
      <div className="space-y-4">
        {drafts.length === 0 && (
          <div className="text-center py-20 text-slate-400">
            No pending drafts — your twin is on it ✓
          </div>
        )}
        {drafts.map((draft: any, i: number) => (
          <motion.div
            key={draft.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
          >
            <DraftCard draft={draft} onAction={handleAction} />
          </motion.div>
        ))}
      </div>
    </div>
  )
}
```

### 5.5 Draft Card Component

**`src/web/components/twin/DraftCard.tsx`**
```tsx
'use client'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Pencil, X } from 'lucide-react'

const CHANNEL_COLORS: Record<string, string> = {
  instagram_dm: '#F43F5E',
  gmail:        '#7C3AED',
  slack:        '#F97316',
}

export default function DraftCard({ draft, onAction }: {
  draft: any
  onAction: (id: string, action: string, edited?: string) => void
}) {
  const [editing, setEditing] = useState(false)
  const [editedText, setEditedText] = useState(draft.content)
  const borderColor = CHANNEL_COLORS[draft.channel] || '#7C3AED'
  const confidencePct = Math.round(draft.confidence * 100)

  return (
    <div
      className="bg-white rounded-[24px] shadow-card border border-slate-100 overflow-hidden"
      style={{ borderLeft: `4px solid ${borderColor}` }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-6 pt-5 pb-3">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {draft.channel?.replace('_', ' ')}
          </span>
          <p className="font-semibold text-slate-900 mt-0.5">
            {draft.sender_name}
          </p>
        </div>
        <ConfidenceRing pct={confidencePct} />
      </div>

      <div className="px-6 pb-4 space-y-3">
        {/* Incoming */}
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Received
          </span>
          <p className="text-slate-600 text-sm mt-1 bg-slate-50 rounded-xl p-3">
            {draft.incoming_message}
          </p>
        </div>

        {/* Draft */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider"
              style={{ color: borderColor }}>
              Twin Draft
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium
              ${draft.confidence_label === 'high'   ? 'bg-emerald-50 text-emerald-600' :
                draft.confidence_label === 'medium' ? 'bg-amber-50 text-amber-600' :
                                                      'bg-red-50 text-red-500'}`}>
              {draft.confidence_label}
            </span>
          </div>
          {editing ? (
            <textarea
              className="w-full rounded-xl border-2 border-selph-violet p-3 text-sm
                text-slate-800 resize-none focus:outline-none"
              rows={4}
              value={editedText}
              onChange={e => setEditedText(e.target.value)}
            />
          ) : (
            <p className="text-slate-800 text-sm bg-violet-50 rounded-xl p-3">
              {draft.content}
            </p>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3 px-6 pb-5">
        {editing ? (
          <>
            <button
              onClick={() => { onAction(draft.id, 'edit', editedText); setEditing(false) }}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl
                bg-gradient-to-r from-amber-400 to-orange-400 text-white font-semibold text-sm"
            >
              <Check size={16} /> Send Edited
            </button>
            <button
              onClick={() => setEditing(false)}
              className="px-4 py-3 rounded-xl border-2 border-slate-200 text-slate-500 text-sm"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => onAction(draft.id, 'approve')}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl
                bg-gradient-to-r from-emerald-400 to-cyan-400 text-white font-semibold text-sm
                hover:shadow-lg hover:-translate-y-0.5 transition-all"
            >
              <Check size={16} /> Approve
            </button>
            <button
              onClick={() => setEditing(true)}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl
                bg-gradient-to-r from-amber-400 to-orange-400 text-white font-semibold text-sm
                hover:shadow-lg hover:-translate-y-0.5 transition-all"
            >
              <Pencil size={16} /> Edit
            </button>
            <button
              onClick={() => onAction(draft.id, 'reject')}
              className="px-4 py-3 rounded-xl border-2 border-red-200 text-red-400
                hover:bg-red-50 transition-all text-sm"
            >
              <X size={16} />
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function ConfidenceRing({ pct }: { pct: number }) {
  const r = 16, c = 2 * Math.PI * r
  const offset = c - (pct / 100) * c
  const color = pct >= 85 ? '#10B981' : pct >= 65 ? '#F59E0B' : '#EF4444'

  return (
    <div className="relative w-10 h-10 flex items-center justify-center">
      <svg width="40" height="40" className="-rotate-90">
        <circle cx="20" cy="20" r={r} fill="none" stroke="#F1F5F9" strokeWidth="3" />
        <motion.circle
          cx="20" cy="20" r={r} fill="none" stroke={color} strokeWidth="3"
          strokeLinecap="round" strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 0.8, ease: 'easeOut', delay: 0.3 }}
        />
      </svg>
      <span className="absolute text-[10px] font-bold" style={{ color }}>
        {pct}%
      </span>
    </div>
  )
}
```

---

## Step 6 — Mobile App (React Native)
**Time: 6–8 hours**

### 6.1 Create Expo App
```bash
cd selph-ai/src
npx create-expo-app mobile --template expo-template-blank-typescript
cd mobile
npx expo install expo-router react-native-reanimated react-native-gesture-handler
npx expo install expo-notifications @react-native-async-storage/async-storage
npm install nativewind
npm install framer-motion  # for web; Reanimated for native
```

### 6.2 Mobile Draft Card (React Native)

**`src/mobile/components/DraftCard.tsx`**
```tsx
import React, { useState } from 'react'
import { View, Text, TouchableOpacity, StyleSheet, TextInput } from 'react-native'
import Animated, {
  useSharedValue, useAnimatedStyle, withSpring, runOnJS
} from 'react-native-reanimated'
import { GestureDetector, Gesture } from 'react-native-gesture-handler'

const CHANNEL_COLORS: Record<string, string> = {
  instagram_dm: '#F43F5E',
  gmail:        '#7C3AED',
  slack:        '#F97316',
}

export default function DraftCard({ draft, onAction }: any) {
  const [editing, setEditing] = useState(false)
  const [editedText, setEditedText] = useState(draft.content)
  const translateX = useSharedValue(0)
  const borderColor = CHANNEL_COLORS[draft.channel] || '#7C3AED'

  const swipeGesture = Gesture.Pan()
    .onUpdate(e => { translateX.value = e.translationX })
    .onEnd(e => {
      if (e.translationX > 100) {
        translateX.value = withSpring(500)
        runOnJS(onAction)(draft.id, 'approve')
      } else if (e.translationX < -100) {
        translateX.value = withSpring(-500)
        runOnJS(onAction)(draft.id, 'reject')
      } else {
        translateX.value = withSpring(0)
      }
    })

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }]
  }))

  return (
    <GestureDetector gesture={swipeGesture}>
      <Animated.View style={[styles.card, { borderLeftColor: borderColor }, animatedStyle]}>
        {/* Channel + sender */}
        <View style={styles.header}>
          <Text style={styles.channel}>{draft.channel?.replace('_', ' ')}</Text>
          <Text style={styles.sender}>{draft.sender_name}</Text>
        </View>

        {/* Incoming */}
        <View style={styles.bubble}>
          <Text style={styles.bubbleLabel}>Received</Text>
          <Text style={styles.bubbleText}>{draft.incoming_message}</Text>
        </View>

        {/* Draft */}
        <View style={[styles.bubble, { backgroundColor: '#F5F3FF' }]}>
          <Text style={[styles.bubbleLabel, { color: borderColor }]}>Twin Draft · {Math.round(draft.confidence * 100)}%</Text>
          {editing
            ? <TextInput
                style={styles.editInput}
                multiline
                value={editedText}
                onChangeText={setEditedText}
              />
            : <Text style={styles.bubbleText}>{draft.content}</Text>
          }
        </View>

        {/* Actions */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[styles.btn, styles.approveBtn]}
            onPress={() => onAction(draft.id, 'approve')}
          >
            <Text style={styles.btnText}>✓ Approve</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.editBtn]}
            onPress={() => editing ? onAction(draft.id, 'edit', editedText) : setEditing(true)}
          >
            <Text style={styles.btnText}>{editing ? 'Send' : '✎ Edit'}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.btn, styles.rejectBtn]}
            onPress={() => onAction(draft.id, 'reject')}
          >
            <Text style={[styles.btnText, { color: '#EF4444' }]}>✕</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.swipeHint}>← swipe to reject · swipe to approve →</Text>
      </Animated.View>
    </GestureDetector>
  )
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff', borderRadius: 20, marginHorizontal: 16,
    marginBottom: 12, borderLeftWidth: 4, overflow: 'hidden',
    shadowColor: '#7C3AED', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.10, shadowRadius: 16, elevation: 4,
  },
  header: { padding: 16, paddingBottom: 8 },
  channel: { fontSize: 11, fontWeight: '600', color: '#94A3B8', textTransform: 'uppercase', letterSpacing: 1 },
  sender: { fontSize: 16, fontWeight: '700', color: '#0F172A', marginTop: 2 },
  bubble: { marginHorizontal: 16, marginBottom: 10, backgroundColor: '#F8FAFC', borderRadius: 12, padding: 12 },
  bubbleLabel: { fontSize: 10, fontWeight: '700', color: '#94A3B8', textTransform: 'uppercase', marginBottom: 4 },
  bubbleText: { fontSize: 14, color: '#334155', lineHeight: 20 },
  editInput: { fontSize: 14, color: '#334155', minHeight: 80, borderWidth: 2, borderColor: '#7C3AED', borderRadius: 8, padding: 8 },
  actions: { flexDirection: 'row', gap: 8, paddingHorizontal: 16, paddingBottom: 8 },
  btn: { flex: 1, paddingVertical: 14, borderRadius: 12, alignItems: 'center' },
  approveBtn: { backgroundColor: '#10B981' },
  editBtn:    { backgroundColor: '#F59E0B' },
  rejectBtn:  { backgroundColor: '#FEF2F2', borderWidth: 1, borderColor: '#FECACA' },
  btnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  swipeHint: { textAlign: 'center', fontSize: 10, color: '#CBD5E1', paddingBottom: 12 },
})
```

---

## Step 7 — Railway Deployment
**Time: 2–3 hours**

### 7.1 Deploy Backend to Railway
```bash
# Login
railway login

# Create project
railway init --name selph-ai

# Add services
railway add --service postgresql   # Railway managed PostgreSQL
railway add --service redis        # Railway managed Redis

# Link local backend to Railway
cd src/backend
railway link

# Set environment variables in Railway dashboard (or CLI):
railway variables set ANTHROPIC_API_KEY=sk-...
railway variables set CLOUDFLARE_R2_ACCESS_KEY=...
railway variables set CLOUDFLARE_R2_SECRET_KEY=...
railway variables set CLOUDFLARE_R2_BUCKET=selph-assets
railway variables set CLOUDFLARE_R2_ENDPOINT=https://YOUR_ACCOUNT.r2.cloudflarestorage.com
railway variables set FIREBASE_PROJECT_ID=selph-ai
railway variables set JWT_PRIVATE_KEY="$(cat private.pem)"
railway variables set JWT_PUBLIC_KEY="$(cat public.pem)"

# Deploy
railway up

# Get your API URL
railway open
# → selph-api-production.up.railway.app
```

### 7.2 Deploy Worker to Railway
```bash
# In Railway dashboard: add another service from same repo
# Set Start Command: celery -A app.workers.celery_app worker --loglevel=info
# Share same env vars as API service
```

### 7.3 Run Migrations on Railway
```bash
# One-time migration run (via Railway terminal or local with Railway DB URL)
railway run alembic upgrade head
```

### 7.4 Deploy Frontend to Vercel
```bash
cd src/web
npx vercel --prod

# Set env vars in Vercel dashboard:
# NEXT_PUBLIC_API_URL=https://selph-api-production.up.railway.app
```

---

## Step 8 — Cloudflare R2 Setup
**Time: 1 hour**

```bash
# 1. In Cloudflare dashboard: R2 → Create bucket → "selph-assets"
# 2. Create API token with R2 read/write permissions
# 3. Get your account ID + endpoint URL

# 4. Test upload via boto3 (S3-compatible):
python3 -c "
import boto3
r2 = boto3.client('s3',
    endpoint_url='https://YOUR_ACCOUNT.r2.cloudflarestorage.com',
    aws_access_key_id='YOUR_KEY',
    aws_secret_access_key='YOUR_SECRET',
)
r2.put_object(Bucket='selph-assets', Key='test.txt', Body=b'hello SELPH')
print('R2 working!')
"
```

---

## Step 9 — Push Notifications (Firebase)
**Time: 2 hours**

**`src/backend/app/services/notifications.py`**
```python
import firebase_admin
from firebase_admin import credentials, messaging
from app.config import settings
import json

# Initialize Firebase (once on startup)
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON))
    firebase_admin.initialize_app(cred)

def send_draft_ready(user_id: str, draft_id: str, sender_name: str, channel: str):
    """Send push notification when a twin draft is ready for review."""
    # Look up user's FCM token from DB (store during mobile app registration)
    fcm_token = get_user_fcm_token(user_id)
    if not fcm_token:
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=f"{sender_name} messaged you",
            body="Your twin drafted a reply — tap to review",
        ),
        data={
            "draft_id": str(draft_id),
            "channel": channel,
            "action": "review_draft",
        },
        token=fcm_token,
    )
    messaging.send(message)
```

---

## Build Sequence — Day by Day

```
Day 1     ██  Repo setup, Docker, database running locally
Day 2     ██  All DB models + Alembic migration (with table ownership comments)
Day 3     ██  Auth (signup, login, JWT RS256)
Day 4     ██  Channel adapters (base + registry + Instagram + Gmail stubs)
Day 5     ██  Celery app (4 queues) + voice/avatar task placeholders
Day 6     ██  Service registry + run_twin_pipeline() boundary
Day 7     ██  LiteLLM integration + draft generation (hardcoded profile test)
Day 8     ██  Confidence scoring + moderation + draft/twin API routes (/v1/)
Day 9     ██  Identity profile model + onboarding questionnaire API
Day 10    ██  Next.js setup + design tokens + /v1/ API client
Day 11    ██  Dashboard page + DraftCard component
Day 12    ██  Expo mobile setup + home screen + DraftCard native
Day 13    ██  Railway deploy (API + worker) + Vercel deploy frontend
Day 14    ██  Firebase push + end-to-end: message → draft → notify → approve
──────────────────────────────────────────────────────────
Week 3+   Instagram DM webhook (InstagramAdapter.parse_incoming live)
Week 4+   Gmail OAuth + Pub/Sub (GmailAdapter live)
Week 5+   Onboarding + social content ingestion + pgvector embeddings
Week 6+   Demo Day: twin generates, user approves, feedback loop trains profile
Phase 6   voice_tasks.py implemented — Chatterbox default, ElevenLabs premium
Phase 7   avatar_tasks.py implemented — Linly-Talker default, HeyGen premium
Phase 3+  Extract twin-engine or identity to services/ if scaling pain hits
```

---

## Environment Variables Reference

**`backend/.env.example`**
```bash
# Database (Railway provides these automatically)
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://user:pass@host:6379

# Auth
JWT_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n..."
JWT_ALGORITHM=RS256

# LLM
ANTHROPIC_API_KEY=sk-ant-...
LITELLM_DEFAULT_MODEL=claude-sonnet-4-6

# Storage
CLOUDFLARE_R2_ACCESS_KEY=...
CLOUDFLARE_R2_SECRET_KEY=...
CLOUDFLARE_R2_BUCKET=selph-assets
CLOUDFLARE_R2_ENDPOINT=https://ACCOUNT_ID.r2.cloudflarestorage.com

# Firebase
FIREBASE_PROJECT_ID=selph-ai
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}

# App
ENVIRONMENT=development
```

**`web/.env.local.example`**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Definition of Done — Phase 0

Before moving to Phase 1, verify all of these:

```
[ ] docker-compose up starts all services without errors
[ ] GET /health returns {"status": "ok"}
[ ] POST /auth/signup creates user + twin record
[ ] POST /auth/login returns JWT token
[ ] GET /twin/me returns twin status (authenticated)
[ ] Alembic migrations run cleanly on fresh database
[ ] pgvector extension enabled
[ ] Railway backend deployed and returning 200 on /health
[ ] Vercel frontend deployed and loading dashboard page
[ ] Swagger UI at /docs shows all routes
```

---

*Implementation Plan v1.1 — 2026-04-27*
*Changes: /v1/ API prefix, channel adapter pattern, service registry,*
*feature flags, voice/avatar queue placeholders, microservice extraction stubs*
*Next: Phase 1 — Identity Core (social ingestion + profile building)*
