from typing import Any, cast

from agents import ModelSettings, Runner
from agents.models.interface import Model
from osmosis_ai.rollout.agent_workflow import AgentWorkflow
from osmosis_ai.rollout.context import AgentWorkflowContext
from osmosis_ai.rollout.integrations.agents.openai_agents import (
    OsmosisAgent,
    OsmosisMemorySession,
    OsmosisRolloutModel,
)
from osmosis_ai.rollout.types import AgentWorkflowConfig

from multiply_rollout.tools import multiply_tool

MAX_TURNS = 8


class MultiplyAgentWorkflowConfig(AgentWorkflowConfig):
    name: str = "MultiplyAgentWorkflow"
    description: str | None = "Multiply two numbers using OpenAI Agents"
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
        if config is None:
            raise ValueError("MultiplyWorkflow requires a workflow config")

        agent = OsmosisAgent(
            name="multiply",
            model=config.model,
            model_settings=config.model_settings,
            tools=config.tools,
        )

        session = OsmosisMemorySession()
        await Runner.run(
            agent,
            cast(Any, ctx.prompt),
            session=session,
            max_turns=MAX_TURNS,
        )
