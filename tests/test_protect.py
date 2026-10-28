"""protect() / restore() round-trips and the placeholder integrity check."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import diet  # noqa: E402


class TestProtect(unittest.TestCase):
    def names(self, text):
        _, table = diet.protect(text)
        return [n for n, _ in table]

    def spans(self, text):
        _, table = diet.protect(text)
        return [s for _, s in table]

    def test_round_trip_identity(self):
        text = ("Поправь `fetch()` в src/app/page.tsx, см. https://example.com/docs?x=1 и флаг --force.\n"
                "```py\nx = load_config()\n```\nСтрока \"hello world\" и «ещё одна».")
        protected, table = diet.protect(text)
        self.assertNotIn("src/app", protected)
        self.assertEqual(diet.restore(protected, table), text)

    def test_rule_coverage(self):
        self.assertEqual(self.spans("файл config.yaml и README.md"), ["config.yaml", "README.md"])
        self.assertEqual(self.spans("хук useGenerate и класс HttpClient"), ["useGenerate", "HttpClient"])
        self.assertEqual(self.spans("переменная SMTP_PASSWORD и load_config"), ["SMTP_PASSWORD", "load_config"])
        self.assertEqual(self.spans("вызови main() и np.array"), ["main()", "np.array"])
        self.assertEqual(self.spans("путь ~/work/app/ и ./scripts/x"), ["~/work/app/", "./scripts/x"])
        self.assertEqual(self.spans("ключи --dry-run и -v"), ["--dry-run", "-v"])
        self.assertEqual(self.spans("лежит в src/utils/time.ts. Дальше"), ["src/utils/time.ts"])
        self.assertEqual(self.spans("см. https://example.com/a, потом"), ["https://example.com/a"])

    def test_cyrillic_words_are_not_protected(self):
        self.assertEqual(self.spans("и/или так-то, т.е. тоже"), [])
        self.assertEqual(self.spans("Сделай, пожалуйста, аккуратно. Это важно!"), [])
        self.assertEqual(self.spans("например e.g. и i.e. не идентификаторы"), [])

    def test_apostrophes_do_not_pair_across_words(self):
        self.assertEqual(self.spans("don't treat this isn't as a quote"), [])

    def test_code_fence_takes_precedence(self):
        text = "```ts\nconst a = get_x(); // path src/a.ts\n```"
        self.assertEqual(self.names(text), ["fence"])

    def test_placeholder_count_matches(self):
        text = "a_b c_d e_f"
        protected, table = diet.protect(text)
        self.assertEqual(len(table), 3)
        self.assertEqual(protected.count(diet.OPEN), 3)


class TestRestore(unittest.TestCase):
    def setUp(self):
        self.table = [("snake", "a_b"), ("snake", "c_d")]

    def test_missing_placeholder_fails(self):
        with self.assertRaises(ValueError):
            diet.restore("only " + diet.OPEN + "0" + diet.CLOSE, self.table)

    def test_duplicated_placeholder_fails(self):
        p = diet.OPEN + "0" + diet.CLOSE
        with self.assertRaises(ValueError):
            diet.restore(p + " " + p + " " + diet.OPEN + "1" + diet.CLOSE, self.table)

    def test_unknown_placeholder_fails(self):
        with self.assertRaises(ValueError):
            diet.restore(diet.OPEN + "0" + diet.CLOSE + diet.OPEN + "1" + diet.CLOSE + diet.OPEN + "9" + diet.CLOSE, self.table)

    def test_spaces_inside_brackets_are_tolerated(self):
        out = diet.restore(diet.OPEN + " 0 " + diet.CLOSE + " and " + diet.OPEN + "1" + diet.CLOSE, self.table)
        self.assertEqual(out, "a_b and c_d")


class TestLanguage(unittest.TestCase):
    def test_detection(self):
        self.assertEqual(diet.detect_language("Привет, нужно поправить баг"), "ru")
        self.assertEqual(diet.detect_language("Привіт, потрібно виправити помилку, будь ласка і ще"), "uk")
        self.assertEqual(diet.detect_language("Necesito que arregles el error en la función para el cliente"), "es")
        self.assertEqual(diet.detect_language("Preciso que você corrija o erro para os clientes, não demora"), "pt")
        self.assertEqual(diet.detect_language("Bitte korrigiere den Fehler, der ist nicht schön und wir brauchen das"), "de")
        self.assertEqual(diet.detect_language("Please fix the bug in the login handler"), "en")
        self.assertEqual(diet.detect_language("```\n1 + 1\n```"), "en")

    def test_answer_line(self):
        self.assertEqual(diet.answer_line("ru"), "Answer in Russian.")
        self.assertIn("original request", diet.answer_line("xx"))


class TestRequests(unittest.TestCase):
    def test_every_provider_builds_without_a_key(self):
        for p in diet.PROVIDERS:
            url, headers, body = diet.build_request(p, diet.PROVIDERS[p]["model"], "text " + diet.OPEN + "0" + diet.CLOSE)
            self.assertTrue(url.startswith("https://"))
            env = "$" + diet.PROVIDERS[p]["env"]
            self.assertTrue(any(env in v for v in headers.values()), "header holds the env var name, not a value")
            self.assertIn(json.dumps(diet.SYSTEM_PROMPT, ensure_ascii=False), json.dumps(body, ensure_ascii=False))

    def test_extract_text(self):
        self.assertEqual(diet.extract_text("openai", {"choices": [{"message": {"content": "x"}}]}), "x")
        self.assertEqual(diet.extract_text("gemini", {"candidates": [{"content": {"parts": [{"text": "a"}, {"text": "b"}]}}]}), "ab")
        self.assertEqual(diet.extract_text("anthropic", {"content": [{"type": "text", "text": "ok"}]}), "ok")
        with self.assertRaises(RuntimeError):
            diet.extract_text("anthropic", {"stop_reason": "refusal", "content": []})


if __name__ == "__main__":
    unittest.main()
