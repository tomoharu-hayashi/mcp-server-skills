# Create Commit

Follow the instructions below to create a commit.

## Notes

- Do not push or create a PR (commit only)
- Refer to coding rules when needed
- Watch out for secrets (tokens, keys, personal data, etc.)

## Commit Creation Process

1. **Review changes** — Check changes with `git status` and `git diff HEAD`
2. **Determine commit scope** — Split by decision/logical unit (create multiple commits if needed)
3. **Stage changes** — Use `git add -p` (or `git add <path>`) to stage only what you intend to commit
4. **Review staged diff** — Confirm what will be committed with `git diff --staged`
5. **Create commit** — Write a commit message following the rules below and run `git commit`

## Commit Message Rules

### Prefix

- `feat:` — New feature (app's direct functionality only)
- `fix:` — Bug fix
- `refactor:` — Refactoring
- `docs:` — Documentation
- `test:` — Tests
- `chore:` — Build, CI, dependencies, etc.
- `style:` — Formatting, semicolons, etc.

### Format

```
<prefix>: <concise description in English>
```

### Examples

```
feat: add user authentication
fix: resolve login validation error
refactor: extract common API call logic
chore: update ESLint configuration
```

