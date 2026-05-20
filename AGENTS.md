# Osmosis Workspace Repository

This is a structured Osmosis workspace repository. Do not invent a different
top-level layout.

## Workspace Directory Contract

Required paths:

- `rollouts/`
- `configs/training/`
- `configs/eval/`
- `data/`

Conventions:

- New rollouts live in `rollouts/<name>/`.
- The canonical rollout entrypoint is `rollouts/<name>/main.py`.
- Eval configs live in `configs/eval/<name>.toml`.
- Training configs live in `configs/training/<name>.toml`.
- Local training guidance lives in `.osmosis/research/program.md`.
- Local cache and metrics state lives in `.osmosis/` and should not be treated
  as source.
- Do not create new top-level directories unless the user explicitly asks.

Check the workspace scaffold with:

```bash
osmosis doctor
```

Repair missing scaffold directories with:

```bash
osmosis doctor --fix
```

## Rollout Contract

- Each rollout entrypoint must expose one concrete `AgentWorkflow`.
- Local eval and managed training require a concrete `Grader` in the rollout
  server.
- Tools should be async Python functions with type hints and docstrings.
- `Grader.grade` must be async and assign rewards in `[0.0, 1.0]`.
- Before `osmosis train submit`, run a local eval and push code to the connected
  workspace repository.

Create a blank rollout scaffold with:

```bash
osmosis rollout init <name>
```

Apply a starter template with:

```bash
osmosis template list
osmosis template apply multiply-local-strands
```

## Environment Variables and Secrets

Training configs can inject environment variables into the rollout container via
two optional TOML sections:

```toml
[rollout.env]
# Literal values baked into the config. Do NOT store secrets here.
LOG_LEVEL = "INFO"

[rollout.secrets]
# Maps env-var name to workspace environment_secret record name.
# The platform resolves the actual value server-side.
OPENAI_API_KEY = "openai-api-key"
```

Rules:

- Both sections are optional; omit them entirely if not needed.
- Keys must match `^[A-Z_][A-Z0-9_]*$`.
- The same key cannot appear in both sections.
- Reserved names (`GITHUB_CLONE_URL`, `GITHUB_TOKEN`, `ENTRYPOINT_SCRIPT`,
  `REPOSITORY_PATH`, `TRAINING_RUN_ID`, `ROLLOUT_NAME`, `ROLLOUT_PORT`) are
  forbidden in both sections.
- Inside the container, all injected vars are available via `os.environ`.

## AI Skills

Detailed workflow guidance lives in project-local Agent Skills under
`.agents/skills/`. Treat those files as the canonical AI workflow source for
this workspace.

| Skill | What it does |
| --- | --- |
| `plan-training` | Turn a vague task into a concrete local training plan. |
| `create-rollouts` | Create or adapt rollouts, graders, entrypoints, and initial eval configs. |
| `evaluate-rollouts` | Run local evals, compare baselines, and iterate with data. |
| `debug-rollouts` | Diagnose rollout, grader, config, dataset, or preflight failures. |
| `submit-training` | Prepare a training config and submit it safely. |

Claude Code discovers the same skills through `.claude/skills/<skill-name>`
symlinks. Each symlink points back to the matching canonical directory under
`.agents/skills/` instead of duplicating workflow content.

## CLI Output

- The commands below use the default rich output for interactive human sessions.
- For AI agents or automation, prefer `osmosis --json ...` for structured output
  or `osmosis --plain ...` for low-noise text.

## Common Commands

```bash
osmosis doctor
osmosis template list
osmosis template apply multiply-local-strands
osmosis rollout init <name>
osmosis eval run configs/eval/<name>.toml --limit 1
osmosis dataset upload data/train.jsonl
osmosis train submit configs/training/<name>.toml
osmosis train info <run-name>
osmosis deploy <checkpoint-name>
osmosis deployment info <checkpoint-name>
```
