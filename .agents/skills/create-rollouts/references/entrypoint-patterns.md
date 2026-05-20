# Rollout Entrypoint Patterns

Read this when hand-writing or substantially rewriting the configured entrypoint under `rollouts/<name>/`, or when an eval/preflight failure suggests the server, sample source, or integration pattern is wrong. Prefer `osmosis --json rollout init <name>` or a template when starting blank.

## Server Skeleton

```python
from __future__ import annotations

import os

import uvicorn

from osmosis_ai.rollout import (
    AgentWorkflow,
    AgentWorkflowContext,
    Grader,
    GraderContext,
    LocalBackend,
    create_rollout_server,
)


class MyWorkflow(AgentWorkflow):
    async def run(self, ctx: AgentWorkflowContext) -> None:
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

## Integration Rules

- Strands: construct `OsmosisStrandsAgent` inside `AgentWorkflow.run`, pass `messages=ctx.prompt`, use `OsmosisRolloutModel(params={...})`, and call `await agent.invoke_async()`.
- OpenAI Agents: construct `OsmosisAgent` inside `run`, use `OsmosisRolloutModel()`, create an `OsmosisMemorySession` inside `run`, and pass `session=session` to `Runner.run`.
- Custom integrations: register a sample source with `get_rollout_context().register_sample_source(...)` before the workflow finishes.
- Do not call a fixed policy model directly from `run`; provider SDK calls bypass the active rollout context and break sample/reward linkage.

## Grader Rules

- Iterate real sample IDs from `ctx.get_samples()` or `ctx.samples.items()`.
- Parse `ctx.label` according to the dataset's actual `ground_truth` format.
- Call `ctx.set_sample_reward(sample_id, reward)` for every sample.
- Keep rewards numeric and task-scaled, normally `[0.0, 1.0]`.
