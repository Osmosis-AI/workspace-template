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
)
from osmosis_ai.rollout.server import create_rollout_server


class MyWorkflow(AgentWorkflow):
    async def run(self, ctx: AgentWorkflowContext) -> None:
        raise NotImplementedError


class MyGrader(Grader):
    async def grade(self, ctx: GraderContext) -> None:
        ctx.set_reward(0.0)


def main() -> None:
    backend = LocalBackend(workflow=MyWorkflow, grader=MyGrader)
    app = create_rollout_server(backend=backend)
    uvicorn.run(
        app, host="0.0.0.0", port=int(os.environ.get("_OSMOSIS_ROLLOUT_PORT", "8000"))
    )


if __name__ == "__main__":
    main()
```

## Harbor Skeleton

Use this pattern only when the rollout needs Harbor task isolation. Keep the workflow and grader in an importable package under the rollout project.

```python
from __future__ import annotations

import os
from pathlib import Path

import uvicorn
from harbor.models.environment_type import EnvironmentType
from harbor.models.trial.config import EnvironmentConfig
from harbor.trial.queue import TrialQueue

from my_rollout.grader import MyGrader
from my_rollout.workflow import MyWorkflow
from osmosis_ai.rollout.backend.harbor import HarborBackend
from osmosis_ai.rollout.server import create_rollout_server

ROLLOUT_DIR = Path(__file__).resolve().parent


def main() -> None:
    backend = HarborBackend(
        orchestrator=TrialQueue(n_concurrent=4),
        tasks_dir=ROLLOUT_DIR / "task",
        task_mode="template",
        agent=MyWorkflow,
        grader=MyGrader,
        code_dir=ROLLOUT_DIR,
        environment_config=EnvironmentConfig(type=EnvironmentType.SKYPILOT),
    )
    app = create_rollout_server(
        backend=backend,
        lifespan=backend.prewarm_lifespan(),
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("_OSMOSIS_ROLLOUT_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
```

The v0.3 Harbor backend builds a wheel from `code_dir` and installs it inside the task container. Keep `task/environment/Dockerfile` limited to task dependencies. `HarborBackendV2` and the old `task_dir=`, `user_code_dir=`, and `workflow=` arguments do not exist.

The skeleton uses SkyPilot for managed runs. Keep that environment for local eval too: `osmosis eval run <config>` detects that the sandbox cannot reach this machine and starts a `cloudflared` tunnel to the local model bridge automatically, so keep `cloudflared` on `PATH`. Use Docker instead only when you deliberately want the host Docker runtime.

## Integration Rules

- Install the feature extras used by the rollout: `server` for `create_rollout_server`, plus `strands`, `openai-agents`, or `harbor` when those modules are imported.
- Strands: import from `osmosis_ai.rollout.integrations.agents.strands`, construct `OsmosisStrandsAgent` inside `AgentWorkflow.run`, pass `messages=ctx.prompt`, use `OsmosisRolloutModel(params={...})`, call `await agent.invoke_async()`, and return `None` so the backend collects the registered sample.
- OpenAI Agents: import from `osmosis_ai.rollout.integrations.agents.openai_agents`, construct `OsmosisAgent` inside `run`, use `OsmosisRolloutModel()`, create exactly one `OsmosisMemorySession()` inside `run`, pass `session=session` to `Runner.run`, and return `None`.
- Custom integrations: either return `AgentWorkflowOutput(messages=..., metrics=...)` (or a bare message list), or register exactly one sample source with `get_rollout_context().set_sample_source(...)` and return `None`.
- `AgentWorkflowOutput` rejects unknown top-level fields and non-finite metric values.
- Do not call a fixed policy model directly from `run`; provider SDK calls bypass the active rollout context and break sample/reward linkage.

## Grader Rules

- Read the rollout's single sample from `ctx.sample`.
- Parse `ctx.label` according to the dataset's actual `ground_truth` format.
- Call `ctx.set_reward(reward)` to assign the sample's scalar reward.
- Keep rewards numeric and task-scaled, normally `[0.0, 1.0]`.
