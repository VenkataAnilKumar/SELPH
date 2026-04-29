# Contributing to SELPH

> SELPH is a proprietary product. Contributions are by invitation only.
> This guide is for the core team and approved collaborators.

---

## Before You Start

- Check open issues and the sprint board before picking up work
- If you have an idea or found a bug, open an issue first — don't jump straight to a PR
- Discuss non-trivial changes in the issue before writing code

---

## Setup

```bash
git clone https://github.com/VenkataAnilKumar/selph.git
cd selph
cp .env.example .env          # add your API keys
docker compose up --build     # starts backend + PostgreSQL + Redis
```

Backend docs live at `http://localhost:8000/docs` once the stack is up.

---

## Branch Naming

```
feature/short-description     new feature
fix/short-description         bug fix
chore/short-description       non-functional (deps, config, docs)
```

Always branch from `main`. Keep branches short-lived.

---

## Commit Style

Follow [Conventional Commits](https://www.conventionalcommits.org):

```
feat: add twin briefing expiry by usage count
fix: resolve confidence score overflow on empty profile
chore: update LiteLLM to 1.42.0
docs: add voice enrollment flow to API design
```

One logical change per commit. Squash fixup commits before merging.

---

## Pull Requests

- Title matches the commit style (`feat:`, `fix:`, etc.)
- Link the issue: `Closes #123`
- Add a short description of what changed and why
- CI must pass before review is requested
- At least one approval required before merge
- Squash merge into `main`

**PR template:**

```
## What
Brief description of the change.

## Why
The problem this solves or the feature it enables.

## How
Key implementation decisions, trade-offs made.

## Testing
How you verified this works (tests added, manual steps, etc.)

Closes #
```

---

## Code Standards

**Python (backend)**
- Follow existing module structure — don't create new patterns without discussion
- Services handle business logic; routers handle HTTP only
- Every new endpoint needs a test in `tests/`
- Run before committing:
  ```bash
  cd src/backend
  pytest tests/ -v
  ```

**TypeScript (web / mobile)**
- Match the existing component patterns
- No `any` types without a comment explaining why
- Run before committing:
  ```bash
  cd src/web && npm run test && npm run lint
  ```

**General**
- No commented-out code in PRs
- No `print()` / `console.log()` left in production paths
- Environment-specific config goes in `.env`, not in code

---

## What Not to Touch

| Area | Reason |
|---|---|
| `docs/04-safety/SELPH_Canonical-Policy-Matrix.md` | Policy changes need Owner sign-off |
| Database migration files once merged | Breaking history causes production issues |
| Voice / avatar provider credentials | Handled separately outside this repo |
| Any `production` branch or tag | Deployment is gated — do not push directly |

---

## Reporting Bugs

Open a GitHub Issue with:

1. **What happened** — exact behavior you observed
2. **What you expected** — what should have happened
3. **Steps to reproduce** — minimal steps, include request/response if API related
4. **Environment** — OS, Python version, Docker version, relevant `.env` values (no secrets)

For security vulnerabilities, **do not open a public issue**. Email `vanilkumarch@gmail.com` directly.

---

## Questions

- Open a GitHub Discussion for anything architectural or directional
- Tag `@VenkataAnilKumar` for anything blocking, or email `vanilkumarch@gmail.com`

---

*SELPH is proprietary software. Contributing does not transfer any ownership rights.*
