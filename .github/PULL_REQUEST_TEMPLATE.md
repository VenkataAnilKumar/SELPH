## Summary

Describe what changed and why.

## Related Issue

Use a closing keyword when applicable so GitHub links and closes the issue on merge.

Example:
- Fixes #123
- Closes #456

## Type Of Change

- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Docs
- [ ] Test
- [ ] Security hardening

## Validation

- [ ] Added or updated tests
- [ ] Backend tests pass locally
- [ ] No breaking API changes, or migration steps documented

Commands run:

```bash
cd src/backend
python -m pytest tests/ -q --tb=short
```

## Checklist

- [ ] Branch follows naming convention (feature/, fix/, chore/, docs/)
- [ ] PR title is clear and action-oriented
- [ ] Linked issue included above when relevant
- [ ] No direct commits to main for this change
- [ ] CI checks are green

## Achievement Hygiene

- [ ] This work is merged through a GitHub PR (not direct push)
- [ ] Issue was opened first when possible
- [ ] Issue closing keyword included (Fixes/Closes)
