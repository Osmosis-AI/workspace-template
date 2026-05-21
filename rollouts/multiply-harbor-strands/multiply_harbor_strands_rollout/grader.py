import logging

from multiply_harbor_strands_rollout.utils import extract_solution
from osmosis_ai.rollout.context import GraderContext
from osmosis_ai.rollout.grader import Grader
from osmosis_ai.rollout.types import GraderConfig

logger = logging.getLogger(__name__)


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
