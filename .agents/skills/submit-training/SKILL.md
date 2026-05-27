---
name: submit-training
description: Use when an Osmosis rollout has passed cloud eval and the user wants to prepare, validate, or submit training, verify platform dataset and Git readiness, tune parameters, or inspect a run.
---

# Submit Training

Submit only after every gate below is green.

- Config `dataset` is a **platform dataset name** from `osmosis --json dataset list`, not a `dataset_id` and not a `data/` path.
- The configured `entrypoint` is a **server** cloned from Git and run during training; it is often `main.py` but does not have to be.
- `osmosis --json train submit ... --yes` starts a managed training run. Use `--yes` only after the user has explicitly confirmed submission intent.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Confirm there is a working rollout, an eval config, and a recorded cloud eval result in `.osmosis/research/`.

## Pre-submit gates (run in order)

### A. Project and cloud eval

```bash
osmosis --json doctor
pip install -e rollouts/<name>
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval info <eval-name-from-submit>
```

For a smoke eval, set `[evaluation].limit = 1` in the eval config before submit. Then run the intended eval size by removing the temporary limit override; every sample must receive reward and meet any threshold in `.osmosis/research/program.md`.

### B. Platform dataset gate

Walk through this whenever the dataset, rollout, or grader changes:

```bash
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
osmosis --json dataset download <dataset-name> -o data/<dataset-name>.jsonl
```

For first uploads, run `osmosis --json dataset upload data/<name>.jsonl`. Confirm status is `uploaded`, required columns exist, `ground_truth` matches `Grader.grade(ctx.label)`, and prompts match `AgentWorkflow.run(ctx.prompt)`. Re-run cloud eval when parity is uncertain.

### C. Git push & commit pin

`osmosis --json train submit` reads the config from disk but fetches rollout code from the connected Git repository. Local edits that are not pushed are ignored.

Commit and push the intended revision. Push to the default branch for Git Sync, or set `commit_sha` to a specific pushed commit. Treat dirty/ahead/no-upstream warnings as blockers until the user explicitly accepts them.

### D. Training config completeness

If the rollout was already created with `osmosis --json rollout init <name>` and `configs/training/<name>.toml` exists, edit that original config instead of creating a new training TOML. Only start from `configs/training/default.toml` when no rollout-specific training config exists; if it is missing, use `references/training-default.toml`. Ensure `[experiment]` has real `rollout`, `entrypoint`, `model_path`, and platform dataset name values; no `<your-...>` placeholders and no `dataset_id`. Include training config edits in the intended commit before submit. Read `references/training-config-gates.md` when editing config fields, env/secrets, or remote rollout concurrency.

## Submit

```bash
osmosis --json train submit configs/training/<run>.toml --yes
osmosis --json train info <run-name>
```

There is no separate `rollout validate` command in the current SDK. `osmosis --json train submit` performs the training preflight and submits if it passes. If any gate is missing or failing, route to `evaluate-rollouts` or `debug-rollouts` before retrying.
