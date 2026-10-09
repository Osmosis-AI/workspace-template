import re

_REASONING = re.compile(r"<think>.*?</think>", re.DOTALL)
_SOLUTION = re.compile(r"####\s*([-+]?\d*\.?\d+)")


def extract_solution(solution_str: str) -> str | None:
    """Extract the final answer from the expected #### <number> format."""
    # Reasoning often quotes the prompt's example answer, so read only the reply's last answer.
    solutions = _SOLUTION.findall(_REASONING.sub("", solution_str))
    return solutions[-1] if solutions else None
