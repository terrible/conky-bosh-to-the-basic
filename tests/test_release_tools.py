from pathlib import Path
import tempfile
import unittest
import importlib.util
import subprocess

ROOT = Path(__file__).resolve().parents[1]


class ReleaseToolRegressionTests(unittest.TestCase):
    def test_benchmark_does_not_combine_scope_with_wait_or_collect(self):
        text = (ROOT / "tools/benchmark-real.sh").read_text()
        self.assertNotIn("--scope --quiet --wait", text)
        self.assertNotIn("--scope --quiet --wait --collect", text)

    def test_visual_compare_keeps_existing_output_and_checks_capture(self):
        text = (ROOT / "tools/visual-compare.sh").read_text()
        self.assertIn("! -e", text)
        self.assertIn("identify", text)
        self.assertIn("compare -metric", text)
        self.assertNotIn("|| true", text)

    def test_benchmark_uses_real_foreground_process_and_monotonic_clock(self):
        text = (ROOT / "tools/benchmark_worker.py").read_text()
        self.assertIn("time.monotonic", text)
        self.assertIn("queries_per_minute", text)
        self.assertIn("process.poll()", text)
        self.assertIn("stderr=", text)
        self.assertIn("stdout=", text)
        self.assertIn("render", text.lower())
        self.assertIn("exclusive", text.lower())
        self.assertIn("unit_name + \".scope\"", text)

    def test_benchmark_sets_isolated_xdg_home_paths(self):
        text = (ROOT / "tools/benchmark-real.sh").read_text()
        self.assertIn('"HOME=$home"', text)
        self.assertIn('"XAUTHORITY=$authority"', text)
        self.assertIn('"XDG_RUNTIME_DIR=$work/runtime"', text)
        self.assertIn("-u DBUS_SESSION_BUS_ADDRESS", text)
        for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME"):
            self.assertIn(name, text)

    def test_benchmark_has_smoke_and_timestamped_nvidia_measurement(self):
        text = (ROOT / "tools/benchmark-real.sh").read_text()
        worker = (ROOT / "tools/benchmark_worker.py").read_text()
        self.assertIn("--smoke-test", text)
        self.assertIn("warm_seconds=3; measure_seconds=5; sample_count=1", text)
        self.assertIn("--x11-window-checker", text)
        self.assertIn("nvidia_failed_queries", text)
        self.assertIn("monotonic_ns", text)
        self.assertIn("nvidia_window_metrics", worker)
        self.assertIn("verify_x11_window", worker)

    def test_scope_is_synchronous_and_cleanup_is_registered(self):
        text = (ROOT / "tools/benchmark-real.sh").read_text()
        self.assertIn("systemd-run --user --scope", text)
        self.assertNotIn("--scope --wait", text)
        self.assertNotIn("--scope --collect", text)
        self.assertIn("trap cleanup EXIT", text)
        self.assertIn("trap 'exit 130' INT", text)
        self.assertIn("trap 'exit 143' TERM", text)
        self.assertIn("systemctl --user stop", text)
        self.assertIn("scan_status > 1", text)

    def test_physical_benchmark_serializes_same_checkout_runs(self):
        text = (ROOT / "tools/benchmark-real.sh").read_text()
        self.assertIn('exec {benchmark_lock}<"$repo/tools/benchmark-real.sh"', text)
        self.assertIn('flock -n "$benchmark_lock"', text)

    def test_make_benchmark_accepts_explicit_opt01_reference_and_has_no_temp_backup_default(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["make", "--no-print-directory", "-n", "benchmark", f"OPT01_REF={directory}"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
        self.assertIn(f'--reference "{directory}"', result.stdout)
        self.assertNotIn("/tmp/bosh-opt01-36yed2x2", result.stdout)

    def test_conky_backend_selection_is_capability_based(self):
        helper = ROOT / "installer/conky_backend.py"
        self.assertTrue(helper.is_file())
        text = helper.read_text()
        self.assertIn("supports_output_backend", text)
        self.assertIn("out_to_x", text)
        self.assertIn("output_backend", text)
        self.assertIn('env.pop("DISPLAY", None)', text)
        for script in ("tools/visual-compare.sh", "tools/benchmark-real.sh"):
            self.assertIn("conky_backend.py", (ROOT / script).read_text())
        distributed = (ROOT / "bosh-to-the-basic/bosh-to-the-basic.conf").read_text()
        self.assertIn("output_backend = 'x11'", distributed)

    def test_backend_probe_distinguishes_modern_and_legacy_conky(self):
        spec = importlib.util.spec_from_file_location("conky_backend", ROOT / "installer/conky_backend.py")
        backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend)
        self.assertTrue(backend.supports_output_backend("backend-probe"))
        self.assertFalse(backend.supports_output_backend("Unknown setting 'output_backend'"))
        self.assertFalse(backend.supports_output_backend("", returncode=0))
        self.assertFalse(backend.supports_output_backend("backend-probe", returncode=1))
        source = (ROOT / "bosh-to-the-basic/bosh-to-the-basic.conf").read_text()
        modern = backend.normalize_text(source, "/tmp/theme", True)
        legacy = backend.normalize_text(source, "/tmp/theme", False)
        self.assertIn("output_backend = 'x11'", modern)
        self.assertNotIn("out_to_x", modern)
        self.assertIn("out_to_x = true", legacy)
        self.assertNotIn("output_backend", legacy)

    def test_backend_normalization_uses_version_appropriate_setting_names(self):
        spec = importlib.util.spec_from_file_location("conky_backend", ROOT / "installer/conky_backend.py")
        backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend)
        source = "conky.config = {\n    xftalpha = 1.0,\n    own_window_colour = '000000',\n    xinerama_head = 1,\n}\n"
        modern = backend.normalize_text(source, "/tmp/theme", True, xinerama_head=0)
        legacy = backend.normalize_text(source, "/tmp/theme", False, xinerama_head=0)
        self.assertIn("text_alpha = 1.0", modern)
        self.assertIn("own_window_color = '000000'", modern)
        self.assertNotIn("xftalpha", modern)
        self.assertNotIn("own_window_colour", modern)
        self.assertIn("xftalpha = 1.0", legacy)
        self.assertIn("own_window_colour = '000000'", legacy)
        self.assertNotIn("text_alpha", legacy)
        self.assertNotIn("own_window_color", legacy)
        self.assertIn("xinerama_head = 0", modern)
        self.assertIn("xinerama_head = 0", legacy)

    def test_backend_probe_requires_positive_output_from_executable(self):
        spec = importlib.util.spec_from_file_location("conky_backend", ROOT / "installer/conky_backend.py")
        backend = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend)
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "conky"
            binary.write_text("#!/bin/sh\nprintf backend-probe\n")
            binary.chmod(0o700)
            self.assertTrue(backend.detect_output_backend(str(binary)))
            binary.write_text("#!/bin/sh\nexit 0\n")
            binary.chmod(0o700)
            with self.assertRaisesRegex(RuntimeError, "no positive marker"):
                backend.detect_output_backend(str(binary))
            binary.write_text("#!/bin/sh\nprintf 'backend-probe\\nUnknown setting output_backend\\n'\n")
            binary.chmod(0o700)
            self.assertFalse(backend.detect_output_backend(str(binary)))
            binary.write_text("#!/bin/sh\nprintf 'Unknown setting output_backend\\n'\n")
            binary.chmod(0o700)
            with self.assertRaisesRegex(RuntimeError, "no positive marker"):
                backend.detect_output_backend(str(binary))

    def test_visual_script_checks_window_capture_and_compare_status(self):
        text = (ROOT / "tools/visual-compare.sh").read_text()
        self.assertIn("x11_window.py", text)
        self.assertIn("window", text)
        self.assertIn("window-probe.log", text)
        self.assertIn("compare_status", text)
        self.assertNotIn("|| true", text)
        self.assertTrue((ROOT / "tools/x11_window.py").is_file())


if __name__ == "__main__":
    unittest.main()
