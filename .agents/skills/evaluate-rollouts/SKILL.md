---
name: evaluate-rollouts
description: Use when smoke-testing rollout configs, iterating on rollout or grader performance with small evaluation runs, comparing evaluation run results or rewards, or inspecting sample failures.
---

# Evaluate Rollouts

Use local evaluation runs to decide what to keep, fix, or try next. `osmosis eval run` requires SDK 0.3.1's `eval` extra and executes the config with the rollout's `LocalBackend` or Harbor backend, using the files on disk; publishing the completed result is optional.

## First checks

1. Read `AGENTS.md`, `configs/AGENTS.md` if present, and `.osmosis/research/program.md` if present.
2. Run `osmosis --json doctor`.
3. Identify the target rollout, `configs/eval/<name>.toml`, and platform dataset name.
4. If the rollout uses Harbor, inspect `environment_config.type`. Docker works directly on macOS. For Daytona, SkyPilot, another cloud environment, or model-calling Docker on Linux, keep the configured environment and plan to add `--tunnel cloudflared`; use `--listener-port <port> --advertise-url <url>` only when the user already manages a suitable public tunnel.
5. If creating an evaluation config, copy from `configs/eval/default.toml`; if it is missing, use `references/eval-default.toml`.
6. Confirm the evaluation config uses the evaluation run schema:
   - `[experiment].rollout`, `entrypoint`, `model_path`, and `dataset` are required.
   - `dataset` is a platform dataset name, not a `data/` path or dataset ID.
   - `branch` and `commit_sha` are optional and mutually exclusive; omit both to use the default branch.
   - `model_path` uses a LiteLLM-style model name; the platform resolves the provider endpoint from its prefix.
   - `[evaluation]` values are optional; leave them commented unless deliberately overriding the selected command's defaults.
7. Confirm dataset availability:
   ```bash
   osmosis --json dataset list
   osmosis --json dataset info <dataset-name>
   osmosis --json dataset preview <dataset-name> --rows 5
   ```
8. If the dataset has not been uploaded yet, validate and upload the local source file, then update `[experiment].dataset` to the platform dataset name:
   ```bash
   osmosis --json dataset validate data/<name>.jsonl
   osmosis --json dataset upload data/<name>.jsonl --yes
   ```

## Core loop

1. Set `[evaluation].limit = 1` for the smoke run, and leave the other optional evaluation fields commented out to use their command defaults.
2. Run the evaluation locally:
   ```bash
   osmosis --json eval run configs/eval/<name>.toml
   ```
   Add `--tunnel cloudflared` when the Harbor environment needs a route back to the local model bridge.
3. Capture `resource.run_name` from the result and inspect `.osmosis/evals/<run-name>/`. Omitting `--name` generates an `adjective-animal-number` name; pass that exact name with `--name` to resume pending work.
4. If the user wants the run in platform viewers, publish only after it completes:
   ```bash
   osmosis --json eval upload .osmosis/evals/<run-name>/
   ```
5. Confirm the smoke run starts, completes, and grades every sample. Failed and skipped samples are terminal and uploadable; pending or cancelled runs are not. Once iteration is done and no rollout or grader change is pending, hand the formal full-size run to `submit-eval`.
6. Inspect score, pass rate, sample count, and failure details in the local metrics and progress files or, after upload, with `osmosis --json eval info <eval-name>`.
7. Choose one small hypothesis or data improvement.
8. Change only the necessary surface:
   - `rollouts/<name>/<entrypoint-from-config>` or its package modules
   - `configs/eval/<name>.toml`
   - local source datasets under `data/` when preparing a new platform upload
9. Re-run the same evaluation config and compare against the prior local or uploaded evaluation run.
10. Keep or discard the change.
11. Log the experiment under `.osmosis/research/experiments/`.

## Dataset rules

- Local source datasets and platform datasets must use one schema throughout: metadata mode (`metadata` is non-empty on every row) or prompt mode (`user_prompt` + `ground_truth`, with optional `system_prompt`).
- In prompt mode, `ctx.prompt` is derived from the prompt columns and `ctx.label` is the `ground_truth` string passed to `Grader.grade`. In metadata mode, inspect `ctx.metadata` and do not assume prompt or label fields exist.
- Prefer real or user-approved examples.
- Add failure cases that exercise the grader and common user mistakes.
- When local data changes, upload or replace the platform dataset before treating an evaluation run as representative.

## Guardrails

- `eval run` validates local rollout startup, workflow execution, and grader behavior without validating managed Git sync or hosted infrastructure.
- Stop a runaway local run through the local runner; `osmosis --json eval stop <eval-name> --yes` applies to managed runs created by `eval submit`.
- Do not report a run from this loop as the formal measurement. When the change is settled, the full-size run belongs to `submit-eval`.
- Do not launch a platform training run from the evaluation loop.
- Uploading a completed local result is idempotent and server-authoritative. Re-run `osmosis --json eval upload .osmosis/evals/<run-name>/` after interruption; it returns the same platform run and uploads only missing server files.
- A named run is locked to its resolved inputs. Resume only after an interruption without code or data changes; start a new generated-name run for an experiment, or use `--fresh` when deliberately archiving and replacing the named run.
- Prefer small, reviewable diffs over rewrites.
- If the rollout cannot load, the local run fails before grading, or rewards are unexpectedly zero, switch to `debug-rollouts`.
