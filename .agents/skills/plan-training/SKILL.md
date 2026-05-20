---
name: plan-training
description: Plan an Osmosis training workflow in a structured project. Use when the user has a vague task idea, asks what to do next, wants a research program, or needs a path from task definition to rollout, eval, and training.
---

# Plan Training

Anchor the plan on the dataset, then design the rollout around it. The dataset's row shape (`system_prompt`, `user_prompt`, `ground_truth`) is the contract every later artifact binds to.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor` to confirm the workspace scaffold.
3. Inspect existing `rollouts/`, `configs/`, `data/`, and `.osmosis/research/`.

## Dataset-first decision

Before writing any rollout code, settle the dataset. Ask the user which case applies:

1. **Local sample file already on disk**
   - Place it at `data/<name>.jsonl` (or `.csv` / `.parquet`).
   - Run `osmosis --json dataset validate <path>` against the actual file path and extension. In JSON output, inspect `warnings` too; Parquet validation is skipped with a warning when `pyarrow` is unavailable.
   - Read 5-10 rows to confirm the shape of `ground_truth` (numeric? string? JSON?).

2. **Already uploaded to the Osmosis platform**
   - List with `osmosis --json dataset list` and confirm the name is in the active workspace.
   - Pull a copy down for local iteration:
     ```bash
     osmosis --json dataset download <name> -o data/<name>.jsonl
     ```
   - Read 5-10 rows.

3. **No sample data yet**
   - Discuss the use case with the user before generating anything: input shape (what goes in `system_prompt` / `user_prompt`), success criterion (what `ground_truth` should encode), tools the agent will call.
   - Generate 5-20 rows in `data/<name>.jsonl` matching the required schema.
   - Run `osmosis --json dataset validate data/<name>.jsonl` and inspect any JSON `warnings`.

The chosen schema drives every later decision: how `AgentWorkflow.run` consumes `ctx.prompt`, and how `Grader.grade` parses `ctx.label` and assigns sample rewards.

## Outputs

- Experiment program: `.osmosis/research/program.md` - record the dataset decision (origin, schema, sample size).
- Research notes: `.osmosis/research/<task>.md`.
- Next action: `create-rollouts`, `evaluate-rollouts`, `debug-rollouts`, or `submit-training`.

## Workflow

1. Settle the dataset (above) before anything else.
2. Clarify the task, interaction shape, and success criteria against the dataset's actual rows.
3. Define the first measurable local baseline.
4. Choose the smallest next step that keeps the project runnable.
5. Write or update `.osmosis/research/program.md` with hypotheses, eval plan, and stop conditions.
6. Route execution:
   - no runnable rollout -> `create-rollouts`
   - runnable baseline needs improvement -> `evaluate-rollouts`
   - eval, config, loading, or grader fails -> `debug-rollouts`
   - validated baseline is ready for platform training -> `submit-training`

## Guardrails

- Do not skip the dataset decision; the rollout has nothing to bind to without it.
- Do not invent benchmark examples. Generate sample rows only after the user has agreed on the use case.
- Do not launch platform training from planning.
- Keep all artifacts in canonical Osmosis project paths.
