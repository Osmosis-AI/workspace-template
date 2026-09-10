"""Check dataset labels and every binary multiplication order without model calls."""

import json
from decimal import Decimal, localcontext
from functools import cache
from pathlib import Path
import unittest


@cache
def products(values):
    if len(values) == 1:
        return {values[0]}
    results = set()
    # Multiplication commutes; keep the first factor on the left of each split.
    for mask in range(1, (1 << len(values)) - 1, 2):
        left = tuple(value for i, value in enumerate(values) if mask & (1 << i))
        right = tuple(value for i, value in enumerate(values) if not mask & (1 << i))
        results.update(a * b for a in products(left) for b in products(right))
    return results


class MultiplyDatasetTest(unittest.TestCase):
    def test_labels_and_tool_orders(self):
        rows = [
            json.loads(line)
            for line in Path(__file__).with_name("multiply.jsonl").read_text().splitlines()
        ]
        self.assertEqual(len(rows), 1000)
        self.assertEqual(len({row["user_prompt"] for row in rows}), len(rows))
        self.assertEqual(
            {len(row["user_prompt"].splitlines()) for row in rows}, {3, 4, 5}
        )
        with localcontext() as context:
            context.prec = 50
            for line, row in enumerate(rows, 1):
                with self.subTest(line=line):
                    self.assertEqual(
                        set(row), {"user_prompt", "system_prompt", "ground_truth"}
                    )
                    self.assertIn("####", row["system_prompt"])
                    values = tuple(
                        Decimal(part.split(" = ")[1])
                        for part in row["user_prompt"].splitlines()
                    )
                    exact = Decimal(1)
                    for value in values:
                        self.assertLessEqual(abs(value), 100)
                        self.assertEqual(value, value.quantize(Decimal("0.0001")))
                        exact *= value
                    self.assertEqual(
                        Decimal(row["ground_truth"]), exact.quantize(Decimal("0.0001"))
                    )
                    label = float(row["ground_truth"])
                    try:
                        for result in products(tuple(map(float, values))):
                            # Keep a 100x margin below the graders' 0.01 tolerance.
                            self.assertLess(abs(result - label), 0.0001)
                    finally:
                        products.cache_clear()


if __name__ == "__main__":
    unittest.main()
