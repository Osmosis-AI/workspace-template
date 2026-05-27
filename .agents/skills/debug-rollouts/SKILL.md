---
name: debug-rollouts
description: Use when Osmosis doctor, cloud eval, rollout server startup, grader rewards, dataset/config validation, Git readiness, environment variables, or training preflight fails or produces low/zero rewards.
---

# Debug Rollouts

Find the smallest fix that makes the project runnable again.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the failing artifact first: rollout code, eval config, training config, dataset, or grader.

## Common failure buckets

- Structure/config: missing scaffold paths, config outside canonical directories, wrong entrypoint, or entrypoint escapes `rollouts/<name>/`.
- Discovery: zero/multiple concrete `AgentWorkflow` classes, no concrete `Grader`, or `Grader.grade` is not async.
- Server: the configured entrypoint, often `main.py`, lacks backend construction, `create_rollout_server`, `uvicorn.run`, or `_OSMOSIS_ROLLOUT_PORT`; cloud eval startup can also fail if `pyproject.toml` is missing, dependencies are incomplete, or imports only work from an unpushed local checkout. Inspect `osmosis --json eval status <eval-name>` and any platform failure details.
- Dataset contract: the eval config names a missing platform dataset, required columns are missing, `AgentWorkflow.run` ignores `ctx.prompt`, or `Grader.grade` parses `ctx.label` differently from the real `ground_truth` format.
- Sample/reward contract: workflow bypasses Osmosis with direct fixed-model provider calls; no sample source is registered; grader skips `ctx.set_sample_reward(...)`; reward logic is too strict, lenient, or broken.
- Platform handoff: eval or training config names a dataset not returned by `osmosis --json dataset list`, dataset status is not `uploaded`, local source data diverges from the platform dataset, code is uncommitted/unpushed, `commit_sha` is not pushed, or Git Sync is not configured.
- Runtime config: eval or training `[env]` / `[secrets]` is absent/wrong, a secret section names a missing platform secret record, or reserved `_OSMOSIS_` vars are used.
- LLM config: `[llm].model_path` is missing or not a LiteLLM-style model name, or `[llm].base_url` is set to the wrong LiteLLM/OpenAI-compatible endpoint. Leave `base_url` commented unless the eval model needs a custom provider URL.
- Intermittent zero-output rows: blocked async event loop from sync calls such as `mcp.list_tools_sync()`; wrap blocking calls in `asyncio.get_running_loop().run_in_executor(None, ...)`, or raise `agent_workflow_timeout_s` for long-horizon tasks.

## Process

1. Reproduce the failure with the narrowest command.
2. Fix one issue at a time.
3. Re-run immediately after each fix.
4. Re-submit cloud eval after changing datasets, rollout files, configs, dependencies, or Git commit pins.
5. Stop once the cloud eval baseline is healthy again.

## Useful commands

```bash
osmosis --json doctor
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval status <eval-name>
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

There is no separate `rollout validate` command in the current SDK. `osmosis --json train submit configs/training/<run>.toml --yes` performs training preflight and submits if it passes, so do not run it until the user intends to submit.
