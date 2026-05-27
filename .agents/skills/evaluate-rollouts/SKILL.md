---
name: evaluate-rollouts
description: Use when submitting Osmosis cloud evals, smoke-testing rollout configs, comparing rewards or baselines, inspecting sample failures, checking platform dataset readiness, or iterating on rollout/grader performance.
---

# Evaluate Rollouts

Use cloud evals to decide what to keep, fix, or try next. `osmosis eval submit` sends a platform evaluation job against the platform dataset named in `configs/eval/<name>.toml`, using the Git-synced rollout entrypoint, workflow, and grader.

## First checks

1. Read `AGENTS.md`, `configs/AGENTS.md` if present, and `.osmosis/research/program.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the target rollout, `configs/eval/<name>.toml`, and platform dataset name.
4. If creating an eval config, copy from `configs/eval/default.toml`; if it is missing, use `references/eval-default.toml`.
5. Confirm the eval config uses the cloud schema:
   - `[experiment].rollout`, `entrypoint`, and `dataset` are required.
   - `dataset` is a platform dataset name, not a `data/` path or dataset ID.
   - `[llm].model_path` is required and uses a LiteLLM-style model name.
   - `[llm].base_url` is optional, LiteLLM/OpenAI-compatible, and normally commented out because no default is applied when omitted.
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
   osmosis --json dataset upload data/<name>.jsonl
   ```

## Core loop

1. For a smoke eval, temporarily set `[evaluation].limit = 1`; otherwise leave optional evaluation fields commented to use platform defaults.
2. Submit the eval:
   ```bash
   osmosis --json eval submit configs/eval/<name>.toml --yes
   ```
3. Inspect the returned run name, then check status/results:
   ```bash
   osmosis --json eval status <eval-name>
   ```
4. If the smoke run starts, completes, and grades every sample, run the intended eval size by removing the temporary `limit` override.
5. Inspect score, pass rate, sample count, and failure details returned by status or the platform UI.
6. Choose one small hypothesis or data improvement.
7. Change only the necessary surface:
   - `rollouts/<name>/<entrypoint-from-config>` or its package modules
   - `configs/eval/<name>.toml`
   - local source datasets under `data/` when preparing a new platform upload
8. Re-submit the same eval config and compare against the prior baseline.
9. Keep or discard the change.
10. Log the experiment under `.osmosis/research/experiments/`.

## Dataset rules

- Local source datasets and platform datasets should share the Osmosis row shape: `system_prompt`, `user_prompt`, `ground_truth`.
- `ctx.prompt` is derived from `system_prompt` + `user_prompt`; `ctx.label` is the `ground_truth` string passed to `Grader.grade`.
- Prefer real or user-approved examples.
- Add failure cases that exercise the grader and common user mistakes.
- When local data changes, upload or replace the platform dataset before treating a cloud eval as representative.

## Guardrails

- Cloud eval validates platform-side dataset availability, Git sync, rollout startup, workflow execution, and grader behavior together.
- Do not launch platform training from the eval loop.
- Local edits that are not pushed can be ignored by platform eval unless the config pins a pushed `commit_sha`.
- Prefer small, reviewable diffs over rewrites.
- If the rollout cannot load, the platform eval fails before grading, or rewards are unexpectedly zero, switch to `debug-rollouts`.
