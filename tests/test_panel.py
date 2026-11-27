"""Behavioral tests for the OPT-01 presentation, using synthetic inputs."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


THEME = Path(__file__).resolve().parents[1] / "bosh-to-the-basic"
CONFIG = THEME / "bosh-to-the-basic.conf"
HOOKS = THEME / "lua/bosh-to-the-basic.lua"


def run_lua(program, *args):
    # First argument after "-" is arg[1] inside the stdin chunk.
    return subprocess.run(
        ["lua", "-", *map(str, args)], input=program, text=True,
        capture_output=True, check=True, timeout=5,
    ).stdout


class NetworkTests(unittest.TestCase):
    def network(self, route, ip_body='printf "%s\\n" "$ROUTE"'):
        with tempfile.TemporaryDirectory() as directory:
            ip = Path(directory) / "ip"
            ip.write_text("#!/bin/sh\n" + ip_body + "\n")
            ip.chmod(0o755)
            return subprocess.check_output(
                [THEME / "scripts/network-info.sh"], text=True, timeout=4,
                env={**os.environ, "LC_ALL": "C", "PATH": f"{directory}:/usr/bin", "ROUTE": route},
            )

    def test_stalled_route_query_becomes_disconnected(self):
        self.assertIn("Red desconectada", self.network("", "exec sleep 6"))

    def test_disconnected(self):
        self.assertIn("Red desconectada", self.network(""))

    def test_valid_vlan(self):
        row = self.network("default via 192.0.2.1 dev eth0.2 proto static")
        self.assertIn("${addr eth0.2}", row)
        self.assertIn("${lua_parse bosh_center_row total eth0.2}", row)

    def test_unusable_interface_is_disconnected(self):
        self.assertIn("Red desconectada", self.network("default dev bad{name}"))


@unittest.skipUnless(shutil.which("lua"), "Lua interpreter unavailable")
class LayoutTests(unittest.TestCase):
    def config(self, cpus):
        return run_lua("""
local cpus = tonumber(arg[2])
local open = io.open
io.open = function(path, ...)
    if path ~= '/proc/stat' then return open(path, ...) end
    local f = io.tmpfile()
    for i=0,cpus-1 do f:write('cpu'..i..' 0 0 0 0\\n') end
    f:seek('set'); return f
end
conky = {}
dofile(arg[1])
        print(conky.config.minimum_width, conky.config.maximum_width,
      conky.config.update_interval, tostring(conky.config.output_backend))
print(conky.text)
""", CONFIG, cpus)

    def test_four_slots_remain_on_large_cpu(self):
        panel = self.config(12)
        self.assertIn("273\t273\t1.0\tx11", panel)
        self.assertIn("${goto 206}${cpubar cpu4 4,58}", panel)
        self.assertNotIn("cpu5", panel)
        self.assertIn("${cpugraph cpu0 22,259 2b96c0 2b96c0}", panel)

    def test_two_cpu_machine_only_reads_two_individual_counters(self):
        panel = self.config(2)
        self.assertIn("${goto 72}${cpubar cpu2 4,58}", panel)
        self.assertNotIn("cpu3", panel)
        self.assertNotIn("cpu4", panel)
        self.assertIn("bosh_center_row cpu 2", panel)

    def test_swap_has_no_shell_pipeline(self):
        self.assertNotIn("/usr/bin/tail", self.config(4))

    def test_percent_bar_requires_no_external_command(self):
        output = run_lua("""
package.preload.cairo = function() return {} end
dofile(arg[1])
if not conky_bosh_percent then print('missing'); return end
print(conky_bosh_percent('20.60'), conky_bosh_percent('101'),
    conky_bosh_percent('nan'), conky_bosh_percent('0'))
""", HOOKS)
        self.assertEqual(output.strip(), "21\t0\t0\t0")

    def test_swap_presence_refreshes_after_ten_seconds(self):
        output = run_lua("""
package.preload.cairo = function() return {} end
local now = 100
os.time = function() return now end
local sample = ''
io.open = function(path)
    assert(path == '/proc/swaps')
    local f = io.tmpfile()
    f:write('Filename Type Size Used Priority\\n'..sample)
    f:seek('set'); return f
