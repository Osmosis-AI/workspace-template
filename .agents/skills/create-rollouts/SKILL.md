---
name: create-rollouts
description: Create or adapt Osmosis rollouts in canonical project paths. Use when the user wants to scaffold a new rollout, add a grader, add an eval config, convert a task plan into runnable code, or make an existing rollout valid for eval and managed training.
---

# Create Rollouts

Create the smallest rollout that can load, evaluate, and later train. The dataset shape decided in `plan-training` is the input contract for both the workflow and the grader.

## First checks

1. Read `AGENTS.md` and `configs/AGENTS.md` if present.
2. Run `osmosis --json doctor`. If scaffold paths are missing, ask before running `osmosis --json doctor --fix`.
3. Confirm `data/<name>.jsonl` exists with valid `system_prompt` / `user_prompt` / `ground_truth` rows. If not, run `plan-training` first.
4. Pick a rollout name matching `^[a-z][a-z0-9-]*$` (lowercase letters, digits, hyphens; starts with a letter) and not `default`.

## Required files

For a blank SDK-owned scaffold, start with `osmosis --json rollout init <name>`; it writes all files below. Use `--force` only when intentionally replacing existing rollout paths.

- `rollouts/<name>/main.py` - server entrypoint.
- `rollouts/<name>/README.md`
- `rollouts/<name>/pyproject.toml`
- `configs/eval/<name>.toml` - points `dataset` at `data/<name>.jsonl`.
- `configs/training/<name>.toml` - points `dataset` at the platform dataset name.

## Rollout rules

- Keep the entrypoint inside `rollouts/<name>/`.
- Default to `main.py` unless the user asks for another Python entrypoint.
- Expose exactly one concrete `AgentWorkflow`.
- Expose exactly one concrete `Grader`; eval configs no longer carry a separate `[grader]` section.
- The workflow's `run` receives `ctx.prompt`, a list of system/user messages converted from the dataset's `system_prompt` + `user_prompt` columns.
- The workflow must register at least one sample source, either through an SDK integration (`OsmosisStrandsAgent`, `OsmosisAgent` + `OsmosisMemorySession`) or by calling `get_rollout_context().register_sample_source(...)`.
- The grader implements async `grade(ctx)`, reads `ctx.label` as the dataset `ground_truth`, and assigns every sample a reward with `ctx.set_sample_reward(sample_id, reward)`.
- Keep tools as async Python functions with type hints and docstrings.
- Keep the grader explicit, partial-credit friendly, and easy to inspect.

## Server entrypoint contract

`main.py` must launch a rollout server. The platform clones your code from the workspace's connected Git remote and runs this exact entrypoint to serve rollouts during training. Use this skeleton:

```python
import os

import uvicorn

from osmosis_ai.rollout.agent_workflow import AgentWorkflow
from osmosis_ai.rollout.backend.local import LocalBackend
from osmosis_ai.rollout.context import AgentWorkflowContext, GraderContext
from osmosis_ai.rollout.grader import Grader
from osmosis_ai.rollout.server import create_rollout_server


class MyWorkflow(AgentWorkflow):
    async def run(self, ctx: AgentWorkflowContext) -> None:
        # Drive the model from ctx.prompt and register sample sources for grading.
        raise NotImplementedError


class MyGrader(Grader):
    async def grade(self, ctx: GraderContext) -> None:
        for sample_id in ctx.get_samples():
            ctx.set_sample_reward(sample_id, 0.0)


def main() -> None:
    backend = LocalBackend(workflow=MyWorkflow, grader=MyGrader)
    app = create_rollout_server(backend=backend)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("_OSMOSIS_ROLLOUT_PORT", "8000")))


if __name__ == "__main__":
    main()
```

For worked examples, run `osmosis --json template list`, then apply one of the current multiply recipes such as `osmosis --json template apply multiply-local-strands` and adapt it to your dataset.

## Validation

After creating or adapting the rollout, run:

```bash
osmosis --json doctor
pip install -e rollouts/<name>
osmosis --json eval run configs/eval/<name>.toml --limit 1 --fresh
```

A clean `eval run` is the local smoke test for the server entrypoint: the same workflow + grader objects the server would expose are exercised end-to-end against `data/<name>.jsonl`.

If a matching training config exists, inspect it now but do not submit training from this skill. `osmosis --json train submit configs/training/<run>.toml --yes` performs the current SDK preflight when the user is ready to train.
