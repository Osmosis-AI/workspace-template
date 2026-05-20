---
name: evaluate-rollouts
description: Run and analyze local Osmosis rollout evals. Use when the user wants to smoke-test a rollout, compare baselines, improve reward performance, inspect failures, curate local eval data, or run a short eval-driven experiment loop.
---

# Evaluate Rollouts

Use fast local evals to decide what to keep, fix, or try next. A clean eval also serves as the smoke test for the server-style rollout entrypoint - the workflow + grader the server would expose are exercised end-to-end against `data/<name>.jsonl`.

## First checks

1. Read `AGENTS.md`, `configs/AGENTS.md` if present, and `.osmosis/research/program.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the target rollout and `configs/eval/<name>.toml`.
4. If rollout dependencies changed, run `pip install -e rollouts/<name>` before eval.

## Core loop

1. Run the current baseline:
   ```bash
   osmosis --json eval run configs/eval/<name>.toml --limit 1 --fresh
   ```
2. If the smoke test loads and grades, run the intended eval size without `--limit`.
3. Inspect rewards and sample-level failures. Add `--log-samples` when conversation traces are needed.
4. Choose one small hypothesis or data improvement.
5. Change only the necessary surface:
   - `rollouts/<name>/main.py` (or its package modules)
   - `configs/eval/<name>.toml`
   - local datasets under `data/`
6. Re-run the same eval with `--fresh` and compare against the prior baseline.
7. Keep or discard the change.
8. Log the experiment under `.osmosis/research/experiments/`.

## Dataset rules

- Local eval datasets share the schema with platform training datasets: `system_prompt`, `user_prompt`, `ground_truth`. Keep parity so the same rows can scale up to managed training without shape drift.
- `ctx.prompt` is derived from `system_prompt` + `user_prompt`; `ctx.label` is the `ground_truth` string passed to `Grader.grade`.
- Prefer real or user-approved examples.
- Add failure cases that exercise the grader and common user mistakes.
- Update the eval config whenever dataset paths change.

## Guardrails

- Local eval validates business logic, not platform-side dataset availability - that is the `submit-training` gate.
- Do not launch platform training from the eval loop.
- Prefer small, reviewable diffs over rewrites.
- If the rollout cannot load or validate, switch to `debug-rollouts`.
