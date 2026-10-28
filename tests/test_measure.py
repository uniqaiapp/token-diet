"""measure.py: request shape, transcript splitting, report formatting. No network."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import measure  # noqa: E402


class TestCountRequest(unittest.TestCase):
    def test_shape(self):
        body = measure.build_count_request("claude-opus-5-5", "hi")
        self.assertEqual(body, {"model": "claude-opus-5-5", "messages": [{"role": "user", "content": "hi"}]})
        self.assertTrue(measure.COUNT_URL.endswith("/v1/messages/count_tokens"))

    def test_counter_falls_back_to_estimate_without_key(self):
        os.environ.pop("ANTHROPIC_API_KEY", None)
        c = measure.Counter("claude-opus-5-5", force_estimate=False)
        self.assertIsNone(c.key)
        self.assertIn("ESTIMATE", c.label)
        self.assertEqual(c(""), 0)
        self.assertGreater(c("some text"), 0)

    def test_force_estimate_ignores_key(self):
        os.environ["ANTHROPIC_API_KEY"] = "placeholder-value-for-test"
        try:
            c = measure.Counter("claude-opus-5-5", force_estimate=True)
            self.assertIsNone(c.key)
        finally:
            os.environ.pop("ANTHROPIC_API_KEY", None)


class TestTranscript(unittest.TestCase):
    def test_split(self):
        t = {"system": "sys", "rag": "ctx",
             "messages": [{"role": "user", "content": "q1"},
                          {"role": "assistant", "content": [{"type": "text", "text": "a1"}, {"type": "tool_use", "input": {"k": 1}}]},
                          {"role": "user", "content": [{"type": "tool_result", "content": "TOOL"}]},
                          {"role": "tool", "content": "TOOL2"},
                          {"role": "user", "content": "q2"}]}
        p = measure.split_transcript(t)
        self.assertEqual(p["system prompt"], "sys")
        self.assertEqual(p["retrieved context (rag)"], "ctx")
        self.assertIn("TOOL\n", p["tool output"])
        self.assertIn("TOOL2\n", p["tool output"])
        self.assertEqual(p["current user turn"], "q2\n")
        self.assertIn("q1", p["history"])
        self.assertIn('{"k": 1}', p["history"])
        self.assertEqual(p["tools / schemas"], "")

    def test_breakdown_report_mentions_method(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"system": "x" * 400, "messages": [{"role": "user", "content": "hi"}]}, f)
            out = measure.breakdown_report(path, measure.Counter("m", True))
            self.assertIn("ESTIMATE", out)
            self.assertIn("system prompt", out)
            self.assertIn("total", out)


class TestCompare(unittest.TestCase):
    def test_compare_and_price_line(self):
        with tempfile.TemporaryDirectory() as d:
            b, a = os.path.join(d, "b.txt"), os.path.join(d, "a.txt")
            open(b, "w", encoding="utf-8").write("привет " * 50)
            open(a, "w", encoding="utf-8").write("hello " * 20)
            out = measure.compare(b, a, measure.Counter("m", True), price_in=3.0)
            self.assertIn("delta", out)
            self.assertIn("of an estimate", out)
            self.assertIn("price supplied by you", out)


if __name__ == "__main__":
    unittest.main()
