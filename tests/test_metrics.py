"""Hardware fixtures for the GPU and temperature panel. Never read host sensors."""
import importlib.util
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "bosh-to-the-basic" / "scripts"


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


class MetricsTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.root = Path(self.work.name)
        self.hwmon = self.root / "hwmon"
        self.intel = self.root / "intel-load"
        self.nvidia = self.root / "nvidia-smi"

    def sensor(self, name, samples):
        device = self.hwmon / "hwmon3"
        device.mkdir(parents=True)
        (device / "name").write_text(name)
        for index, (label, value) in enumerate(samples, 1):
            (device / f"temp{index}_label").write_text(label)
            (device / f"temp{index}_input").write_text(value)

    def panel(self):
        panel = load_script("temperature-panel")
        self.assertTrue(hasattr(panel, "full_panel"), "missing fused OPT-01 panel")
        return panel.full_panel(self.hwmon, self.intel, str(self.nvidia))

    def backend(self):
        self.assertTrue((SCRIPTS / "hardware_metrics.py").is_file(), "missing hardware reader")
        return load_script("hardware_metrics")

    def fake_nvidia(self, command):
        self.nvidia.write_text("#!/bin/sh\n" + command + "\n")
        self.nvidia.chmod(0o700)

    def test_fused_snapshot_uses_one_query_and_preserves_rows(self):
        self.sensor("coretemp", [("Package id 0", "70000"), ("Core 0", "80000"), ("Core 9", "90000")])
        self.intel.write_text("37.25")
        self.fake_nvidia(
            'printf "%s\\n" "$*" >> "$0.calls"\n'
            'printf "%s\\n" "300, 1200, 74, 75"'
        )
        text = self.panel()
        self.assertEqual((self.root / "nvidia-smi.calls").read_text().splitlines(), [
            "-i 0 --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits",
        ])
        self.assertEqual(text.splitlines(), [
            "${font NotoSans:size=9}GPU MEMORY ${alignr}300 / 1200 MiB",
            "${lua_bar 4,259 bosh_percent 25}",
            "${font NotoSans:size=9}GPU INTEL LOAD ${alignr}37.25%",
            "${lua_bar 4,259 bosh_percent 37.25}",
            "${font NotoSans:size=9}GPU NVIDIA LOAD ${alignr}74%",
            "${lua_bar 4,259 bosh_percent 74}",
            "",
            "${color2}${font NotoSans:bold:size=10}TEMPERATURA${color}",
            "${font NotoSans:size=9}CPU PACKAGE${alignr}${color3}70°C${color}",
            "${font NotoSans:size=9}CPU PROMEDIO${alignr}${color4}85°C${color}",
            "${font NotoSans:size=9}NVIDIA${alignr}${color3}75°C${color}",
        ])

    def test_missing_hardware_keeps_all_rows(self):
        text = self.panel()
        self.assertEqual(text.count("N/D"), 6)  # memory, two loads, three temperatures
        self.assertIn("GPU INTEL LOAD ${alignr}N/D\n \n", text)
        self.assertLess(len(text.encode()), 1024)

    def test_intel_zero_and_full_scale_keep_the_value_and_bar_rows(self):
        panel = load_script("temperature-panel")
        for value in (0, 100):
            with self.subTest(value=value):
                self.intel.write_text(str(value))
                output = panel.full_panel(self.hwmon, self.intel, str(self.nvidia))
                self.assertIn(f"GPU INTEL LOAD ${{alignr}}{value:.2f}%", output)
                self.assertIn(f"${{lua_bar 4,259 bosh_percent {float(value)}}}", output)

    def test_nvidia_rejects_bad_field_independently(self):
        self.fake_nvidia("echo '600, 200, 1e99, 77'")
        data = self.backend().nvidia_snapshot(str(self.nvidia))
        self.assertIsNone(data.memory)
        self.assertIsNone(data.util)
        self.assertEqual(data.temp, 77)

    def test_nvidia_temperature_accepts_decimal_and_renderer_displays_celsius(self):
        self.fake_nvidia(
            'printf "%s\\n" "$*" >> "$0.calls"\n'
            'printf "%s\\n" "586, 4096, 16, 34.22"'
        )
        panel = load_script("temperature-panel")
        output = panel.full_panel(self.hwmon, self.intel, str(self.nvidia))
        self.assertIn("GPU MEMORY ${alignr}586 / 4096 MiB", output)
        self.assertIn("GPU NVIDIA LOAD ${alignr}16%", output)
        self.assertIn("${font NotoSans:size=9}NVIDIA${alignr}${color}34°C${color}", output)
        self.assertEqual((self.root / "nvidia-smi.calls").read_text().splitlines(), [
            "-i 0 --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader,nounits",
        ])

    def test_nvidia_temperature_parser_accepts_decimal_range_and_preserves_threshold_semantics(self):
        backend = self.backend()
        panel = load_script("temperature-panel")
        valid = {"34": 34, "34.22": 34.22, "0": 0, "0.0": 0.0,
                 "74.9": 74.9, "75": 75, "85": 85, "150": 150}
        for raw, expected in valid.items():
            with self.subTest(raw=raw):
                self.fake_nvidia(
                    'printf "%s\\n" "$*" >> "$0.calls"\n'
                    f'printf "%s\\n" "586, 4096, 16, {raw}"'
                )
                (self.root / "nvidia-smi.calls").write_text("")
                snapshot = backend.nvidia_snapshot(str(self.nvidia))
                self.assertEqual(snapshot.memory, (586, 4096))
                self.assertEqual(snapshot.util, 16)
                self.assertEqual(snapshot.temp, expected)
                self.assertEqual(len((self.root / "nvidia-smi.calls").read_text().splitlines()), 1)
                rendered = panel.render("NVIDIA", snapshot.temp, 75, 85)
                if raw == "74.9":
                    self.assertIn("${color}75°C", rendered)  # compare raw value before display rounding
                if raw == "75":
                    self.assertIn("${color3}75°C", rendered)
                if raw == "85":
                    self.assertIn("${color4}85°C", rendered)

    def test_invalid_nvidia_temperature_does_not_discard_valid_gpu_metrics(self):
        backend = self.backend()
        invalid = ("150.01", "-1", "NaN", "Inf", "N/A", "[Not Supported]", "", "warm",
                   "3.422e1", "34C")
        for raw in invalid:
            with self.subTest(raw=raw):
                escaped = raw.replace("'", "'\\''")
                self.fake_nvidia(
                    'printf "%s\\n" "$*" >> "$0.calls"\n'
                    f"printf '%s\\n' '586, 4096, 16, {escaped}'"
                )
                (self.root / "nvidia-smi.calls").write_text("")
                snapshot = backend.nvidia_snapshot(str(self.nvidia))
                self.assertEqual(snapshot.memory, (586, 4096))
                self.assertEqual(snapshot.util, 16)
                self.assertIsNone(snapshot.temp)
                self.assertEqual(len((self.root / "nvidia-smi.calls").read_text().splitlines()), 1)

    def test_nvidia_timeout(self):
        self.fake_nvidia("exec /bin/sleep 10")
        start = time.monotonic()
        data = self.backend().nvidia_snapshot(str(self.nvidia), timeout=0.05)
        self.assertLess(time.monotonic() - start, 2)
        self.assertIsNone(data.util)

    def test_legacy_nvidia_script_uses_same_snapshot_format(self):
        self.fake_nvidia("echo '300, 1200, 74, 75'")
        for metric, expected in [("memory", "300 / 1200 MiB"), ("util", "74"),
                                 ("memory_percent", "25"), ("temp", "75")]:
            with self.subTest(metric=metric):
                result = subprocess.run([SCRIPTS / "gpu-metric.sh", metric],
                                        env={**os.environ, "PATH": str(self.root) + os.pathsep + os.defpath},
                                        capture_output=True, text=True, check=True, timeout=3)
                self.assertEqual(result.stdout.strip(), expected)

    def test_intel_rejects_writable_cache(self):
        self.intel.write_text("10")
        self.intel.chmod(0o666)
        self.assertIsNone(self.backend().intel_load(self.intel))

    def test_intel_range_and_age(self):
        reader = self.backend().intel_load
        for value, age, expected in [("0", 15, 0), ("100", 0, 100), ("44", 16, None),
                                     ("12", -1, None), ("nan", 4, None), ("101", 4, None),
                                     ("-1", 0, None), ("0" * 65, 0, None)]:
            with self.subTest(value=value, age=age):
                self.intel.write_text(value)
                os.utime(self.intel, (1000-age, 1000-age))
                self.assertEqual(reader(self.intel, now=1000), expected)

    def test_intel_rejects_non_regular_and_symlink(self):
        reader = self.backend().intel_load
        os.mkfifo(self.intel)
        self.assertIsNone(reader(self.intel))
        self.intel.unlink()
        sample = self.root / "sample"
        sample.write_text("43")
        self.intel.symlink_to(sample)
        self.assertIsNone(reader(self.intel))

    def test_amd_prefers_tdie_and_handles_missing_cores(self):
        self.sensor("k10temp", [("Tctl", "81000"), ("Tdie", "70000")])
        self.assertEqual(self.backend().cpu_temperatures(self.hwmon), (70, None))

    def test_rejects_malformed_or_out_of_range_coretemp(self):
        self.sensor("coretemp", [("Package id 0", "151000"), ("Core 0", "xx"), ("Core 1", "-5")])
        self.assertEqual(self.backend().cpu_temperatures(self.hwmon), (None, None))

    def test_temperature_thresholds(self):
        panel = load_script("temperature-panel")
        for degrees, warm, color in [(69, 70, "color"), (70, 70, "color3"), (74, 75, "color"),
                                     (75, 75, "color3"), (85, 75, "color4"), (None, 70, "color")]:
            self.assertIn("${alignr}${" + color + "}", panel.render("sensor", degrees, warm, 85))
