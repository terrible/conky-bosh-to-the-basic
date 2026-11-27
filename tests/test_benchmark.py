import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("bench", Path(__file__).resolve().parents[1] / "tools/benchmark.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class BenchmarkTests(unittest.TestCase):
    def test_counter_includes_children_and_uses_microseconds(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cpu.stat"
            path.write_text("usage_usec 1234567\nuser_usec 1000000\n")
            self.assertEqual(bench.usage(path), 1234567)
            self.assertAlmostEqual(bench.cpu_percent(1234567, 1434567, 2), 10)

    def test_invalid_or_reset_counter_is_rejected(self):
        for end, seconds in [(50, 1), (100, 0)]:
            with self.subTest(end=end), self.assertRaises(ValueError):
                bench.cpu_percent(100, end, seconds)

    def test_pairs_alternate_order(self):
        self.assertEqual(list(bench.order(3)), [("OPT-01", "candidate"), ("candidate", "OPT-01"), ("OPT-01", "candidate")])

    def test_lab_rejects_real_home_and_production_config(self):
        with tempfile.TemporaryDirectory() as directory:
            lab = Path(directory)
            home = lab / "test-home"
            home.mkdir()
            with self.assertRaises(ValueError):
                bench.check_lab(lab, Path.home(), [lab / "config"])
            with self.assertRaises(ValueError):
                bench.check_lab(lab, home, [Path.home() / ".config/conky/panel.conf"])
            bench.check_lab(lab, home, [home / "panel.conf"])
