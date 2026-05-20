---
name: submit-training
description: Prepare and submit Osmosis training runs from canonical project configs. Use when the user has a validated rollout and wants to create or update a training config, tune submit-time hyperparameters, run `osmosis --json train submit`, or check training status.
---

# Submit Training

Submit only after every gate below is green. Two facts shape the whole flow:

- The training config's `dataset` is a **platform dataset name** (from `osmosis --json dataset list`), not a path under `data/`.
- The rollout's `main.py` is a **server** the platform clones from your Git remote and runs during training.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Confirm there is a working rollout, an eval config, and a recorded baseline in `.osmosis/research/`.

## Pre-submit gates (run in order)

### A. Project sanity

```bash
osmosis --json doctor
```

### B. Local eval clean

```bash
pip install -e rollouts/<name>
osmosis --json eval run configs/eval/<name>.toml --limit 1 --fresh
```

Then run the intended eval size without `--limit`. This is the server smoke test by proxy - the same workflow + grader objects the server would expose are exercised end-to-end. Every sample must receive a non-null reward; apply any task-specific pass threshold from `.osmosis/research/program.md`.

### C. Platform dataset gate

Walk through this whenever the dataset, rollout, or grader changes:

1. Decide which platform dataset to use.
   - First-time use of a local file: upload it.
     ```bash
     osmosis --json dataset upload data/<name>.jsonl
     ```
   - Reusing an existing platform dataset: confirm it lives in the active workspace.
     ```bash
     osmosis --json dataset list
     ```
2. Inspect status and a quick preview:
   ```bash
   osmosis --json dataset info <dataset-name>           # status must be "uploaded"
   osmosis --json dataset preview <dataset-name> --rows 5
   ```
3. Pull the platform copy into the project for review:
   ```bash
   osmosis --json dataset download <dataset-name> -o data/<dataset-name>.jsonl
   ```
   Use `--overwrite` if a local file with the same name already exists. Keeping the canonical copy under `data/` makes it easy to re-run local eval against the exact rows the platform will train on.
4. Read 5-10 rows of the downloaded copy and verify against the rollout:
   - All three required columns present: `system_prompt`, `user_prompt`, `ground_truth`.
   - `ground_truth` format matches what `Grader.grade` parses from `ctx.label` (numeric string, JSON, free text, etc.).
   - `system_prompt` + `user_prompt` shape matches what `AgentWorkflow.run` reads from `ctx.prompt`, and is realistic enough to drive the workflow to a terminal state.
5. Optionally re-run local eval against the downloaded copy to confirm parity end-to-end.

If any check fails, fix the dataset, the workflow, or the grader before submitting - do not proceed with a mismatched contract.

### D. Git push & commit pin

`osmosis --json train submit` reads the config from disk but fetches **rollout code** from the workspace's connected Git repository. Local edits to code that have not been pushed are silently ignored.

- All rollout changes committed and pushed.
- Prefer an up-to-date upstream branch, or pin `commit_sha` to a pushed commit when the intended source revision matters. The SDK warns about dirty, ahead, or no-upstream state; it does not treat those warnings as automatic preflight failures once the user confirms.
- The workspace must have Git Sync configured in the Osmosis Platform.

### E. Training config completeness

Under `configs/training/<run>.toml`:

- `[experiment]` populated with real values for `rollout`, `entrypoint`, `model_path`, `dataset`. No `<your-...>` template placeholders.
- One config per run intent. For a new rollout, prefer the SDK scaffold:
  ```bash
  osmosis --json rollout init <name>
  ```
  For an existing rollout, copy and adapt a nearby `configs/training/<rollout>.toml` or a cookbook template.

#### Key `[training]` parameters for remote rollout servers

When submitting a run with a remote rollout server (Harbor or MCP-based), set `rollout_batch_size` explicitly. A batch size of 32 combined with `n_samples_per_prompt = 8` sends 256 concurrent LLM calls to the inference engine per step, which can overwhelm large remote agents and cause rollouts to timeout with zero reward.

```toml
[training]
n_samples_per_prompt = 8
rollout_batch_size = 8      # 8 x 8 = 64 concurrent calls; safe for 35B+ models
# agent_workflow_timeout_s = 900   # increase for long-horizon tasks (default: 450 s)
# grader_timeout_s = 300           # increase for slow verification graders (default: 150 s)
```

Rule of thumb: `rollout_batch_size <= 32` for remote MCP/Harbor rollout servers with 35B+ models.

#### Optional: environment variables and secrets

If the rollout reads env vars at runtime, declare them in the config. Both sections are optional - omit them entirely if not needed.

```toml
[rollout.env]
# Literal key = "value" pairs injected verbatim into the rollout container.
# Visible in this file - do NOT put secrets here.
LOG_LEVEL = "INFO"

[rollout.secrets]
# Maps env-var name -> workspace environment_secret record *name*.
# Values are resolved server-side; they never appear in this file or in transit.
# Pre-register secrets at /:orgName/secrets in the platform UI first.
OPENAI_API_KEY = "openai-api-key"
```

Rules:
- Keys must match `^[A-Z_][A-Z0-9_]*$`.
- The same key cannot appear in both sections.
- Reserved names are forbidden: `GITHUB_CLONE_URL`, `GITHUB_TOKEN`,
  `ENTRYPOINT_SCRIPT`, `REPOSITORY_PATH`, `TRAINING_RUN_ID`, `ROLLOUT_NAME`,
  `ROLLOUT_PORT`.
- Inside the container, all injected vars are accessible via `os.environ`.

## Submit

```bash
osmosis --json train submit configs/training/<run>.toml --yes
osmosis --json train info <run-name>
```

There is no separate `rollout validate` command in the current SDK. `osmosis --json train submit` performs the training preflight and submits if it passes. If any gate is missing or failing, route to `evaluate-rollouts` or `debug-rollouts` before retrying.
