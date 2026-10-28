"""Structure checks shared by every uniqaiapp repo: skill frontmatter, adapters, versions, forbidden strings."""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "token-diet"
TEXT_EXT = {".md", ".mdc", ".py", ".json", ".yml", ".yaml", ".txt", ".svg", ".cff", ".toml", ".editorconfig", ".gitignore", ".gitattributes", ""}
SKIP_DIRS = {".git", "__pycache__"}
# Spelled with a joiner so this file does not trip its own scan.
J = ""
FORBIDDEN = [s.lower() for s in (
    "aeo" + J + "ria", "rich" + J + "peach", "/Use" + J + "rs/", "/Volu" + J + "mes/", "node_" + J + "modules",
    "sk-" + J + "ant-", "sk_" + J + "live", "api_" + J + "key=", "API_" + J + "KEY=<real", "TODO: " + J + "fill", "lorem " + J + "ipsum")]
MARKER = "# conventions-allow: abs-path"
SCAN_EXEMPT = {os.path.join("tests", "test_adapters.py")}
EXEMPT_STRINGS = {".gitignore": {"node_" + J + "modules"}}  # the ignore file must name the folder it ignores


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "SKILL.md has no YAML frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z_]+:", line):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
        elif re.match(r"^\s+[a-z_]+:", line):
            k, v = line.strip().split(":", 1)
            fm["metadata." + k.strip()] = v.strip()
    return fm


def tracked_text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext in TEXT_EXT or fn in (".gitignore", ".gitattributes", ".editorconfig", "LICENSE"):
                yield os.path.relpath(os.path.join(dirpath, fn), ROOT)


class TestSkill(unittest.TestCase):
    def setUp(self):
        self.fm = frontmatter(read("SKILL.md"))

    def test_name_matches_repo(self):
        self.assertEqual(self.fm["name"], REPO)
        self.assertTrue(re.fullmatch(r"[a-z0-9-]{1,64}", self.fm["name"]))

    def test_description(self):
        d = self.fm["description"]
        self.assertTrue(1 <= len(d) <= 1024, len(d))
        self.assertNotIn("\n", d)
        for trigger in ("token", "Use when", "Not for"):
            self.assertIn(trigger, d)

    def test_body_length(self):
        self.assertLess(len(read("SKILL.md").splitlines()), 500)

    def test_versions_match(self):
        plugin = json.loads(read(os.path.join(".claude-plugin", "plugin.json")))
        self.assertEqual(plugin["name"], REPO)
        self.assertEqual(plugin["version"], self.fm["metadata.version"])
        self.assertEqual(plugin["skills"], ["./"])
        top = re.search(r"^## \[(\d+\.\d+\.\d+)\]", read("CHANGELOG.md"), re.M)
        self.assertEqual(top.group(1), self.fm["metadata.version"])
        self.assertEqual(plugin["author"]["name"], "UniqAI")


class TestAdapters(unittest.TestCase):
    def test_cursor_rule(self):
        t = read(os.path.join(".cursor", "rules", REPO + ".mdc"))
        self.assertIn("@SKILL.md", t)
        self.assertIn("alwaysApply: false", t)

    def test_agents_and_codex_point_to_skill(self):
        self.assertIn("SKILL.md", read("AGENTS.md"))
        self.assertIn("SKILL.md", read(os.path.join("codex", "INSTRUCTIONS.md")))

    def test_required_files(self):
        for rel in READMES + ("LICENSE", "CONTRIBUTING.md", "CHANGELOG.md", ".gitignore",
                    ".gitattributes", ".editorconfig", os.path.join(".github", "workflows", "ci.yml"),
                    os.path.join(".github", "repo.json"), os.path.join("assets", "banner.svg"),
                    os.path.join("assets", "banner-light.svg"), os.path.join("assets", "demo.svg"),
                    os.path.join("assets", "social-preview.png"), os.path.join("assets", "icon.svg"),
                    os.path.join("examples", "README.md")):
            self.assertTrue(os.path.exists(os.path.join(ROOT, rel)), rel)

    def test_repo_json(self):
        meta = json.loads(read(os.path.join(".github", "repo.json")))
        self.assertEqual(meta["name"], REPO)
        self.assertTrue(meta["description"])
        self.assertLessEqual(len(meta["topics"]), 20)
        self.assertIn("utm_campaign=" + REPO, meta["homepage"])


READMES = ("README.md", "README.ru.md", "README.zh-CN.md", "README.es.md", "README.pt-BR.md", "README.ja.md", "README.ko.md")


class TestHygiene(unittest.TestCase):
    def test_no_forbidden_strings(self):
        hits = []
        for rel in tracked_text_files():
            if rel in SCAN_EXEMPT:
                continue
            text = read(rel)
            for n, line in enumerate(text.splitlines(), 1):
                if MARKER in line:
                    continue
                low = line.lower()
                for bad in FORBIDDEN:
                    if bad in low and bad not in EXEMPT_STRINGS.get(os.path.basename(rel), set()):
                        hits.append("%s:%d: %s" % (rel, n, bad))
        self.assertEqual(hits, [])

    def test_copyright_is_brand_only(self):
        for rel in tracked_text_files():
            if rel in SCAN_EXEMPT:
                continue
            for line in read(rel).splitlines():
                if "Copyright (c)" in line:
                    self.assertIn("UniqAI", line, rel)

    def test_utm_on_every_uniqai_link(self):
        for rel in READMES + ("SKILL.md",):
            for url in re.findall(r"https://uniqai\.app[^\s)\"'>]*", read(rel)):
                self.assertIn("utm_campaign=" + REPO, url, "%s: %s" % (rel, url))

    def test_one_made_by_footer(self):
        for rel in READMES:
            self.assertEqual(read(rel).count("Made by <a href"), 1, rel)

    def test_asset_sizes(self):
        limits = {"banner.svg": 15, "banner-light.svg": 15, "demo.svg": 60, "social-preview.png": 120, "icon.svg": 4}
        for name, kb in limits.items():
            size = os.path.getsize(os.path.join(ROOT, "assets", name)) / 1024
            self.assertLessEqual(size, kb, "%s is %.1f KB" % (name, size))


if __name__ == "__main__":
    unittest.main()
