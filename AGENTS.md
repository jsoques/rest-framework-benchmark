# AGENTS.md

## Project
`perf-test` — a performance-testing project. Currently scaffolding only: no source code,
build tooling, README, or git repo yet. Installed project-local skills target Go and
Python/FastAPI, indicating the intended stacks.

## Development workflow (OpenSpec)
- Primary process is spec-driven via the `openspec` CLI (v1.8.0). Default schema: `spec-driven` (see `openspec/config.yaml`).
- `/opsx-propose` — plan only. Creates proposal/specs/design/tasks. NEVER implement or edit project code during propose; wait for a new user request.
- `/opsx-apply <change>` — implement tasks from a change. Read `openspec instructions apply --change <name> --json` context files first; tick `- [ ]` → `- [x]` in tasks.md after each task.
- `/opsx-sync` / `/opsx-archive` — promote delta specs to main specs / archive a finished change.
- Key commands: `openspec status --change <name> --json`, `openspec instructions <artifact> --change <name> --json`, `openspec list --json`.
- Artifacts are file-existence-gated; after proposing, re-run `openspec status` until the full required set is done.

## Skills (project-local, `.agents/skills/`)
- Go work → invoke relevant `golang-*` skill (e.g. `golang-performance` for benchmarks/profiling, `golang-concurrency`, `golang-testing` patterns).
- Python work → `fastapi-python`.
- `skills-lock.json` is machine-managed (GitHub sources: mindrally/skills, samber/cc-skills-golang) — don't hand-edit.

## Boundaries
- No git repo yet — no commit/branch/PR conventions established.
- `.opencode/commands/opsx-*.md` and `.devin/workflows/opsx-*.md` mirror each other; keep in sync if modified.
- No build/test commands exist to run until scaffolding lands.