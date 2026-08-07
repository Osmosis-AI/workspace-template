import logging

from osmosis_ai.rollout.context import GraderContext
from osmosis_ai.rollout.grader import Grader
from osmosis_ai.rollout.types import GraderConfig

from multiply_rollout.utils import extract_solution

logger = logging.getLogger(__name__)


class MultiplyGraderConfig(GraderConfig):
    name: str = "MultiplyGrader"
    description: str | None = "Grades multiplication rollouts"


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

        content = sample.messages[-1].get("content", "") if sample.messages else ""
        if isinstance(content, list):
            content = next((block["text"] for block in content if "text" in block), "")

        reward = self.compute_reward(content, ctx.label or "")
        ctx.set_reward(reward)
        logger.info("[MultiplyGrader] reward = %.1f", reward)
