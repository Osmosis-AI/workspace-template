"""Local OpenAI Agents multiply rollout server."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import uvicorn
from agents import ModelSettings, Runner, function_tool
from agents.models.interface import Model

from osmosis_ai.rollout.agent_workflow import AgentWorkflow
from osmosis_ai.rollout.backend.local import LocalBackend
from osmosis_ai.rollout.context import AgentWorkflowContext, GraderContext
from osmosis_ai.rollout.grader import Grader
from osmosis_ai.rollout.integrations.agents.openai_agents import (
    OsmosisAgent,
    OsmosisMemorySession,
    OsmosisRolloutModel,
)
from osmosis_ai.rollout.server import create_rollout_server
from osmosis_ai.rollout.types import AgentWorkflowConfig, GraderConfig

logger = logging.getLogger(__name__)
MAX_TURNS = 8


def extract_solution(solution_str: str) -> str | None:
    """Extract a final answer from the expected #### <number> format."""
    solution = re.search(r"####\s*([-+]?\d*\.?\d+)", solution_str)
    if not solution:
        return None
    return solution.group(1)


@function_tool
async def multiply_tool(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


class MultiplyAgentWorkflowConfig(AgentWorkflowConfig):
    name: str = "MultiplyAgentWorkflow"
    description: str = "Multiply two numbers using OpenAI Agents"
    model: Model
    model_settings: ModelSettings
    tools: Any


multiply_workflow_config = MultiplyAgentWorkflowConfig(
    model=OsmosisRolloutModel(),
    model_settings=ModelSettings(temperature=1.0, top_p=1.0, max_tokens=4096),
    tools=[multiply_tool],
)


class MultiplyWorkflow(AgentWorkflow):
    async def run(self, ctx: AgentWorkflowContext) -> None:
        config = ctx.config
        agent = OsmosisAgent(
            name="multiply",
            model=config.model,
            model_settings=config.model_settings,
            tools=config.tools,
        )

        session = OsmosisMemorySession(name="multiply")
        await Runner.run(
            agent,
            ctx.prompt,
            session=session,
            max_turns=MAX_TURNS,
        )


class MultiplyGraderConfig(GraderConfig):
    name: str = "MultiplyOpenAIAgentsGrader"
    description: str = "Grades multiplication rollouts using OpenAI Agents"


multiply_grader_config = MultiplyGraderConfig()


class MultiplyGrader(Grader):
    def compute_reward(self, solution_str: str, ground_truth: str) -> float:
        extracted = extract_solution(solution_str)
        try:
            sol_val = float(extracted)
            gt_val = float(ground_truth)
        except (TypeError, ValueError):
            return 0.0

        if abs(gt_val - sol_val) < 1e-2:
            return 1.0
        return 0.0

    async def grade(self, ctx: GraderContext) -> None:
        samples = ctx.get_samples()
        if "multiply" not in samples:
            for sample_id in samples:
                ctx.set_sample_reward(sample_id, 0.0)
            return

        last_message = samples["multiply"].messages[-1]
        content = last_message.get("content", "")
        reward = self.compute_reward(_extract_text(content), ctx.label or "")
        ctx.set_sample_reward("multiply", reward)
        logger.info("[MultiplyGrader] reward = %.1f", reward)


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "output_text"
        ]
        return "\n".join(parts)
    return ""


def main() -> None:
    backend = LocalBackend(
        workflow=MultiplyWorkflow,
        workflow_config=multiply_workflow_config,
        grader=MultiplyGrader,
        grader_config=multiply_grader_config,
    )
    app = create_rollout_server(backend=backend)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("_OSMOSIS_ROLLOUT_PORT", "8000")))


if __name__ == "__main__":
    main()
