# Osmosis Workspace Repository

This repository is the local source for rollouts, eval configs, training configs,
and datasets connected to an Osmosis platform workspace.

## Quick Start

After cloning the workspace repository from the Osmosis Platform:

```bash
# Enter the local workspace directory
cd <workspace-repository>

# Install workspace dependencies
pip install -e .

# Authenticate the CLI
osmosis auth login

# Check the workspace directory scaffold
osmosis doctor
```

For AI agents or automation, use `osmosis --json ...` for structured output or
`osmosis --plain ...` for low-noise text.

## AI-Assisted Workflow

This workspace includes project-local Agent Skills in `.agents/skills/`.
Agents that support the open Agent Skills format can use those skills for the
standard Osmosis flow:

- `plan-training`
- `create-rollouts`
- `evaluate-rollouts`
- `debug-rollouts`
- `submit-training`

`AGENTS.md` contains the always-loaded workspace contract. `CLAUDE.md` imports
that contract for Claude Code, and `.claude/skills/<skill-name>` symlinks list
the same skills for Claude while pointing back to the canonical `.agents`
directories.

## Build a Rollout

Start from a template:

```bash
osmosis template list
osmosis template apply multiply-local-strands
pip install -e rollouts/multiply-local-strands
osmosis eval run configs/eval/multiply-local-strands.toml --limit 1
```

Or create a blank scaffold:

```bash
osmosis rollout init my-rollout
pip install -e rollouts/my-rollout
osmosis eval run configs/eval/my-rollout.toml --limit 1
```

## Sync and Train

Push rollout code to the connected workspace repository before training:

```bash
git add .
git commit -m "add rollout"
git push
osmosis train submit configs/training/my-rollout.toml
```

Inspect training runs and deploy checkpoints:

```bash
osmosis train info <run-name>
osmosis deploy <checkpoint-name>
osmosis deployment info <checkpoint-name>
```

## Ask Your Agent

```text
I want to train a model for <task>. Read .osmosis/research/program.md,
create or adapt a rollout in this workspace repository, iterate locally with
evals, and prepare a training config. Use `osmosis --json` or
`osmosis --plain` for Osmosis CLI commands when you need machine-readable or
low-noise output.
```
