# Osmosis Workspace Repository

This repository is the source of truth for rollout code, eval configs, training configs, and local datasets connected to one Osmosis platform workspace. Run Osmosis CLI commands from inside this clone so the CLI can resolve the workspace from the GitHub `origin` remote.

## Setup

Start here after creating or joining an Osmosis platform workspace and cloning the connected workspace repository.

```bash
cd <workspace-repository>
pip install -e .
osmosis auth login
osmosis doctor
osmosis auth whoami
```

`osmosis doctor` checks that the Git remote, workspace layout, and required directories are valid. If the scaffold is missing required directories, run:

```bash
osmosis doctor --fix
```

For AI agents or automation, prefer `osmosis --json ...` for structured output or `osmosis --plain ...` for low-noise text.

## Repository Layout

```text
repository/
├── rollouts/            # AgentWorkflow + Grader code
├── configs/
│   ├── eval/            # Local eval configs
│   └── training/        # Training run configs
├── data/                # Local datasets for evals and uploads
├── AGENTS.md            # Workspace contract for AI coding assistants
├── CLAUDE.md            # Claude Code entrypoint for the same contract
└── pyproject.toml       # Workspace Python package
```

The CLI expects `rollouts/`, `configs/eval/`, `configs/training/`, and `data/` to exist. Keep rollout code and configs in those canonical paths so local eval and training preflight can discover them.

## Run the Starter Example

Use the included multiply example to verify the full loop before building a custom rollout.

```bash
pip install -e rollouts/multiply-local-openai
export OPENAI_API_KEY="sk-..."
osmosis eval run configs/eval/multiply-local-openai.toml --limit 10 --fresh
osmosis dataset upload data/multiply.jsonl
osmosis train submit configs/training/multiply-local-openai.toml
```

The eval config reads the local dataset from `data/multiply.jsonl`. The training config references the uploaded platform dataset as `multiply`.

## Build Your Own Rollout

Create a blank scaffold:

```bash
osmosis rollout init my-rollout
pip install -e rollouts/my-rollout
osmosis eval run configs/eval/my-rollout.toml --limit 1 --fresh
```

Or adapt one of the starter rollouts included in this repository by default: `multiply-local-strands`, `multiply-local-openai`, or `multiply-harbor-strands`.

```bash
pip install -e rollouts/multiply-local-strands
osmosis eval run configs/eval/multiply-local-strands.toml --limit 1 --fresh
```

Each rollout should expose one concrete `AgentWorkflow` and one concrete `Grader` from the configured entrypoint, usually `main.py`. Route policy model calls through Osmosis-supported integrations such as `OsmosisStrandsAgent` or `OsmosisAgent` so eval and training can collect samples and attach rewards.

## Configs and Data

Eval configs live in `configs/eval/*.toml` and use local datasets under `data/`.

```bash
osmosis eval run configs/eval/<name>.toml --limit 1 --fresh
```

Training configs live in `configs/training/*.toml` and use platform dataset names from:

```bash
osmosis dataset list
```

Upload local JSONL, CSV, or Parquet datasets when you are ready to train:

```bash
osmosis dataset upload data/<dataset>.jsonl
```

Never put secret values in TOML. Use `[rollout.secrets]` to map environment variable names to workspace secret record names that the platform resolves server-side.

## Git Sync and Training

Push rollout code and configs to the connected workspace repository before submitting training. Automatic Git Sync runs from the default branch, and training uses the synced code version.

```bash
git add .
git commit -m "add rollout"
git push
osmosis train submit configs/training/<name>.toml
```

Use `commit_sha` in the training config when you need to pin a run to a specific commit.

Inspect training runs and deploy checkpoints:

```bash
osmosis train info <run-name>
osmosis deploy <checkpoint-name>
osmosis deployment info <checkpoint-name>
```

## AI-Assisted Workflow

This workspace includes project-local Agent Skills in `.agents/skills/`:

- `plan-training`
- `create-rollouts`
- `evaluate-rollouts`
- `debug-rollouts`
- `submit-training`

`AGENTS.md` contains the always-loaded workspace contract. `CLAUDE.md` imports that contract for Claude Code, and `.claude/skills/<skill-name>` symlinks expose the same skills while pointing back to the canonical `.agents` directories.

A useful initial prompt for a coding agent:

```text
I want to train a model for <task> in this Osmosis workspace. Start with the `plan-training` skill: read the workspace instructions, help me settle the dataset plan, and propose the next step before creating rollouts, running evals, or submitting training.
```
