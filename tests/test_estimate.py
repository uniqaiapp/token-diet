"""The estimator is only a heuristic; these tests pin its shape, not its accuracy."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import estimate  # noqa: E402


class TestEstimate(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(estimate.estimate_tokens(""), 0)

    def test_monotonic(self):
        self.assertLess(estimate.estimate_tokens("short"), estimate.estimate_tokens("a much longer english sentence here"))

    def test_cyrillic_costs_more_per_char_than_latin(self):
        ru = "привет мир " * 12
        en = "hello world " * 11
        self.assertEqual(len(ru), len(en))
        self.assertGreater(estimate.estimate_tokens(ru), estimate.estimate_tokens(en))

    def test_breakdown_sums_to_length(self):
        text = "code: ```py\nx=1\n```\nтекст text 漢字"
        counts = estimate.breakdown(text)
        self.assertEqual(sum(counts.values()), len(text))
        self.assertGreater(counts["code"], 0)
        self.assertGreater(counts["cyrillic"], 0)
        self.assertGreater(counts["cjk"], 0)

    def test_describe(self):
        self.assertEqual(estimate.describe({"latin": 0, "cyrillic": 0, "cjk": 0, "code": 0, "other": 0}), "empty")
        self.assertTrue(estimate.describe(estimate.breakdown("hello")).startswith("latin 100%"))

    def test_rates_are_sane(self):
        for k, v in estimate.RATES.items():
            self.assertTrue(0.5 <= v <= 6, k)


if __name__ == "__main__":
    unittest.main()
