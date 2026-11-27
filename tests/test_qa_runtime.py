import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tools.qa_runtime import (
    build_scoped_process_argv,
    assert_no_production_reference,
    nvidia_window_metrics,
    relocate_config,
    smoke_timing,
    verify_opt01_reference,
    verify_x11_window,
)
from tools.visual_fixture import apply_visual_fixture, graphic_dimensions


class QaRuntimeTests(unittest.TestCase):
    def test_relocates_literal_and_escaped_production_roots(self):
        source = Path("/tmp/opt 01/theme")
        temp = Path("/tmp/run 77/theme")
        escaped_source = str(source).replace(" ", chr(92) + " ")
        config = f"conky.config = {{ lua_load='{source}/lua/panel.lua' }}\n"
        config += f"conky.text = '${{execi 5 {escaped_source}/scripts/read.sh}}'\n"
        moved = relocate_config(config, source, temp)
        self.assertNotIn(str(source), moved)
        self.assertIn(str(temp), moved)
        self.assertIn("/tmp/run\\ 77/theme/scripts/read.sh", moved)

    def test_unrelated_production_path_is_rejected(self):
        config = "conky.text='${execi 5 /home/tester/.config/conky/bosh-to-the-basic/run.sh}'"
        with self.assertRaisesRegex(ValueError, "active production"):
            assert_no_production_reference(config, "/home/tester/.config/conky/bosh-to-the-basic")

    def test_reference_fingerprint_checks_all_audited_files(self):
        files = {
            "bosh-to-the-basic.conf": b"config @CONKY_DIR@/scripts/x\n",
            "lua/bosh-to-the-basic.lua": b"lua source\n",
            "scripts/network-info.sh": b"network source\n",
            "scripts/intel-reader.py": b"intel source\n",
            "scripts/temperature-panel.py": b"temperature source\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "OPT-01"
            for relative, data in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            expected = {relative: hashlib.sha256(data).hexdigest()
                        for relative, data in files.items()}
            verify_opt01_reference(root, expected)
            (root / "bosh-to-the-basic.conf").write_text("different config\n")
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                verify_opt01_reference(root, expected)

    def test_reference_accepts_documented_normalized_config_but_rejects_tampering(self):
        from tools.qa_runtime import OPT01_NORMALIZED_FINGERPRINTS
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "OPT-01"
            root.mkdir()
            original_config = f"conky.config={{lua_load='{root}/lua/panel.lua'}}\n".encode()
            normalized_config = original_config.replace(str(root).encode(), b"@CONKY_DIR@")
            expected_original = hashlib.sha256(original_config).hexdigest()
            expected_normalized = hashlib.sha256(normalized_config).hexdigest()
            expected = {"bosh-to-the-basic.conf": expected_original}
            normalized = {"bosh-to-the-basic.conf": expected_normalized}
            path = root / "bosh-to-the-basic.conf"
            path.write_bytes(original_config)
            self.assertEqual(verify_opt01_reference(root, expected, normalized)[path.name], expected_original)
            path.write_bytes(normalized_config)
            self.assertEqual(
                verify_opt01_reference(root, expected, normalized),
                {"bosh-to-the-basic.conf": expected_normalized},
            )
            path.write_bytes(normalized_config + b"-- altered\n")
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                verify_opt01_reference(root, expected, normalized)

    def test_reference_rejects_altered_non_config_audited_file(self):
        files = {
            "bosh-to-the-basic.conf": b"config @CONKY_DIR@/scripts/x\n",
            "lua/bosh-to-the-basic.lua": b"lua original\n",
            "scripts/network-info.sh": b"network original\n",
            "scripts/intel-reader.py": b"intel original\n",
            "scripts/temperature-panel.py": b"temperature original\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "OPT-01"
            expected = {}
            for relative, data in files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                expected[relative] = hashlib.sha256(data).hexdigest()
            (root / "lua/bosh-to-the-basic.lua").write_text("altered Lua\n")
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch: lua/"):
                verify_opt01_reference(root, expected, {})

    def test_reference_fingerprint_rejects_symlinked_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "theme"
            root.mkdir()
            target = Path(directory) / "outside"
            target.write_text("x")
            (root / "bosh-to-the-basic.conf").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "regular"):
                verify_opt01_reference(root, {"bosh-to-the-basic.conf": "x"})

    def test_smoke_profile_is_short_and_full_profile_keeps_three_samples(self):
        self.assertEqual(smoke_timing(True), (3, 5, 1))
        self.assertEqual(smoke_timing(False), (30, 60, 3))

    def test_scoped_command_sets_private_gui_env_after_systemd_client(self):
        test_env = {
            "HOME": "/tmp/home test", "XDG_CONFIG_HOME": "/tmp/home test/cfg",
            "XDG_DATA_HOME": "/tmp/home test/data", "XDG_CACHE_HOME": "/tmp/home test/cache",
            "XDG_STATE_HOME": "/tmp/home test/state", "XDG_RUNTIME_DIR": "/tmp/runtime test",
            "DISPLAY": ":117", "XAUTHORITY": "/tmp/runtime test/Xauthority",
            "PATH": "/tmp/bin:/usr/bin",
        }
        argv = build_scoped_process_argv("bosh-qa.scope", test_env, ["/usr/bin/python3", "worker.py"])
        systemd_pos = argv.index("--scope")
        env_pos = argv.index("/usr/bin/env")
        self.assertLess(systemd_pos, env_pos)
        self.assertIn("XDG_RUNTIME_DIR=/tmp/runtime test", argv)
        self.assertIn("XAUTHORITY=/tmp/runtime test/Xauthority", argv)
        self.assertIn("-u", argv)
        self.assertNotIn("WAYLAND_DISPLAY=:0", argv)
        self.assertEqual(os.environ.get("XDG_RUNTIME_DIR"), os.environ.get("XDG_RUNTIME_DIR"))

    def test_nvidia_events_count_only_measurement_and_report_failures(self):
        events = [
            {"event": "start", "id": "warm", "monotonic_ns": 10},
            {"event": "end", "id": "warm", "monotonic_ns": 20,
             "wrapper_cpu_seconds": .1, "return_code": 0},
            {"event": "start", "id": "ok", "monotonic_ns": 110},
            {"event": "end", "id": "ok", "monotonic_ns": 130,
             "wrapper_cpu_seconds": .02, "return_code": 0},
            {"event": "start", "id": "fail", "monotonic_ns": 150},
            {"event": "end", "id": "fail", "monotonic_ns": 170,
             "wrapper_cpu_seconds": .03, "return_code": 9},
            {"event": "start", "id": "final", "monotonic_ns": 210},
            {"event": "end", "id": "final", "monotonic_ns": 220,
             "wrapper_cpu_seconds": .4, "return_code": 0},
        ]
        got = nvidia_window_metrics(events, 100, 200)
        self.assertEqual((got.queries, got.failed, got.wrapper_cpu_seconds), (2, 1, .05))

    def test_nvidia_call_crossing_window_invalidates_measurement(self):
        events = [
            {"event": "start", "id": "cross", "monotonic_ns": 90},
            {"event": "end", "id": "cross", "monotonic_ns": 110,
             "wrapper_cpu_seconds": .1, "return_code": 0},
        ]
        with self.assertRaisesRegex(ValueError, "crosses measurement boundary"):
            nvidia_window_metrics(events, 100, 200)

    def test_x11_window_probe_rejects_missing_or_invalid_window(self):
        with patch("tools.qa_runtime.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")):
            with self.assertRaisesRegex(RuntimeError, "positive window evidence"):
                verify_x11_window("x11_window.py", 123, {})
        with patch("tools.qa_runtime.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "0x23 273 720\n", "")):
            self.assertEqual(verify_x11_window("x11_window.py", 123, {"DISPLAY": ":117"}),
                             ("0x23", 273, 720))

    def test_x11_window_probe_passes_conky_log_as_window_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "conky.log"
            log.write_text("drawing to created window 0x200001\n")
            with patch("tools.qa_runtime.subprocess.run", return_value=subprocess.CompletedProcess(
                    [], 0, "0x200001 273 720\n", "")) as run:
                verify_x11_window("x11_window.py", 123, {"DISPLAY": ":117"}, log)
            self.assertIn("--log", run.call_args.args[0])
            self.assertIn(str(log), run.call_args.args[0])

    def test_conky_window_log_parser_requires_one_unambiguous_xid(self):
        from tools.x11_window import conky_window_xid
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "conky.log"
            log.write_text("starting\ndrawing to created window 0x200001\n")
            self.assertEqual(conky_window_xid(log), 0x200001)
            log.write_text("drawing to created window 0x200001\ndrawing to created window 0x200002\n")
            with self.assertRaisesRegex(RuntimeError, "ambiguous"):
                conky_window_xid(log)
            log.write_text("starting but no window\n")
            with self.assertRaisesRegex(RuntimeError, "not reported"):
                conky_window_xid(log)

    def test_window_id_probe_waits_for_conky_startup_log(self):
        from tools.x11_window import wait_for_conky_window_xid
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "conky.log"
            log.write_text("starting\n")
            with patch("tools.x11_window.time.sleep", side_effect=lambda _delay:
                    log.write_text("drawing to created window 0x200001\n")):
                self.assertEqual(wait_for_conky_window_xid(log, os.getpid(), timeout=.2), 0x200001)

    def test_logged_xid_identifies_viewable_window_when_pid_property_is_absent(self):
        from tools.x11_window import resolve_window

        class FakeX11:
            def root_window(self): return 1
            def children(self, window): return {1: [2], 2: [3], 3: []}.get(window, [])
            def pid(self, window): return None
            def visible(self, window): return None
            def geometry(self, window): return (273, 720)

        self.assertEqual(resolve_window(FakeX11(), 123, 3), (3, 273, 720))

    def test_logged_xid_must_be_in_window_tree_and_match_pid_when_available(self):
        from tools.x11_window import resolve_window

        class FakeX11:
            def root_window(self): return 1
            def children(self, window): return {1: [2], 2: [], 3: []}.get(window, [])
            def pid(self, window): return {2: 124}.get(window)
            def visible(self, window): return None
            def geometry(self, window): return (273, 720)

        with self.assertRaisesRegex(RuntimeError, "not in the isolated X11 window tree"):
            resolve_window(FakeX11(), 123, 3)
        with self.assertRaisesRegex(RuntimeError, "belongs to PID 124"):
            resolve_window(FakeX11(), 123, 2)

        class MatchingPid(FakeX11):
            def children(self, window): return {1: [2], 2: []}.get(window, [])
            def pid(self, window): return 123 if window == 2 else None

        self.assertEqual(resolve_window(MatchingPid(), 123, 2), (2, 273, 720))

    def test_logged_xid_rejects_unmapped_and_empty_windows(self):
        from tools.x11_window import resolve_window

        class FakeX11:
            state = "mapped"
            size = (273, 720)
            def root_window(self): return 1
            def children(self, window): return {1: [2], 2: []}.get(window, [])
            def pid(self, window): return None
            def visible(self, window):
                if self.state != "mapped": raise RuntimeError("matched Conky window is not mapped and viewable")
            def geometry(self, window): return self.size

        fake = FakeX11()
        fake.state = "unmapped"
        with self.assertRaisesRegex(RuntimeError, "not mapped"):
            resolve_window(fake, 123, 2)
        fake.state = "mapped"
        fake.size = (0, 720)
        with self.assertRaisesRegex(RuntimeError, "empty"):
            resolve_window(fake, 123, 2)

    def test_pid_fallback_rejects_ambiguous_windows(self):
        from tools.x11_window import resolve_window

        class FakeX11:
            def root_window(self): return 1
            def children(self, window): return {1: [2, 3], 2: [], 3: []}.get(window, [])
            def pid(self, window): return 123 if window in (2, 3) else None

        with self.assertRaisesRegex(RuntimeError, "found 2"):
            resolve_window(FakeX11(), 123)

    def test_window_tree_query_preserves_xlib_errors(self):
        from tools.x11_window import resolve_window

        class FailedX11:
            def root_window(self): return 1
            def children(self, window): raise RuntimeError("Xlib error 3 on resource 0x1")

        with self.assertRaisesRegex(RuntimeError, "Xlib error 3"):
            resolve_window(FailedX11(), 123, 2)

    def test_window_probe_waits_until_initial_geometry_resize_is_stable(self):
        from tools.x11_window import wait_for_stable_window

        class ResizingX11:
            sizes = iter(((5, 5), (283, 765), (283, 765), (283, 765)))
            def root_window(self): return 1
            def children(self, window): return {1: [2], 2: []}.get(window, [])
            def pid(self, window): return None
            def visible(self, window): return None
            def geometry(self, window): return next(self.sizes)

        self.assertEqual(wait_for_stable_window(ResizingX11(), 123, 2, timeout=1),
                         (2, 283, 765))

    def test_x11_probe_requires_mapped_viewable_window(self):
        from tools.x11_window import X11
        class FakeXlib:
            state = 2
            def XGetWindowAttributes(self, display, window, pointer):
                pointer._obj.map_state = self.state
                return 1
            def XSync(self, display, discard): return 0
        checker = object.__new__(X11)
        checker.lib = FakeXlib()
        checker.display = None
        checker._errors = []
        checker.visible(23)
        checker.lib.state = 0
        with self.assertRaisesRegex(RuntimeError, "not mapped and viewable"):
            checker.visible(23)

    def test_visual_fixture_keeps_presentation_and_graph_dimensions(self):
        repo = Path(__file__).resolve().parents[1]
        source = repo / "bosh-to-the-basic"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "theme copy"
            subprocess.run(["cp", "-R", str(source), str(target)], check=True)
            config = target / "bosh-to-the-basic.conf"
            config.write_text(config.read_text().replace("@CONKY_DIR@", str(source)))
            original = config.read_text()
            dimensions = apply_visual_fixture(source, target)
            transformed = config.read_text()
            self.assertEqual(sorted(dimensions), sorted(graphic_dimensions(transformed)))
            for section in ("SISTEMA", "GPU", "ALMACENAMIENTO", "PROCESOS", "temperature-panel.py", "network-info.sh"):
                self.assertIn(section, transformed)
            self.assertIn("${execbar 4,259 echo 35}", transformed)
            self.assertIn("xinerama_head = 0", transformed)
            self.assertIn("22,125", transformed)
            self.assertIn(":format(palette.yellow, palette.yellow, palette.blue, palette.blue)", transformed)
            self.assertNotIn(str(source), transformed)
            self.assertIn("2b96c0", original)
            self.assertIn("2b96c0", transformed)
            self.assertIn("2048, 4096", (target / "scripts/hardware_metrics.py").read_text())
            self.assertIn("return 42.0", (target / "scripts/hardware_metrics.py").read_text())
            self.assertIn("swap_present = 1", (target / "lua/bosh-to-the-basic.lua").read_text())

    def test_visual_fixture_injects_fixed_metrics_into_legacy_opt01_theme(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "legacy-opt01"
            target = root / "legacy-copy"
            (source / "scripts").mkdir(parents=True)
            (source / "lua").mkdir()
            (source / "bosh-to-the-basic.conf").write_text("""conky.config = {
    xinerama_head = 1,
    minimum_width=273,
}
conky.text = [[
${if_match ${execi 10 /usr/bin/wc -l /proc/swaps} > 0}SWAP ${swap}${swapbar 4,259}
GPU ${execi 5 @CONKY_DIR@/scripts/gpu-metric.sh memory}
${execibar 5 4,259 @CONKY_DIR@/scripts/gpu-metric.sh memory_percent}
${execpi 5 /usr/bin/python3 @CONKY_DIR@/scripts/intel-reader.py}
${execi 5 @CONKY_DIR@/scripts/gpu-metric.sh util}
${execibar 5 4,259 @CONKY_DIR@/scripts/gpu-metric.sh util}
${execpi 5 /usr/bin/python3 @CONKY_DIR@/scripts/temperature-panel.py}
${cpugraph cpu0 22,259 2b96c0 2b96c0}
${execpi 10 /usr/bin/bash "@CONKY_DIR@/scripts/network-info.sh"}
]]
""")
            (source / "lua/bosh-to-the-basic.lua").write_text(
                'value = conky_parse("${cpu cpu" .. n .. "}")\n'
                'down = conky_parse("${downspeed " .. iface .. "}")\n')
            for name in ("intel-reader.py", "temperature-panel.py", "network-info.sh"):
                (source / "scripts" / name).write_text("# source reader\n")
            shutil.copytree(source, target)
            apply_visual_fixture(source, target)
            config = (target / "bosh-to-the-basic.conf").read_text()
            self.assertNotIn("/proc/swaps", config)
            self.assertNotIn("gpu-metric.sh", config)
            self.assertIn("echo 2048 / 4096 MiB", config)
            self.assertIn("echo 25", config)
            self.assertIn("xinerama_head = 0", config)
            self.assertIn("visual-temperature-fixture.sh", config)
            self.assertIn("visual-intel-fixture.py", config)
            self.assertIn('execgraph "echo 35" 22,125', (target / "scripts/network-info.sh").read_text())
            intel_path = target / "scripts/visual-intel-fixture.py"
            intel = intel_path.read_text()
            self.assertNotIn("/run/bosh-conky", intel)
            self.assertIn("42.00%", intel)
            self.assertIn("${execbar 4,259 echo 42}", intel)

    def test_worker_rejects_early_simulated_process_and_requires_cgroup_membership(self):
        from tools.benchmark_worker import wait_alive
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            class FakeProcess:
                pid = os.getpid()
                returncode = 17
                def poll(self): return self.returncode
            with (root / "log").open("w+") as log:
                with self.assertRaisesRegex(RuntimeError, "exited early"):
                    wait_alive(FakeProcess(), .01, root, os.getpid(), log)

    def test_worker_measures_live_simulated_process_inside_cgroup(self):
        from tools.benchmark_worker import wait_alive
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "cgroup.procs").write_text(f"{os.getpid()}\n")
            process = subprocess.Popen(["/usr/bin/sleep", "1"])
            (root / "cgroup.procs").write_text(f"{os.getpid()}\n{process.pid}\n")
            try:
                with (root / "log").open("w+") as log:
                    panel_peak, worker_peak = wait_alive(process, .03, root, os.getpid(), log)
                self.assertGreaterEqual(panel_peak, 0)
                self.assertGreater(worker_peak, 0)
            finally:
                process.terminate()
                process.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
