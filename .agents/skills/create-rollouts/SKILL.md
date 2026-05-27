---
name: create-rollouts
description: Use when creating or adapting Osmosis rollout code, scaffolding configs, adding an AgentWorkflow, Grader, or rollout server entrypoint, or making a rollout load under cloud eval or training preflight.
---

# Create Rollouts

Create the smallest rollout that can load, submit to cloud eval, and later train. The dataset shape from `plan-training` is the contract for both workflow and grader.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`. If scaffold paths are missing, ask before running `osmosis --json doctor --fix`.
3. Confirm the local source dataset exists with valid `system_prompt` / `user_prompt` / `ground_truth` rows. If not, run `plan-training` first.
4. Pick a rollout name matching `^[a-z][a-z0-9-]*$` (lowercase letters, digits, hyphens; starts with a letter) and not `default`.
5. Treat `osmosis --json rollout init <name>`, SDK templates, and generated files as source of truth if a hand-written skeleton differs.

## Scaffold

For a blank rollout, start with `osmosis --json rollout init <name>`; it usually writes `rollouts/<name>/main.py`, `pyproject.toml`, `README.md`, and matching eval/training configs from the SDK scaffold. That default filename is not mandatory once the eval/training configs name a different in-rollout entrypoint. Use `--force` only when intentionally replacing those paths.

Do not reapply default TOML after `rollout init`. Use `configs/eval/default.toml`, `configs/training/default.toml`, or the skill fallback TOMLs only when repairing missing configs or creating configs without `rollout init`.

For worked examples, run `osmosis --json template list` and apply a local template such as `multiply-local-strands` or `multiply-local-openai`, then adapt it to the dataset.

Read `references/entrypoint-patterns.md` only when hand-writing or substantially rewriting the configured entrypoint, or when the server/sample-source pattern is failing.

## Rollout rules

- Keep the entrypoint inside `rollouts/<name>/`.
- Default new scaffolds to `main.py`, but preserve and honor any explicit `entrypoint` already named in eval or training configs.
- Expose exactly one concrete `AgentWorkflow`.
- Expose exactly one concrete `Grader`; eval configs no longer carry a separate `[grader]` section.
- The workflow's `run` receives `ctx.prompt`, a list of system/user messages converted from the dataset's `system_prompt` + `user_prompt` columns.
- The workflow must register at least one sample source, either through an SDK integration (`OsmosisStrandsAgent`, `OsmosisAgent` + `OsmosisMemorySession`) or by calling `get_rollout_context().register_sample_source(...)`.
- Policy model calls inside `AgentWorkflow.run` must route through the active rollout context. Do not call `litellm`, the OpenAI SDK, or another provider SDK directly with a fixed policy model from the workflow.
- The grader implements async `grade(ctx)`, reads `ctx.label` as the dataset `ground_truth`, and assigns every sample a reward with `ctx.set_sample_reward(sample_id, reward)`.
- Keep tools as async Python functions with type hints and docstrings.
- Keep the grader explicit, partial-credit friendly, and easy to inspect.

## Validation

After creating or adapting the rollout, run:

```bash
osmosis --json doctor
python -m py_compile rollouts/<name>/<entrypoint-from-config>
pip install -e rollouts/<name>
osmosis --json dataset info <dataset-name-from-eval-config>
osmosis --json eval submit configs/eval/<name>.toml --yes
osmosis --json eval status <eval-name-from-submit>
```

A clean cloud eval submit is the platform smoke test for the same Git-synced entrypoint, workflow, grader, model config, and platform dataset that training will use. If the eval config still has a placeholder dataset, upload or select a platform dataset first; `[experiment].dataset` must be a platform dataset name, not a local path.

If a matching training config exists, inspect and update that original file now, then include the config changes in the intended commit when the user is ready to prepare training. Do not submit training from this skill. `osmosis --json train submit configs/training/<run>.toml --yes` performs the current SDK preflight when the user is ready to train.
