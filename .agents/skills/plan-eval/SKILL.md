---
name: plan-eval
description: Use when an Osmosis evaluation goal is not settled; the user asks what to evaluate next or wants to score a model on a dataset; or an evaluation path needs planning before code changes.
---

# Plan Eval

Anchor the plan on the number you intend to report. Settle what is being measured, on which dataset, and against which model before writing rollout or config code.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor` to confirm the workspace scaffold.
3. Inspect existing `rollouts/`, `configs/eval/`, `data/`, and `.osmosis/research/`.
4. Treat the installed `osmosis` CLI, SDK scaffold, and generated files as source of truth if this skill conflicts with them.

## Dataset-first decision

The row shape (`system_prompt`, `user_prompt`, `ground_truth`) is the contract for the rollout, the grader, and the score. Settle the dataset before shaping an evaluation config. Ask the user which case applies:

1. **Local sample file already on disk**
   - Place it at `data/<name>.jsonl` (or `.csv` / `.parquet`).
   - Run `osmosis --json dataset validate <path>` and inspect `warnings`.
   - If validation fails because the source schema differs from Osmosis' expected row shape, inspect 5-10 rows and ask the user to confirm the intended field mapping.
   - When the source has enough information, create one normalized dataset copy under `data/<name>.jsonl` with the expected columns, preserve the original file, then validate and inspect the normalized copy before continuing.
   - Read 5-10 normalized rows to confirm every row has non-empty string `system_prompt`, `user_prompt`, and `ground_truth`, and note the actual `ground_truth` format (numeric string? JSON? free text?).

2. **Already uploaded to the Osmosis platform**
   - Confirm the name is in the active workspace and inspect what the platform actually holds:
     ```bash
     osmosis --json dataset list
     osmosis --json dataset info <dataset-name>
     osmosis --json dataset preview <dataset-name> --rows 5
     ```
   - Pull a copy down for local reasoning:
     ```bash
     osmosis --json dataset download <name> -o data/<name>.jsonl
     ```
   - Use `--overwrite` only when intentionally replacing an existing local copy.

3. **No sample data yet**
   - Discuss the use case with the user before generating anything: input shape (what goes in `system_prompt` / `user_prompt`), success criterion (what `ground_truth` should encode), tools the agent will call.
   - Generate 5-20 rows in `data/<name>.jsonl` matching the required schema.
   - Run `osmosis --json dataset validate data/<name>.jsonl` and inspect any JSON `warnings`.

An evaluation dataset may be a held-out slice rather than the training data, but it has to reach the platform before a run: `[experiment].dataset` is a platform dataset name, never a `data/` path and never a dataset ID. Upload with `osmosis --json dataset upload data/<name>.jsonl --yes` when the local file is the source.

Record the dataset decision, the model(s) under test, the success criterion, and the stop conditions in `.osmosis/research/program.md`; use `.osmosis/research/<task>.md` for task notes.

## Workflow

1. Settle the dataset (above) before anything else.
2. State what the score means: the capability under test, and what counts as a pass for a single row.
3. Fix the success criterion up front — target score or pass rate — so the run returns a verdict instead of a number.
4. Choose the model(s) to score. `[experiment].model_path` is a LiteLLM-style model name and the platform resolves the provider endpoint from its prefix; use one evaluation config per rollout/model setup and keep the dataset identical across them so scores stay comparable.
5. Confirm a grader exists that reads `ctx.label` in the dataset's real `ground_truth` format and can express partial credit.
6. Shape `configs/eval/<name>.toml` by copying `configs/eval/default.toml`; if it is missing, use `.agents/skills/evaluate-rollouts/references/eval-default.toml`. `[experiment].rollout`, `entrypoint`, `model_path`, and `dataset` are required; `branch` and `commit_sha` are optional and mutually exclusive; `[secrets]` must be present with a `required` list; leave `[evaluation]` values commented unless deliberately overriding platform defaults.
7. Route execution:
   - no runnable rollout -> `create-rollouts`
   - rollout or grader still needs iteration -> `evaluate-rollouts`
   - evaluation, config, loading, or grader fails -> `debug-rollouts`
   - rollout and config are settled and the formal number is next -> `submit-eval`

## Guardrails

- Do not skip the dataset decision; the score has nothing to bind to without it.
- Do not invent benchmark examples. Generate sample rows only after the user has agreed on the use case.
- Do not design rollout or grader logic around a non-conforming raw dataset schema when a one-time normalization step can produce the expected dataset contract.
- Do not submit any run from planning. Smoke runs belong to `evaluate-rollouts`; the full-size run belongs to `submit-eval`.
- Do not plan a training run here. If the user pivots from measuring a model to improving one, hand off to `plan-training`.
- Keep all artifacts in canonical Osmosis project paths.
