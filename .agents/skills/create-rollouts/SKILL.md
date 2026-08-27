---
name: create-rollouts
description: Use when creating or adapting Osmosis rollout code, scaffolding configs, adding an AgentWorkflow, Grader, or rollout server entrypoint, or making a rollout load under an evaluation run or training run preflight.
---

# Create Rollouts

Create the smallest rollout that can load, submit an evaluation run, and later submit a training run. The dataset shape from `plan-training` is the contract for both workflow and grader.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`. If scaffold paths are missing, ask before running `osmosis --json doctor --fix`.
3. Confirm the local source dataset consistently uses metadata mode or prompt mode. If not, run `plan-training` first.
4. Pick a rollout name matching `^[a-z][a-z0-9-]*$` (lowercase letters, digits, hyphens; starts with a letter) and not `default`.
5. Treat `osmosis --json rollout init <name>`, SDK templates, and generated files as source of truth if a hand-written skeleton differs.

## Scaffold

For a blank rollout, start with `osmosis --json rollout init <name>`; it usually writes `rollouts/<name>/main.py`, `pyproject.toml`, `README.md`, and matching evaluation/training configs from the SDK scaffold. That default filename is not mandatory once the evaluation/training configs name a different in-rollout entrypoint. Use `--force` only when intentionally replacing those paths.

Do not reapply default TOML after `rollout init`. Use `configs/eval/default.toml`, `configs/training/default.toml`, or the skill fallback TOMLs only when repairing missing configs or creating configs without `rollout init`.

For worked examples, run `osmosis --json template list` and apply a template such as `multiply-local-strands`, `multiply-local-openai`, or `multiply-harbor-strands`, then adapt it to the dataset.

Read `references/entrypoint-patterns.md` only when hand-writing or substantially rewriting the configured entrypoint, or when the server/sample-source pattern is failing.

## Rollout rules

- Keep the entrypoint inside `rollouts/<name>/`.
- Default new scaffolds to `main.py`, but preserve and honor any explicit `entrypoint` already named in evaluation or training configs.
- Expose exactly one concrete `AgentWorkflow`.
- Expose exactly one concrete `Grader`; evaluation configs no longer carry a separate `[grader]` section.
- The workflow's `run` receives `ctx.prompt`, built from any prompt columns present. `system_prompt` is optional, and metadata-only rows may produce an empty prompt list.
- The workflow must produce one sample. Return `AgentWorkflowOutput(messages=..., metrics=...)` or a bare message list when the workflow owns the history. Return `None` only after an SDK integration (`OsmosisStrandsAgent`, `OsmosisAgent` + `OsmosisMemorySession`) or custom `get_rollout_context().set_sample_source(...)` call registers exactly one fallback source.
- Keep `AgentWorkflowOutput.metrics` finite and numeric; unknown top-level output fields and `NaN`/infinite metrics are rejected by both Local and Harbor/container execution.
- Policy model calls inside `AgentWorkflow.run` must route through the active rollout context. Do not call `litellm`, the OpenAI SDK, or another provider SDK directly with a fixed policy model from the workflow.
- The grader implements async `grade(ctx)`, reads the rollout's single sample from `ctx.sample`, and assigns its reward with `ctx.set_reward(reward)`. In prompt mode, `ctx.label` is the dataset `ground_truth`; metadata-mode graders may instead use `ctx.metadata`.
- Keep tools as async Python functions with type hints and docstrings.
- Keep the grader explicit, partial-credit friendly, and easy to inspect.
- For Harbor isolation, mirror `multiply-harbor-strands`: import `HarborBackend` from `osmosis_ai.rollout.backend.harbor`; pass `tasks_dir=`, `task_mode=`, and `agent=`; point `code_dir=` at the project root containing `pyproject.toml` when needed; and use `backend.prewarm_lifespan()`. Do not use `HarborBackendV2` or the removed `task_dir=`, `user_code_dir=`, and `workflow=` Harbor arguments.
- Keep Harbor task Dockerfiles task-only. The backend bundles the rollout project and installs it in the task container, so do not copy the workspace or install the rollout SDK manually in the task image.

## Validation

After creating or adapting the rollout, run:

```bash
osmosis --json doctor
python -m py_compile rollouts/<name>/<entrypoint-from-config>
pip install -e rollouts/<name>
osmosis --json dataset info <dataset-name-from-eval-config>
osmosis --json eval run configs/eval/<name>.toml
```

Run an evaluation locally first to confirm the entrypoint, workflow, grader, model config, and selected backend work together. Harbor Docker works directly on macOS; for Daytona, SkyPilot, another Harbor cloud environment, or model-calling Harbor Docker on Linux, keep the configured environment and add `--tunnel cloudflared`. The dataset can differ (e.g. a held-out eval set), but `[experiment].dataset` must be a platform dataset name, not a placeholder or local path. Uploading that result is optional and does not replace the managed full-size evaluation gate before training.

If a matching training config exists, inspect and update that original file now, then include the config changes in the intended commit when the user is ready to prepare a training run. Do not submit a training run from this skill. `osmosis --json train submit configs/training/<run>.toml --yes` performs the current SDK preflight when the user is ready to train.
