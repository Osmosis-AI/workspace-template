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

- Structure/config: missing scaffold paths, a source-backed eval or training config outside its canonical directory, wrong entrypoint, or entrypoint escapes `rollouts/<name>/`.
- Discovery: zero/multiple concrete `AgentWorkflow` classes, no concrete `Grader`, or `Grader.grade` is not async.
- Server: the configured entrypoint, often `main.py`, lacks backend construction, `create_rollout_server`, `uvicorn.run`, or `_OSMOSIS_ROLLOUT_PORT`; local or managed evaluation startup can also fail if `pyproject.toml` is missing or the required `server`/integration/backend extras are absent. Managed runs can additionally fail when imports only work from an unpushed local checkout; inspect `osmosis --json eval info <eval-name>` and `osmosis --json eval logs <eval-name>`. Local eval also warns when the CLI and the rollout environment resolve different `osmosis-ai` versions; align the pin in `rollouts/<name>/pyproject.toml` and re-sync that environment if the run misbehaves.
- Dataset readiness: The dataset in your evaluation or training config isn't listed by `osmosis --json dataset list`, its status isn't `uploaded`, local data has diverged, rows mix schema modes, metadata is empty, prompt-mode columns are missing, or workflow/grader code expects prompt or label fields that the selected mode does not provide.
- Sample/reward contract: workflow bypasses Osmosis with direct fixed-model provider calls; `run()` returns an unsupported type, unknown output fields, or non-finite metrics; `run()` returns `None` without exactly one registered sample source; the grader cannot read `ctx.sample` or skips `ctx.set_reward(...)`; reward logic is too strict, lenient, or broken.
- Harbor v0.3 migration: the entrypoint still passes removed `task_dir`, `user_code_dir`, or `workflow` arguments; `code_dir` does not contain `pyproject.toml` and an importable package; the task Dockerfile still copies rollout source or installs the SDK; or startup omits `backend.prewarm_lifespan()` and first-rollout setup fails or times out.
- Local upload: the run is pending or cancelled, or its directory lacks compatible `manifest.json`, `index.jsonl`, `progress.json`, or `metrics.json`. Failed and skipped samples are terminal; re-run `osmosis --json eval upload <run-name>` after an interrupted upload because the server resumes the same platform run.
- Git sync: For managed `eval submit`, your code is uncommitted or unpushed, the `commit_sha` hasn't been pushed, or Git Sync isn't configured. Compare the pushed HEAD against `last_synced_commit_sha` from `osmosis --json rollout list`.
- Workspace scope: A platform-only command ran outside a connected repository without root `--workspace`, the selected workspace name is unavailable, or a source submit's absolute config belongs to a different repository. Use `osmosis --workspace <workspace-name> ...` for platform-only commands; for `eval submit` and `train submit`, keep the absolute config under the matching repository's canonical config directory.
- Runtime config: The evaluation or training `[env]` or `[secrets]` is missing or incorrect, a secret section points to a platform secret record that doesn't exist (check with `osmosis --json secret list`), or you're using reserved `_OSMOSIS_` variables.
- LLM config: `[experiment].model_path` is missing or isn't a LiteLLM-style model name. The platform resolves the provider endpoint from the `model_path` prefix. There is no SDK-side base URL override.
- Intermittent zero-output rows: blocked async event loop from sync calls such as `mcp.list_tools_sync()`; wrap blocking calls in `asyncio.get_running_loop().run_in_executor(None, ...)`, or raise `agent_workflow_timeout_s` for long-horizon tasks.

## Process

1. Reproduce the failure with the narrowest command.
2. Fix one issue at a time.
3. Re-run immediately after each fix.
4. Re-run the local evaluation after changing datasets, rollout files, configs, or dependencies; re-submit a managed evaluation after changing Git commit pins.
5. Stop once the evaluation run baseline is healthy again.

## Useful commands

```bash
osmosis --json doctor
osmosis --json eval run configs/eval/<name>.toml
osmosis --json eval upload <run-name>
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval info <eval-name>
osmosis --json eval logs <eval-name>
osmosis --json eval list --limit 10

# Platform dataset checks
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset logs <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
osmosis --json dataset download <dataset-name> -o data/<dataset-name>.jsonl

# Training run diagnosis
osmosis --json train list
osmosis --json train logs <run-name>

# Secrets referenced by configs
osmosis --json secret list

# Git sanity
git status
git log --oneline -5
osmosis --json rollout list
```

`osmosis --json train submit configs/training/<run>.toml --yes` performs the training-run preflight checks and, if they pass, submits the run. Don't run this command until the user actually intends to submit.
