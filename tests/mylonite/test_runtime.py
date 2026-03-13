from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from mylonite.runtime import (
    ensure_runtime_env_file,
    load_simple_env,
    update_simple_env,
    write_simple_env,
)


class RuntimeEnvTests(SimpleTestCase):
    def test_write_and_load_simple_env(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            write_simple_env(path, {"DJANGO_DEBUG": "false", "A": "B"})

            loaded = load_simple_env(path)

            self.assertEqual(loaded["DJANGO_DEBUG"], "false")
            self.assertEqual(loaded["A"], "B")

    def test_update_simple_env_updates_and_appends_keys(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("A=1\n# comment\n", encoding="utf-8")

            update_simple_env(path, {"A": "2", "B": "3"})

            loaded = load_simple_env(path)
            self.assertEqual(loaded, {"A": "2", "B": "3"})

    def test_ensure_runtime_env_file_creates_secret_when_missing(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"

            created, updated = ensure_runtime_env_file(path)

            loaded = load_simple_env(path)
            self.assertTrue(created)
            self.assertFalse(updated)
            self.assertIn("DJANGO_SECRET_KEY", loaded)
            self.assertIn("DJANGO_DEBUG", loaded)

    def test_ensure_runtime_env_file_adds_secret_if_blank(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("DJANGO_SECRET_KEY=\nDJANGO_DEBUG=true\n", encoding="utf-8")

            created, updated = ensure_runtime_env_file(path)

            loaded = load_simple_env(path)
            self.assertFalse(created)
            self.assertTrue(updated)
            self.assertTrue(loaded["DJANGO_SECRET_KEY"])

    def test_load_simple_env_handles_quotes_and_ignores_invalid_lines(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text(
                "# comment\nA='quoted value'\nB=\"double\"\nINVALID_LINE\nC=plain\n",
                encoding="utf-8",
            )

            loaded = load_simple_env(path)

            self.assertEqual(loaded, {"A": "quoted value", "B": "double", "C": "plain"})

    def test_ensure_runtime_env_file_noop_when_secret_exists(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("DJANGO_SECRET_KEY=present\nDJANGO_DEBUG=false\n", encoding="utf-8")

            created, updated = ensure_runtime_env_file(path)

            self.assertFalse(created)
            self.assertFalse(updated)
