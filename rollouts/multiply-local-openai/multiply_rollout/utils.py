import re


def extract_solution(solution_str: str) -> str | None:
    """Extract the final answer from the expected #### <number> format."""
    # Reasoning can quote the prompt's example answer; the reply's own answer comes last.
    solutions = re.findall(r"####\s*([-+]?\d*\.?\d+)", solution_str)
    return solutions[-1] if solutions else None
