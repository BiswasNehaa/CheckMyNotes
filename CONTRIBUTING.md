# Contributing to CheckMyNotes

Thanks for considering a contribution! This is a small student project, so the process is intentionally lightweight.

## Getting Set Up

Follow the [Self-Hosting section in README.md](./README.md#-self-hosting) to get the backend and frontend running locally. You'll need a free Groq API key to actually evaluate pages — without one, uploads still work but every evaluation returns "AI unavailable."

For a full explanation of how the code is organized and why, read [ARCHITECTURE.md](./ARCHITECTURE.md) before making non-trivial changes.

## Finding Something to Work On

Check the [Issues tab](https://github.com/BiswasNehaa/CheckMyNotes/issues) — issues labeled [`good first issue`](https://github.com/BiswasNehaa/CheckMyNotes/labels/good%20first%20issue) are scoped to be self-contained and don't require deep familiarity with the codebase.

If you want to work on something not already filed, open an issue first describing the problem and your proposed approach, so we can align before you put in the work.

## Making Changes

1. Fork the repo and create a branch off `main` (e.g. `fix/cache-scoping`, `feat/pdf-upload`).
2. Keep changes focused — one issue/feature per pull request.
3. Match the existing code style:
   - **Backend**: plain, readable Python; docstrings on public functions explaining *why*, not just what.
   - **Frontend**: functional React components, no new state-management libraries for small features.
4. Run the linter before committing:
   ```bash
   cd frontend && npm run lint
   ```
5. Manually test the flow your change touches (login → upload → evaluate → view → PDF export) — there's no automated test suite yet, so manual verification matters.

## Submitting a Pull Request

- Reference the issue number in your PR description (e.g. `Closes #3`).
- Describe what changed and why, not just what.
- Keep the diff minimal — avoid unrelated refactors or formatting-only changes mixed into a feature PR.

## Code of Conduct

Be respectful and constructive in issues and PRs. Disagreements about approach are fine; personal attacks aren't.
