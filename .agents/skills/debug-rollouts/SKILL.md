---
name: debug-rollouts
description: Use when Osmosis doctor, local eval, rollout server startup, grader rewards, dataset/config validation, Git readiness, environment variables, or training preflight fails or produces low/zero rewards.
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
- Server: the configured entrypoint, often `main.py`, lacks backend construction, `create_rollout_server`, `uvicorn.run`, or `_OSMOSIS_ROLLOUT_PORT`; local eval health can also fail if port `8000` is occupied, `pyproject.toml` is missing, or imports only work from repo root. Inspect `.osmosis/cache/eval/<model>/<dataset>/user-server-<task_id>.log`.
- Dataset contract: local path is wrong, required columns are missing, `AgentWorkflow.run` ignores `ctx.prompt`, or `Grader.grade` parses `ctx.label` differently from the real `ground_truth` format.
- Sample/reward contract: workflow bypasses Osmosis with direct fixed-model provider calls; no sample source is registered; grader skips `ctx.set_sample_reward(...)`; reward logic is too strict, lenient, or broken.
- Platform handoff: training config names a dataset not returned by `osmosis --json dataset list`, dataset status is not `uploaded`, schema diverges from local eval data, code is uncommitted/unpushed, `commit_sha` is not pushed, or Git Sync is not configured.
- Runtime config: `[rollout.env]` is absent/wrong, `[rollout.secrets]` names a missing platform secret record, or reserved `_OSMOSIS_` vars are used.
- Intermittent zero-output rows: blocked async event loop from sync calls such as `mcp.list_tools_sync()`; wrap blocking calls in `asyncio.get_running_loop().run_in_executor(None, ...)`, or raise `agent_workflow_timeout_s` for long-horizon tasks.

## Process

1. Reproduce the failure with the narrowest command.
2. Fix one issue at a time.
3. Re-run immediately after each fix.
4. Use `--fresh` after changing datasets, rollout files, configs, or dependencies.
5. Stop once the local baseline is healthy again.

## Useful commands

```bash
osmosis --json doctor
osmosis --json eval run configs/eval/<name>.toml --limit 1 --fresh --debug

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
