import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

RESOURCE = Path(__file__).resolve().parents[1] / "resources/intel"
spec = importlib.util.spec_from_file_location("collector", RESOURCE / "bosh-conky-intel.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class CollectorTests(unittest.TestCase):
    def test_sample_uses_generic_intel_filter_and_timeout(self):
        data = '[{}, {"engines":{"Render/3D":{"busy":12.345}}}]'
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess([], 0, data)) as run:
            self.assertEqual(collector.sample(), 12.345)
            args, kwargs = run.call_args
            self.assertIn("pci:vendor=8086", args[0])
            self.assertEqual(kwargs["timeout"], 8)
            self.assertTrue(kwargs["check"])

    def test_invalid_samples(self):
        for value in [True, "nan", -1, 101, None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                collector.busy_percent([{"engines": {"Render/3D": {"busy": value}}}])

    def test_publication_is_atomic_and_discloses_only_percentage(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            victim = path / "unrelated"
            victim.write_text("keep")
            (path / "intel-load").symlink_to(victim)
            collector.publish(path, 25.125)
            sample = path / "intel-load"
            self.assertEqual(victim.read_text(), "keep")
            self.assertFalse(sample.is_symlink())
            self.assertEqual(sample.read_text(), "25.12\n")
            self.assertEqual(sample.stat().st_mode & 0o777, 0o644)
            self.assertEqual(len(list(path.iterdir())), 2)

    def test_failed_measurement_invalidates_previous_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            collector.publish(path, 10)
            with patch.object(collector, "sample", side_effect=subprocess.TimeoutExpired("intel_gpu_top", 8)):
                self.assertFalse(collector.update(path))
            self.assertFalse((path / "intel-load").exists())
