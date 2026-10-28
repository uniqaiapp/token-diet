"""Every script answers --help, and every committed example output is reproduced byte-for-byte.

The byte-for-byte rule is how numbers in README stay honest: if a report changes, this test fails
and the person changing it sees exactly what moved.
"""
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EX = os.path.join(ROOT, "examples")
ENV = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY") and not k.startswith("TOKEN_DIET_")}
ENV["PYTHONIOENCODING"] = "utf-8"


def run(*args, cwd=ROOT):
    p = subprocess.run([sys.executable] + list(args), cwd=cwd, env=ENV, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestHelp(unittest.TestCase):
    def test_help_exits_zero(self):
        for name in ("diet.py", "measure.py", "estimate.py"):
            code, out, err = run(os.path.join(ROOT, "scripts", name), "--help")
            self.assertEqual(code, 0, err)
            self.assertIn("usage", out.lower())

    def test_runs_from_any_cwd(self):
        code, out, _ = run(os.path.join(ROOT, "scripts", "estimate.py"), os.path.join(EX, "ru-01-bugfix", "before.txt"), cwd=os.sep)
        self.assertEqual(code, 0)
        self.assertIn("ESTIMATE", out)


class TestExamplesReproduce(unittest.TestCase):
    def pairs(self):
        for d in sorted(os.listdir(EX)):
            if os.path.isfile(os.path.join(EX, d, "before.txt")):
                yield d

    def test_dry_run_fixtures(self):
        for d in self.pairs():
            code, out, err = run("scripts/diet.py", "examples/%s/before.txt" % d, "--dry-run", "--provider", "openai")
            self.assertEqual(code, 0, err)
            self.assertEqual(out, read(os.path.join(EX, d, "dry-run.txt")), d)

    def test_measure_fixtures(self):
        for d in self.pairs():
            code, out, err = run("scripts/measure.py", "examples/%s/before.txt" % d, "examples/%s/after.txt" % d, "--estimate")
            self.assertEqual(code, 0, err)
            self.assertEqual(out, read(os.path.join(EX, d, "report.txt")), d)

    def test_breakdown_fixture(self):
        code, out, err = run("scripts/measure.py", "--breakdown", "examples/transcript/transcript.sample.json", "--estimate")
        self.assertEqual(code, 0, err)
        self.assertEqual(out, read(os.path.join(EX, "transcript", "breakdown.txt")))

    def test_after_keeps_every_protected_span(self):
        """The reference rewrite must contain each protected span of the original verbatim."""
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        from diet import protect
        for d in self.pairs():
            before, after = read(os.path.join(EX, d, "before.txt")), read(os.path.join(EX, d, "after.txt"))
            _, table = protect(before)
            for name, span in table:
                self.assertIn(span, after, "%s: %s %r missing from after.txt" % (d, name, span))
            self.assertLess(len(after), len(before), d)

    def test_no_key_means_no_network(self):
        """Without a key, a real run must fail fast with a clear message and never reach the network."""
        code, out, err = run("scripts/diet.py", "examples/ru-03-sql/before.txt", "--provider", "anthropic")
        self.assertNotEqual(code, 0)
        self.assertIn("ANTHROPIC_API_KEY is not set", err)


if __name__ == "__main__":
    unittest.main()
