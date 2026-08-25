---
name: submit-training
description: Use when an Osmosis rollout has passed an evaluation run and the user wants to prepare, validate, or submit a training run, verify platform dataset and Git readiness, tune parameters, or inspect a run.
---

# Submit Training

Submit only after every gate below is green.

- Config `dataset` is a **platform dataset name** from `osmosis --json dataset list`, not a `dataset_id` and not a `data/` path.
- The configured `entrypoint` is a **server** cloned from Git and run during training; it is often `main.py` but does not have to be.
- `osmosis --json train submit ... --yes` starts a managed training run. Use `--yes` only after the user has explicitly confirmed submission intent.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Confirm there is a working rollout, an evaluation config, and a passing full-size evaluation run on the platform.

## Pre-submit gates (run in order)

### A. Project and evaluation run

```bash
osmosis --json doctor
pip install -e rollouts/<name>
osmosis --json eval list
osmosis --json eval info <eval-name>
```

A full-size managed evaluation run created by `osmosis eval submit` must already have passed on the revision being submitted. An uploaded local result can support diagnosis and comparison but does not satisfy this gate. Find the managed run with `eval list`, inspect it with `eval info`, and confirm:

- It covered the whole dataset — no `[evaluation].limit` override.
- Every sample received a reward.
- The score meets the success criterion, taken from `.osmosis/research/program.md` when present. That directory is gitignored and empty on a fresh clone, so the platform run is the authority.
- Its pinned commit matches the revision Gate C pins. A rollout, grader, dataset, or config change since that run makes it stale.

If no qualifying run exists, or it is stale, stop and route the user to the `submit-eval` skill.

### B. Platform dataset gate

Walk through this whenever the dataset, rollout, or grader changes:

```bash
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
osmosis --json dataset download <dataset-name> -o data/<dataset-name>.jsonl
```

For first uploads, run `osmosis --json dataset upload data/<name>.jsonl --yes`. Confirm status is `uploaded` and every row follows the selected schema. In prompt mode, verify `ground_truth` matches `Grader.grade(ctx.label)` and prompts match `AgentWorkflow.run(ctx.prompt)`; in metadata mode, verify the workflow and grader consume `ctx.metadata`. Route back to `submit-eval` for a fresh evaluation run when parity is uncertain.

### C. Git push & source pin

`osmosis --json train submit` reads the config from disk but fetches rollout code from the connected Git repository. Local edits that are not pushed are ignored.

Commit and push the intended revision. Set `branch` to pin to a branch or `commit_sha` to pin to a specific commit; the two fields are mutually exclusive. Omit both to use the connected repository's default branch. Treat dirty/ahead/no-upstream warnings as blockers until the user explicitly accepts them.

### D. Training config completeness

If the rollout was already created with `osmosis --json rollout init <name>` and `configs/training/<name>.toml` exists, edit that original config instead of creating a new training TOML. Only start from `configs/training/default.toml` when no rollout-specific training config exists; if it is missing, use `references/training-default.toml`. Ensure `[experiment]` has real `rollout`, `entrypoint`, `model_path`, and platform dataset name values; no `<your-...>` placeholders and no `dataset_id`. Include training config edits in the intended commit before submit. Read `references/training-config-gates.md` when editing training config fields, env/secrets, or remote rollout concurrency.

## Submit

```bash
osmosis --json train submit configs/training/<run>.toml --yes
osmosis --json train info <run-name>
```

`osmosis --json train submit configs/training/<run>.toml --yes` performs the training-run preflight checks and, if they pass, submits the run. If any gate is missing or failing, route to `submit-eval` for a missing or stale evaluation run, or to `evaluate-rollouts` or `debug-rollouts`, before retrying.

Find run names with `osmosis --json train list`. If a run fails or crashes, inspect `osmosis --json train logs <run-name>`. Stop an in-progress run with `osmosis --json train stop <run-name> --yes` — only after the user explicitly asks. `train info -o <path>` exports the run's metrics JSON.

## After the run finishes

Checkpoints from a finished run appear as LoRA models (`osmosis --json model list`). Deploying one for inference is a separate, user-initiated workflow — use the `deploy-models` skill when the user asks.
