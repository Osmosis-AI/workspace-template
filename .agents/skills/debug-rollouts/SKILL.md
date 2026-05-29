---
name: debug-rollouts
description: Use when Osmosis doctor, an evaluation run, rollout server startup, grader rewards, dataset/config validation, Git readiness, environment variables, or training run preflight fails or produces low/zero rewards.
---

# Debug Rollouts

Find the smallest fix that makes the project runnable again.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the failing artifact first: rollout code, evaluation config, training config, dataset, or grader.

## Common failure buckets

- Structure/config: missing scaffold paths, config outside canonical directories, wrong entrypoint, or entrypoint escapes `rollouts/<name>/`.
- Discovery: zero/multiple concrete `AgentWorkflow` classes, no concrete `Grader`, or `Grader.grade` is not async.
- Server: the configured entrypoint, often `main.py`, lacks backend construction, `create_rollout_server`, `uvicorn.run`, or `_OSMOSIS_ROLLOUT_PORT`; evaluation run startup can also fail if `pyproject.toml` is missing, dependencies are incomplete, or imports only work from an unpushed local checkout. Inspect `osmosis --json eval info <eval-name>` and any platform failure details.
- **Dataset readiness:** The dataset in your evaluation or training config isn't listed by `osmosis --json dataset list`, its status isn't `uploaded`, your local source data has diverged from the platform dataset, required columns are missing, `AgentWorkflow.run` ignores `ctx.prompt`, or `Grader.grade` parses `ctx.label` in a format that doesn't match the real `ground_truth`.
- Sample/reward contract: workflow bypasses Osmosis with direct fixed-model provider calls; no sample source is registered; grader skips `ctx.set_sample_reward(...)`; reward logic is too strict, lenient, or broken.
- **Git sync:** Your code is uncommitted or unpushed, the `commit_sha` hasn't been pushed, or Git Sync isn't configured.
- **Runtime config:** The evaluation or training `[env]` or `[secrets]` is missing or incorrect, a secret section points to a platform secret record that doesn't exist, or you're using reserved `_OSMOSIS_` variables.
- **LLM config:** `[experiment].model_path` is missing or isn't a LiteLLM-style model name. The platform resolves the provider endpoint from the `model_path` prefix. There is no SDK-side base URL override.
- Intermittent zero-output rows: blocked async event loop from sync calls such as `mcp.list_tools_sync()`; wrap blocking calls in `asyncio.get_running_loop().run_in_executor(None, ...)`, or raise `agent_workflow_timeout_s` for long-horizon tasks.

## Process

1. Reproduce the failure with the narrowest command.
2. Fix one issue at a time.
3. Re-run immediately after each fix.
4. Re-submit the evaluation run after changing datasets, rollout files, configs, dependencies, or Git commit pins.
5. Stop once the evaluation run baseline is healthy again.

## Useful commands

```bash
osmosis --json doctor
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval info <eval-name>
osmosis --json eval list --limit 10

# Platform dataset checks
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
osmosis --json dataset download <dataset-name> -o data/<dataset-name>.jsonl

# Git sanity
git status
git log --oneline -5
```

`osmosis --json train submit configs/training/<run>.toml --yes` performs the training-run preflight checks and, if they pass, submits the run. Don't run this command until the user actually intends to submit.
