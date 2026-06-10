---
name: evaluate-rollouts
description: Use when submitting Osmosis evaluation runs, smoke-testing rollout configs, comparing evaluation run results or rewards, inspecting sample failures, checking platform dataset readiness, or iterating on rollout/grader performance.
---

# Evaluate Rollouts

Use evaluation runs to decide what to keep, fix, or try next. `osmosis eval submit` sends a platform evaluation job against the platform dataset named in `configs/eval/<name>.toml`, using the Git-synced rollout entrypoint, workflow, and grader.

## First checks

1. Read `AGENTS.md`, `configs/AGENTS.md` if present, and `.osmosis/research/program.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the target rollout, `configs/eval/<name>.toml`, and platform dataset name.
4. If creating an evaluation config, copy from `configs/eval/default.toml`; if it is missing, use `references/eval-default.toml`.
5. Confirm the evaluation config uses the evaluation run schema:
   - `[experiment].rollout`, `entrypoint`, `model_path`, and `dataset` are required.
   - `dataset` is a platform dataset name, not a `data/` path or dataset ID.
   - `model_path` uses a LiteLLM-style model name; the platform resolves the provider endpoint from its prefix.
   - `[evaluation]` values are optional; leave them commented unless deliberately overriding platform defaults.
6. Confirm dataset availability:
   ```bash
   osmosis --json dataset list
   osmosis --json dataset info <dataset-name>
   osmosis --json dataset preview <dataset-name> --rows 5
   ```
7. If the dataset has not been uploaded yet, validate and upload the local source file, then update `[experiment].dataset` to the platform dataset name:
   ```bash
   osmosis --json dataset validate data/<name>.jsonl
   osmosis --json dataset upload data/<name>.jsonl --yes
   ```

## Core loop

1. For a quick smoke test, temporarily set `[evaluation].limit = 1`. Otherwise, leave the optional evaluation fields commented out to use the platform defaults.
2. Ensure the intended rollout code and config are committed and pushed to the connected workspace repository.
3. Submit the evaluation run:
   ```bash
   osmosis --json eval submit configs/eval/<name>.toml --yes
   ```
4. Inspect the returned run name, then check details/results:
   ```bash
   osmosis --json eval info <eval-name>
   ```
5. If the smoke run starts, completes, and grades every sample, run the intended evaluation size by removing the temporary `limit` override.
6. Inspect score, pass rate, sample count, and failure details returned by `eval info` or the platform UI.
7. Choose one small hypothesis or data improvement.
8. Change only the necessary surface:
   - `rollouts/<name>/<entrypoint-from-config>` or its package modules
   - `configs/eval/<name>.toml`
   - local source datasets under `data/` when preparing a new platform upload
9. Commit and push the change, then re-submit the same evaluation config and compare against the prior evaluation run.
10. Keep or discard the change.
11. Log the experiment under `.osmosis/research/experiments/`.

## Dataset rules

- Local source datasets and platform datasets should share the Osmosis row shape: `system_prompt`, `user_prompt`, `ground_truth`.
- `ctx.prompt` is derived from `system_prompt` + `user_prompt`; `ctx.label` is the `ground_truth` string passed to `Grader.grade`.
- Prefer real or user-approved examples.
- Add failure cases that exercise the grader and common user mistakes.
- When local data changes, upload or replace the platform dataset before treating an evaluation run as representative.

## Guardrails

- Evaluation run validates platform-side dataset availability, Git sync, rollout startup, workflow execution, and grader behavior together.
- Do not launch a platform training run from the evaluation loop.
- Local edits that are not pushed can be ignored by platform evaluation runs unless the config pins a pushed `commit_sha`.
- Prefer small, reviewable diffs over rewrites.
- If the rollout cannot load, the platform evaluation run fails before grading, or rewards are unexpectedly zero, switch to `debug-rollouts`.