end
dofile(arg[1])
if not conky_bosh_swap_present then print('missing'); return end
print(conky_bosh_swap_present())
sample = '/dev/zram0 partition 512 0 1\\n'
now = 109; print(conky_bosh_swap_present())
now = 110; print(conky_bosh_swap_present())
""", HOOKS)
        self.assertEqual(output.splitlines(), ["0", "0", "1"])


@unittest.skipUnless(shutil.which("conky"), "Conky unavailable")
class ConsoleIntegrationTests(unittest.TestCase):
    def test_conky_loads_spaced_path_cairo_and_parses_last_gpu_row(self):
        """Exercise the real renderer and Lua ABI without a display or live collectors."""
        with tempfile.TemporaryDirectory(prefix="bosh panel ") as directory:
            root = Path(directory)
            (root / "lua").mkdir()
            (root / "scripts").mkdir()
            shutil.copy(HOOKS, root / "lua" / HOOKS.name)
            scripts = root / "scripts"
            shutil.copy(THEME / "scripts/temperature-panel.py", scripts)
            shutil.copy(THEME / "scripts/hardware_metrics.py", scripts / "fixture_backend.py")
            (scripts / "hardware_metrics.py").write_text(
                "from pathlib import Path\nfrom fixture_backend import *\n"
                "HWMON = Path(__file__).parent / 'hwmon'\n"
                "INTEL_FILE = Path(__file__).parent / 'intel'\n"
            )
            fake_gpu = scripts / "nvidia-smi"
            fake_gpu.write_text('#!/bin/sh\nprintf "%s\\n" "512, 2048, 26, 77"\n')
            fake_gpu.chmod(0o755)
            shutil.copy(THEME / "scripts/network-info.sh", scripts)
            fake_ip = scripts / "ip"
            fake_ip.write_text('#!/bin/sh\nprintf "%s\\n" "default dev lo"\n')
            fake_ip.chmod(0o755)
            # Exercise console rendering on both modern output_backend builds and
            # older Conky releases that only understand out_to_console.
            from installer.conky_backend import detect_output_backend
            modern_backend = detect_output_backend(shutil.which("conky") or "conky")
            conf = CONFIG.read_text().replace("@CONKY_DIR@", str(root))
            if not modern_backend:
                conf = conf.replace("output_backend = 'x11',", "")
            # Limit output to a synthetic GPU block, template expansion and Lua text
            # measurement. Never emit the workstation's processes or network addresses.
            conf += """
__CONSOLE_BACKEND__
conky.config.total_run_times = 2
conky.config.update_interval = 0.1
local gpu = assert(conky.text:match('(%${execpi 5 [^}]+})'))
local network = assert(conky.text:match('(%${execpi 10 [^}]+})'))
-- In console mode graph pixels cannot be inspected. A visible template
-- marker verifies that the emitted interface reaches the graph template.
conky.config.template0 = [[GRAPH \\1]]
conky.text = gpu .. '\\n' .. network .. '\\n${lua bosh_percent 20.60}'
"""
            conf = conf.replace(
                "__CONSOLE_BACKEND__",
                "conky.config.output_backend = 'console'" if modern_backend
                else "conky.config.out_to_console = true\nconky.config.out_to_x = false",
            )
            cfg = root / "test.conf"
            cfg.write_text(conf)
            result = subprocess.run(
                ["conky", "-c", str(cfg)], capture_output=True, text=True, timeout=8,
                env={"PATH": f"{scripts}:/usr/bin:/bin", "HOME": str(root), "LC_ALL": "C.UTF-8",
                     **({"DISPLAY": os.environ["DISPLAY"]} if os.environ.get("DISPLAY") else {})},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = result.stdout.replace("\x01", "")  # Console alignment control byte
            self.assertIn("GPU MEMORY", output, result.stderr)
            self.assertRegex(output, r"NVIDIA\s*77°C")
            self.assertRegex(output, r"BAJADA\s*SUBIDA", result.stderr)
            self.assertIn("GRAPH lo", output)
            self.assertIn("21", result.stdout)
            self.assertNotIn("[error]", result.stderr)
