import logging
from typing import Any

from osmosis_ai.rollout.context import GraderContext
from osmosis_ai.rollout.grader import Grader
from osmosis_ai.rollout.types import GraderConfig

from multiply_rollout.utils import extract_solution

logger = logging.getLogger(__name__)


class MultiplyGraderConfig(GraderConfig):
    name: str = "MultiplyOpenAIAgentsGrader"
    description: str | None = "Grades multiplication rollouts using OpenAI Agents"


multiply_grader_config = MultiplyGraderConfig()


class MultiplyGrader(Grader):
    def compute_reward(self, solution_str: str, ground_truth: str) -> float:
        extracted = extract_solution(solution_str)
        if extracted is None:
            return 0.0
        try:
            sol_val = float(extracted)
            gt_val = float(ground_truth)
        except (TypeError, ValueError):
            return 0.0

        if abs(gt_val - sol_val) < 1e-2:
            return 1.0
        return 0.0

    async def grade(self, ctx: GraderContext) -> None:
        sample = ctx.sample
        if sample is None:
            raise ValueError("No rollout sample to grade")

        content: Any = ""
        if sample.messages:
            content = sample.messages[-1].get("content", "")
        reward = self.compute_reward(_extract_text(content), ctx.label or "")
        ctx.set_reward(reward)
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
