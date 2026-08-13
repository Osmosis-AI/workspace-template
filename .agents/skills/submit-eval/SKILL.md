---
name: submit-eval
description: Use when the rollout and evaluation config are settled and the user wants the full evaluation run as the formal measurement, or when reading out final evaluation results.
---

# Submit Eval

The full-size evaluation run is the measurement of record. Submit only after every gate below is green.

- Config `dataset` is a **platform dataset name** from `osmosis --json dataset list`, not a `dataset_id` and not a `data/` path.
- The configured `entrypoint` is a **server** cloned from Git and run during the evaluation run; it is often `main.py` but does not have to be.
- `osmosis --json eval submit ... --yes` grades every row and costs money. Use `--yes` only after the user has explicitly confirmed submission intent.

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

### B. Platform dataset gate

```bash
osmosis --json dataset list
osmosis --json dataset info <dataset-name>
osmosis --json dataset preview <dataset-name> --rows 5
```

Confirm status is `uploaded`, required columns exist, `ground_truth` matches `Grader.grade(ctx.label)`, and prompts match `AgentWorkflow.run(ctx.prompt)`. If the local source data changed during iteration, upload or replace the platform dataset before treating the run as the measurement of record.

### C. Git push & source pin

`osmosis --json eval submit` reads the config from disk but fetches rollout code from the connected Git repository. Local edits that are not pushed are ignored.

Commit and push the intended revision, config included. Set `branch` to pin to a branch or `commit_sha` to pin to the exact commit being measured; the two fields are mutually exclusive, and omitting both uses the connected repository's default branch. A pinned commit is what makes the reported score reproducible. Treat dirty/ahead/no-upstream warnings as blockers until the user explicitly accepts them.

## Submit

```bash
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval info <eval-name-from-submit>
```

If any gate is missing or failing, route to `evaluate-rollouts` or `debug-rollouts` before retrying. Find run names with `osmosis --json eval list --limit 10`. Stop a run submitted by mistake with `osmosis --json eval stop <eval-name> --yes`.

## Read out the result

1. From `osmosis --json eval info <eval-name>`, report score, pass rate, and sample count, and confirm every sample received a reward.
2. Export the metrics JSON with `osmosis --json eval info <eval-name> -o <path>` so the run can be compared against later ones.
3. Give the verdict against the success criterion in `.osmosis/research/program.md`, not just the raw score.
4. Log the run under `.osmosis/research/experiments/` with its config, pinned commit, model, and dataset.

## Guardrails

- Confirm with the user before every `--yes`; a full-size evaluation run grades every row and costs money.
- Do not iterate here. Hypothesis-driven rollout and grader changes belong to `evaluate-rollouts`; return once the change is settled.
- Do not shrink the run to reach a better number. `[evaluation].limit` belongs to smoke tests.
- If the run fails to start, samples come back ungraded, or rewards are unexpectedly zero, switch to `debug-rollouts` instead of interpreting the score.
- Do not launch a platform training run from here; that is `submit-training`.
- Report the score with its pinned commit, model, and dataset. An unattributed number is not a measurement.
