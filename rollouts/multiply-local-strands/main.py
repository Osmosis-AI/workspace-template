"""Local Strands multiply rollout server."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Any

import uvicorn
from strands import tool
from strands.agent.agent_result import AgentResult
from strands.models.model import Model

from osmosis_ai.rollout.agent_workflow import AgentWorkflow
from osmosis_ai.rollout.backend.local import LocalBackend
from osmosis_ai.rollout.context import AgentWorkflowContext, GraderContext
from osmosis_ai.rollout.grader import Grader
from osmosis_ai.rollout.integrations.agents.strands import OsmosisRolloutModel
from osmosis_ai.rollout.integrations.agents.strands import (
    OsmosisStrandsAgent as StrandsAgent,
)
from osmosis_ai.rollout.server import create_rollout_server
from osmosis_ai.rollout.types import AgentWorkflowConfig, GraderConfig

logger = logging.getLogger(__name__)


def extract_solution(solution_str: str) -> str | None:
    """Extract a final answer from the expected #### <number> format."""
    solution = re.search(r"####\s*([-+]?\d*\.?\d+)", solution_str)
    if not solution:
        return None
    return solution.group(1)


@tool(name="multiply")
async def multiply_tool(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


class MultiplyAgentWorkflowConfig(AgentWorkflowConfig):
    name: str = "MultiplyAgentWorkflow"
    description: str = "Multiply two numbers using Strands"
    model: Model
    tools: Any


multiply_workflow_config = MultiplyAgentWorkflowConfig(
    model=OsmosisRolloutModel(
        params={
            "temperature": 1.0,
            "top_p": 1.0,
            "max_tokens": 16384,
        }
    ),
    tools=[multiply_tool],
)


def _is_transient_model_error(exc: Exception) -> bool:
    transient_type_names = {
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "ReadError",
        "ServerDisconnectedError",
        "EventLoopException",
        "OpenAIError",
    }
    transient_message_fragments = (
        "connection error",
        "server disconnected",
        "connection reset",
        "timed out",
        "temporarily unavailable",
    )

    current: BaseException | None = exc
    while current is not None:
        if type(current).__name__ in transient_type_names:
            return True

        message = str(current).lower()
        if any(fragment in message for fragment in transient_message_fragments):
            return True

        current = current.__cause__ or current.__context__

    return False


async def _invoke_with_retry(
    agent: StrandsAgent,
    *,
    max_attempts: int = 3,
    initial_backoff_seconds: float = 2.0,
) -> AgentResult:
    """Retry transient model failures; the multiply tool is pure."""
    for attempt in range(1, max_attempts + 1):
        try:
            return await agent.invoke_async()
        except Exception as exc:
            if attempt >= max_attempts or not _is_transient_model_error(exc):
                raise

            backoff_seconds = initial_backoff_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Transient model failure on attempt %d/%d: %s. Retrying in %.1fs",
                attempt,
                max_attempts,
                exc,
                backoff_seconds,
            )
            await asyncio.sleep(backoff_seconds)

    raise RuntimeError("unreachable")


class MultiplyWorkflow(AgentWorkflow):
    async def check_done(self, result: AgentResult) -> bool:
        message = result.message
        content = message.get("content", "")

        if not any("toolUse" in block for block in content):
            return True

        text_content = next((block for block in content if block.get("text")), None)
        if text_content:
            return extract_solution(text_content.get("text", "")) is not None

        return False

    async def run(self, ctx: AgentWorkflowContext) -> None:
        config = ctx.config
        agent = StrandsAgent(
            name="multiply",
            model=config.model,
            tools=config.tools,
            messages=ctx.prompt,
            callback_handler=None,
        )

        for _ in range(8):
            result = await _invoke_with_retry(agent)
            if await self.check_done(result):
                break


class MultiplyGraderConfig(GraderConfig):
    name: str = "MultiplyGrader"
    description: str = "Grades multiplication rollouts"


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
        rollout_samples = ctx.get_samples()
        if "multiply" not in rollout_samples:
            for sample_id in rollout_samples:
                ctx.set_sample_reward(sample_id, 0.0)
            return

        content = rollout_samples["multiply"].messages[-1]["content"]
        if isinstance(content, list):
            content = next((block["text"] for block in content if "text" in block), "")

        reward = self.compute_reward(content, ctx.label or "")
        ctx.set_sample_reward("multiply", reward)
        logger.info("[MultiplyGrader] reward = %.1f", reward)


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
