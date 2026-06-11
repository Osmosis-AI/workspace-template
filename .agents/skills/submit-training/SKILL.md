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
2. Confirm there is a working rollout, an evaluation config, and a recorded evaluation run result in `.osmosis/research/`.

## Pre-submit gates (run in order)

### A. Project and evaluation run

```bash
osmosis --json doctor
pip install -e rollouts/<name>
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval info <eval-name-from-submit>
```

For a quick smoke test, set `[evaluation].limit = 1` in the evaluation config before submitting. Then run the full evaluation by removing the temporary limit override; every sample must receive a reward and meet any threshold in `.osmosis/research/program.md`.

### B. Platform dataset gate

Walk through this whenever the dataset, rollout, or grader changes:

```bash
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
osmosis --json dataset download <dataset-name> -o data/<dataset-name>.jsonl
```

For first uploads, run `osmosis --json dataset upload data/<name>.jsonl --yes`. Confirm status is `uploaded`, required columns exist, `ground_truth` matches `Grader.grade(ctx.label)`, and prompts match `AgentWorkflow.run(ctx.prompt)`. Re-run the evaluation run when parity is uncertain.

### C. Git push & commit pin

`osmosis --json train submit` reads the config from disk but fetches rollout code from the connected Git repository. Local edits that are not pushed are ignored.

Commit and push the intended revision. Push to the default branch for Git Sync, or set `commit_sha` to a specific pushed commit. Treat dirty/ahead/no-upstream warnings as blockers until the user explicitly accepts them.

### D. Training config completeness

If the rollout was already created with `osmosis --json rollout init <name>` and `configs/training/<name>.toml` exists, edit that original config instead of creating a new training TOML. Only start from `configs/training/default.toml` when no rollout-specific training config exists; if it is missing, use `references/training-default.toml`. Ensure `[experiment]` has real `rollout`, `entrypoint`, `model_path`, and platform dataset name values; no `<your-...>` placeholders and no `dataset_id`. Include training config edits in the intended commit before submit. Read `references/training-config-gates.md` when editing training config fields, env/secrets, or remote rollout concurrency.

## Submit

```bash
osmosis --json train submit configs/training/<run>.toml --yes
osmosis --json train info <run-name>
```

`osmosis --json train submit configs/training/<run>.toml --yes` performs the training-run preflight checks and, if they pass, submits the run. If any gate is missing or failing, route to `evaluate-rollouts` or `debug-rollouts` before retrying.

Find run names with `osmosis --json train list`. If a run fails or crashes, inspect `osmosis --json train logs <run-name>`. Stop an in-progress run with `osmosis --json train stop <run-name> --yes` — only after the user explicitly asks. `train info -o <path>` exports the run's metrics JSON.

## After the run finishes

Checkpoints from a finished run appear as LoRA models. List them and serve one for inference only when the user asks to deploy:

```bash
osmosis --json model list
osmosis --json model info <lora-model-name>
osmosis --json model deploy <lora-model-name>
osmosis --json model undeploy <lora-model-name>
```

`model info` reports a single model's checkpoint step, training reward, Hugging Face upload status, deployment status, and `platform_url`.
