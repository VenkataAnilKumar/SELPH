# GitHub Achievement Workflow

This workflow helps contributions count consistently for GitHub profile achievements while keeping engineering quality high.

## Why Achievements May Not Increase

- Work merged by direct commit to main does not count the same as merged pull requests.
- Some achievements require specific event types, not just code volume.
- GitHub can delay achievement updates.

## Required Team Process

1. Open an issue first when possible.
2. Create a branch from main.
3. Commit to the branch.
4. Open a pull request on GitHub.
5. Merge only through the pull request.

## Branch Naming

- feature/short-description
- fix/short-description
- chore/short-description
- docs/short-description

## Pull Request Rules

- PR title should be clear and action-oriented.
- PR body should include an issue reference when relevant.
- Use closing keywords in PR body:
  - Fixes #123
  - Closes #456
- Avoid direct commits to main for tracked work.

## Suggested Command Flow

```bash
git checkout main
git pull origin main
git checkout -b fix/oauth-state-hardening

# work, test, commit
git add .
git commit -m "fix: harden oauth state validation"
git push -u origin fix/oauth-state-hardening
```

Then open PR in GitHub, include issue reference, and merge from PR UI.

## Achievement-Oriented Notes

### Pull Shark

- Increments from merged pull requests.
- Direct pushes to main are not a substitute.

### Quickdraw

- Depends on close timing after opening an issue or PR.
- Fast, valid resolution with a merge event is required.

### YOLO

- Depends on specific merge and review conditions.
- Team settings and review flow can affect eligibility.

## Quality Guardrails

- Keep full test suite green before merge.
- Keep changes small and focused by issue.
- Prefer one issue to one PR for cleaner audit trail.

## Practical Cadence

- For each phase item, open an issue and resolve via one or more PRs.
- Merge PRs regularly instead of batching all work into direct main commits.
- Keep PR descriptions complete so timeline data is explicit and attributable.
