import asyncio
import logging
from typing import Any

from strands.agent.agent_result import AgentResult
from strands.models.model import Model

from multiply_rollout.tools import multiply_tool
from multiply_rollout.utils import extract_solution
from osmosis_ai.rollout.agent_workflow import AgentWorkflow
from osmosis_ai.rollout.context import AgentWorkflowContext
from osmosis_ai.rollout.integrations.agents.strands import OsmosisRolloutModel
from osmosis_ai.rollout.integrations.agents.strands import (
    OsmosisStrandsAgent as StrandsAgent,
)
from osmosis_ai.rollout.types import AgentWorkflowConfig

logger = logging.getLogger(__name__)


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
        if any(fragment in str(current).lower() for fragment in transient_message_fragments):
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
