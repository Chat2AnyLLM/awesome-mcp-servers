import importlib.util
import os
import pathlib
import unittest
from unittest import mock

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "build.py"
SPEC = importlib.util.spec_from_file_location("build", SCRIPT)
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class GeneratedAtTests(unittest.TestCase):
    def test_uses_valid_override(self):
        with mock.patch.dict(os.environ, {"GENERATED_AT": "2026-09-03T08:00:00Z"}):
            self.assertEqual("2026-09-03T08:00:00Z", BUILD.generated_at())

    def test_default_is_stable_within_build(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(BUILD.generated_at(), BUILD.generated_at())

    def test_rejects_invalid_override(self):
        with mock.patch.dict(os.environ, {"GENERATED_AT": "invalid"}):
            with self.assertRaises(ValueError):
                BUILD.generated_at()


if __name__ == "__main__":
    unittest.main()
