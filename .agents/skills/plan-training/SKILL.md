---
name: plan-training
description: Use when an Osmosis task idea, dataset, or training goal is not settled; the user asks what to train or evaluate next; or a rollout/evaluation/training path needs planning before code changes.
---

# Plan Training

Anchor the plan on the dataset. The row shape (`system_prompt`, `user_prompt`, `ground_truth`) is the contract for rollout, grader, evaluation, and training.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor` to confirm the workspace scaffold.
3. Inspect existing `rollouts/`, `configs/`, `data/`, and `.osmosis/research/`.
4. Treat the installed `osmosis` CLI, SDK scaffold, and generated files as source of truth if this skill conflicts with them.

## Dataset-first decision

Before writing any rollout code, settle the dataset. Ask the user which case applies:

1. **Local sample file already on disk**
   - Place it at `data/<name>.jsonl` (or `.csv` / `.parquet`).
   - Run `osmosis --json dataset validate <path>` and inspect `warnings`.
   - If validation fails because the source schema differs from Osmosis' expected row shape, inspect 5-10 rows and ask the user to confirm the intended field mapping.
   - When the source has enough information, create one normalized dataset copy under `data/<name>.jsonl` with the expected columns, preserve the original file, then validate and inspect the normalized copy before continuing.
   - Read 5-10 normalized rows to confirm every row has non-empty string `system_prompt`, `user_prompt`, and `ground_truth`, and note the actual `ground_truth` format (numeric string? JSON? free text?).

2. **Already uploaded to the Osmosis platform**
   - List with `osmosis --json dataset list` and confirm the name is in the active workspace.
   - Pull a copy down for local iteration:
     ```bash
     osmosis --json dataset download <name> -o data/<name>.jsonl
     ```
   - Use `--overwrite` only when intentionally replacing an existing local copy.
   - Read 5-10 rows and verify local schema parity before designing rollout or grader logic.

3. **No sample data yet**
   - Discuss the use case with the user before generating anything: input shape (what goes in `system_prompt` / `user_prompt`), success criterion (what `ground_truth` should encode), tools the agent will call.
   - Generate 5-20 rows in `data/<name>.jsonl` matching the required schema.
   - Run `osmosis --json dataset validate data/<name>.jsonl` and inspect any JSON `warnings`.

Record the dataset decision, hypotheses, eval plan, and stop conditions in `.osmosis/research/program.md`; use `.osmosis/research/<task>.md` for task notes.

## Workflow

1. Settle the dataset (above) before anything else.
2. Clarify the task, interaction shape, and success criteria against the dataset's actual rows.
3. Define the first measurable evaluation run result to compare against future runs.
4. Choose the smallest next step that keeps the project runnable.
5. Route execution:
   - no runnable rollout -> `create-rollouts`
   - runnable eval result needs improvement -> `evaluate-rollouts`
   - evaluation, config, loading, or grader fails -> `debug-rollouts`
   - validated evaluation run result is ready for a platform training run -> `submit-training`

## Guardrails

- Do not skip the dataset decision; the rollout has nothing to bind to without it.
- Do not invent benchmark examples. Generate sample rows only after the user has agreed on the use case.
- Do not design rollout or grader logic around a non-conforming raw dataset schema when a one-time normalization step can produce the expected dataset contract.
- Do not launch platform training from planning.
- Keep all artifacts in canonical Osmosis project paths.
