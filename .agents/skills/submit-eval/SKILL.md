---
name: submit-eval
description: Use when the rollout and evaluation config are settled and the user wants the full evaluation run as the formal measurement, or when reading out final evaluation results.
---

# Submit Eval

The full-size evaluation run is the measurement of record. Choose local execution plus optional upload, or managed execution, then proceed only after the applicable gates below are green.

- Config `dataset` is a **platform dataset name** from `osmosis --json dataset list`, not a `dataset_id` and not a `data/` path.
- `osmosis eval run` executes the configured server from local files through `LocalBackend` or Harbor. With `--dataset-file PATH` and no `--upload`, it does not require platform credentials; platform dataset selection or upload still does. Harbor Docker works directly on macOS; Daytona, other Harbor cloud environments, and model-calling Harbor Docker on Linux need a public route to the local model bridge, which the run creates with `cloudflared` automatically, so keep `cloudflared` on `PATH` or supply a tunnel you manage via `--listener-port` and `--advertise-url`. Daytona configs must list `DAYTONA_API_KEY` under `[secrets].required`. `osmosis eval submit` clones the pushed server from Git and runs it on managed infrastructure.
- `osmosis --json eval submit ... --yes` grades the managed selection and costs money. Use `--yes` only after the user has explicitly confirmed submission intent.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`.
3. Confirm iteration is finished: a clean smoke run on the target `configs/eval/<name>.toml`, and no pending rollout or grader change.

## Pre-submit gates (run in order)

### A. Config sanity

Read the target `configs/eval/<name>.toml` and confirm:

- `[experiment].rollout`, `entrypoint`, `model_path`, and `dataset` all hold real values — no `<your-...>` placeholders, no `dataset_id`.
- `model_path` is the LiteLLM-style name of the model actually under test.
- `[evaluation].limit` is commented out or removed; the formal run covers the whole dataset.
- The rest of `[evaluation]` stays commented unless the user deliberately wants an override (`n` for repeated attempts, `pass_threshold` for the pass bar).
- Every name in `[secrets].required` resolves at submit from `--secrets-file <path|->`, the environment, a stored record, or an interactive prompt (TTY only), first hit wins; confirm each name has a route, checking stored records with `osmosis --json secret list`. A value supplied at submit is never saved, so a rerun must supply it again.

### B. Dataset gate

```bash
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
```

Confirm status is `uploaded`, required columns exist, `ground_truth` matches `Grader.grade(ctx.label)`, and prompts match `AgentWorkflow.run(ctx.prompt)`. If the local source data changed during iteration, upload or replace the platform dataset before treating the run as the measurement of record.

### C. Managed-only Git push & source pin

`osmosis --json eval submit` reads the config from disk but fetches rollout code from the connected Git repository. Local edits that are not pushed are ignored.

Commit and push the intended revision, config included. Set `branch` to pin to a branch or `commit_sha` to pin to the exact commit being measured; the two fields are mutually exclusive, and omitting both uses the connected repository's default branch. A pinned commit is what makes the reported score reproducible. Treat dirty/ahead/no-upstream warnings as blockers until the user explicitly accepts them.

## Run locally and optionally upload

```bash
osmosis --json eval run configs/eval/<name>.toml
osmosis --json eval run configs/eval/<name>.toml --dataset-file data/<name>.jsonl
osmosis --json eval run configs/eval/<name>.toml --upload
```

The `--dataset-file` form stays local without platform credentials only when `--upload` is absent. The config still belongs under `configs/eval/` in a valid local workspace.

The default run directory is `.osmosis/evals/<run-name>/`. `--upload` publishes only after the run reaches a complete terminal state; failed and skipped samples are terminal, while pending or cancelled runs cannot be uploaded. To publish an already-completed run later, pass its run name or an explicit run directory:

```bash
osmosis --json eval upload <run-name>
```

`eval upload` has no confirmation and no extra flags. A bare run name resolves under the workspace's `.osmosis/evals/`; a path with a separator, or an existing directory of that name, is used as given. It requires workspace authentication/context and a compatible directory containing `manifest.json`, `index.jsonl`, `progress.json`, and `metrics.json`. Re-running it after interruption is safe: the server returns the same platform run and the CLI uploads only files missing there.

The upload includes `index.jsonl`, `progress.json`, canonical referenced `trajectory*.json` files, and safe artifacts for selected rollout IDs. It keeps `logs.txt` local and excludes local `manifest.json` bytes, `events.jsonl`, `metrics.json`, summary/projection copies, control files, per-trial logs, and superseded attempts. Manifest digest, schema versions, and allowlisted redacted Git provenance are sent as metadata; the server validates files, recomputes metrics, and does not launch a hosted or Temporal evaluation.

## Submit on managed infrastructure

```bash
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval info <eval-name-from-submit>
```

From another current directory, pass the root workspace selector and the config's absolute canonical path:

```cli
osmosis --workspace <workspace-name> --json eval submit /absolute/path/to/repository/configs/eval/<name>.toml --yes
```

The CLI locates the config's containing Osmosis Git workspace, verifies the selected platform workspace is connected to that repository, and submits with workspace-name scope only. Without root `--workspace`, submission retains the current directory's Git-derived scope.

If any gate is missing or failing, route to `evaluate-rollouts` or `debug-rollouts` before retrying. Find run names with `osmosis --json eval list --limit 10`. Stop a run submitted by mistake with `osmosis --json eval stop <eval-name> --yes`.

## Read out the result

1. From `osmosis --json eval info <eval-name>`, report score, pass rate, and sample count, and confirm every sample received a reward.
2. Export the metrics JSON with `osmosis --json eval info <eval-name> -o <path>` so the run can be compared against later ones.
3. Give the verdict against the success criterion in `.osmosis/research/program.md`, not just the raw score.
4. Log the run under `.osmosis/research/experiments/` with its config, pinned commit, model, and dataset.

Outside the clone, platform read and lifecycle commands can use explicit scope, for example `osmosis --workspace <workspace-name> --json eval info <eval-name>`.

## Guardrails

- Confirm with the user before every `--yes`; a full-size evaluation run grades every row and costs money.
- Uploaded local results appear in `eval list`, `eval info`, and Platform viewers with a Local badge; dirty Git provenance produces a warning.
- Do not claim an uploaded local run satisfies the managed full-size evaluation gate before training.
- Do not iterate here. Hypothesis-driven rollout and grader changes belong to `evaluate-rollouts`; return once the change is settled.
- Do not shrink the run to reach a better number. `[evaluation].limit` belongs to smoke tests.
- If the run fails to start, samples come back ungraded, or rewards are unexpectedly zero, switch to `debug-rollouts` instead of interpreting the score.
- Do not launch a platform training run from here; that is `submit-training`.
- Report the score with its pinned commit, model, and dataset. An unattributed number is not a measurement.
