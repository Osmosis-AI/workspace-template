---
name: debug-rollouts
description: Diagnose rollout, grader, config, eval, dataset, or training-preflight failures in a structured Osmosis project. Use when the user sees errors, low rewards, broken local evals, rollout validation failures, or train submit preflight failures.
---

# Debug Rollouts

Find the smallest fix that makes the project runnable again.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the failing artifact first: rollout code, eval config, training config, dataset, or grader.

## Common failure buckets

1. Project structure is invalid.
2. Config lives outside the canonical path.
3. Entrypoint is wrong or escapes the rollout directory.
4. Multiple workflows or graders are exported.
5. No concrete `Grader` exists, or `Grader.grade` is not async.
6. **Rollout entrypoint is not a server** - `main.py` is missing a backend (`LocalBackend` or `HarborBackend`), `create_rollout_server`, or `uvicorn.run`. The platform cannot serve a non-server entrypoint even if local eval still imports the workflow class.
7. **Workflow / dataset shape mismatch** - `AgentWorkflow.run` reads fields the dataset rows do not carry, or ignores fields the dataset assumes will be used.
8. **Grader / `ground_truth` format mismatch** - `Grader.grade` cannot parse `ctx.label` as the dataset's actual `ground_truth` format (e.g. expects a float but rows contain JSON).
9. Local dataset path or row shape is wrong.
10. **Platform dataset not usable** - the name in `configs/training/<run>.toml` is not in `osmosis --json dataset list` for the active workspace, status is not `uploaded`, or its schema diverges from the local copy.
11. **Git remote not aligned** - uncommitted or unpushed code, no upstream branch, `commit_sha` pinned to an unpushed commit, or workspace has no Git Sync configured.
12. **Missing or wrong env vars / secrets** - rollout fails at startup (`status=failed` within ~30 s) because a `[rollout.env]` key is absent or has the wrong value, or a `[rollout.secrets]` reference points to a workspace `environment_secret` record that does not exist. Pre-register secrets in the platform UI and verify names match exactly.
13. **No rewards assigned** - `Grader.grade` returns without calling `ctx.set_sample_reward(...)` for every sample.
14. Grader logic is too strict, too lenient, or broken.
15. **Intermittent dropped rows** - a small number of rows (2-10) show zero reward and empty output while the rest succeed. Causes: (a) the rollout server's async event loop is blocked by synchronous calls (e.g. `mcp.list_tools_sync()`) preventing it from responding to the default 30 s HTTP timeout; wrap blocking calls in `asyncio.get_running_loop().run_in_executor(None, ...)`. (b) `agent_workflow_timeout_s` too low for long-horizon tasks; increase it in `[training]`.

## Process

1. Reproduce the failure with the narrowest command.
2. Fix one issue at a time.
3. Re-run immediately after each fix.
4. Stop once the local baseline is healthy again.

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
