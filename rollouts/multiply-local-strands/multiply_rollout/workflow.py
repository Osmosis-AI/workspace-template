from typing import Any

from osmosis_ai.rollout.agent_workflow import AgentWorkflow
from osmosis_ai.rollout.context import AgentWorkflowContext
from osmosis_ai.rollout.integrations.agents.strands import OsmosisRolloutModel
from osmosis_ai.rollout.integrations.agents.strands import (
    OsmosisStrandsAgent as StrandsAgent,
)
from osmosis_ai.rollout.types import AgentWorkflowConfig
from strands.agent.agent_result import AgentResult
from strands.models.model import Model

from multiply_rollout.tools import multiply_tool
from multiply_rollout.utils import extract_solution


class MultiplyAgentWorkflowConfig(AgentWorkflowConfig):
    name: str = "MultiplyAgentWorkflow"
    description: str | None = "Multiply two numbers using Strands"
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
        if config is None:
            raise ValueError("MultiplyWorkflow requires a workflow config")

        agent = StrandsAgent(
            name="multiply",
            model=config.model,
            tools=config.tools,
            messages=ctx.prompt,
            callback_handler=None,
        )

        for _ in range(8):
            result = await agent.invoke_async()
            if await self.check_done(result):
                break
