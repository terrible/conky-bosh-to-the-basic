"""Apply the same deterministic metric sources to both isolated visual copies."""
from pathlib import Path
import argparse
import re

try:
    from qa_runtime import relocate_config
except ImportError:
    from tools.qa_runtime import relocate_config


FIXED = {
    "${time %H:%M:%S}": "12:34:56",
    "${time %A %d %b %Y}": "Thu 26 Nov 2026",
    "${uptime_short}": "1d 02h",
    "${cpu}": "35",
    "${mem}": "4.0 GiB",
    "${memmax}": "16.0 GiB",
    "${swap}": "0 B",
    "${swapmax}": "0 B",
    "${fs_used /}": "42 GiB",
    "${fs_size /}": "256 GiB",
}

SYNTHETIC_HARDWARE = '''"""Fixed visual-test metrics; no host sensors or GPU are read."""
from pathlib import Path
HWMON = Path("/nonexistent/bosh-visual-test")
INTEL_FILE = Path("/nonexistent/bosh-visual-test/intel")
class Nvidia(tuple):
    __slots__ = ()
    def __new__(cls, memory=None, util=None, temp=None):
        return tuple.__new__(cls, (memory, util, temp))
    memory = property(lambda self: self[0])
    util = property(lambda self: self[1])
    temp = property(lambda self: self[2])
def cpu_temperatures(root=HWMON): return 42, 40
def intel_load(path=INTEL_FILE, now=None): return 42.0
def nvidia_snapshot(binary="nvidia-smi", timeout=1.5): return Nvidia((2048, 4096), 25, 43)
def memory_display(snapshot): return "2048 / 4096 MiB"
def memory_percent(snapshot): return 50
'''


def graphic_dimensions(config_text):
    dimensions = []
    for match in re.finditer(r"\$\{(?:cpu|mem|swap)bar(?: cpu[^ ]+)? ([^}]+)\}", config_text):
        dimensions.append(("bar", match.group(1).split()[0]))
    for match in re.finditer(r"\$\{execbar ([^}]+)\}", config_text):
        dimensions.append(("bar", match.group(1).split()[0]))
    for match in re.finditer(r"\$\{(?:cpu|downspeed|upspeed)graph [^}]*?(\d+,\d+)", config_text):
        dimensions.append(("graph", match.group(1)))
    for match in re.finditer(r'\$\{execgraph (?:"echo \d+"|echo \d+) ([^}]+)', config_text):
        dimensions.append(("graph", match.group(1).split()[0]))
    for match in re.finditer(r"\$\{fs_bar ([^}]+)\}", config_text):
        dimensions.append(("bar", match.group(1).split()[0]))
    return dimensions


def apply_visual_fixture(source_theme, target_theme):
    source_theme, target_theme = Path(source_theme).resolve(), Path(target_theme).resolve()
    config_path = target_theme / "bosh-to-the-basic.conf"
    config = relocate_config(config_path.read_text(), source_theme, target_theme)
    hardware = target_theme / "scripts" / "hardware_metrics.py"
    legacy_opt01 = not hardware.exists()
    config, head_count = re.subn(r"(?m)^(\s*xinerama_head\s*=\s*)\d+", r"\g<1>0", config)
    if head_count != 1:
        raise ValueError("visual fixture expected exactly one xinerama_head setting")
    expected_dimensions = graphic_dimensions(config)
    for source, replacement in FIXED.items():
        config = config.replace(source, replacement)
    config = re.sub(r"\$\{top name (\d+)\}", lambda m: "test-process-" + m.group(1), config)
    config = re.sub(r"\$\{top (?:cpu|mem) (\d+)\}", "1.0", config)
    config = config.replace("${cpubar cpu%d 4,58}", "${execbar 4,58 echo 35}")
    config = re.sub(r"\$\{cpubar cpu(\d+) ([^}]+)\}", r"${execbar \2 echo 35}", config)
    config = re.sub(r"\$\{cpubar ([^}]+)\}", r"${execbar \1 echo 35}", config)
    config = re.sub(r"\$\{membar ([^}]+)\}", r"${execbar \1 echo 45}", config)
    config = re.sub(r"\$\{swapbar ([^}]+)\}", r"${execbar \1 echo 0}", config)
    config = re.sub(r"\$\{fs_bar ([0-9,]+) /\}", r"${execbar \1 echo 30}", config)
    config = re.sub(r"\$\{cpugraph cpu0 ([^}]+)\}", r'${execgraph "echo 35" \1}', config)
    config = config.replace("${downspeedgraph %s 22,125 %s %s}", '${execgraph "echo 35" 22,125 %s %s}')
    config = config.replace("${upspeedgraph %s 22,125 %s %s}", '${execgraph "echo 15" 22,125 %s %s}')
    config = config.replace(
        ":format([[\\1]], palette.yellow, palette.yellow, [[\\1]], palette.blue, palette.blue)",
        ":format(palette.yellow, palette.yellow, palette.blue, palette.blue)",
    )
    if legacy_opt01:
        config = re.sub(
            r"\$\{if_match \$\{execi\s+\d+\s+[^}]*?/proc/swaps[^}]*\} > 0\}",
            "${if_match 1 > 0}", config)
        config = re.sub(
            r"\$\{execi\s+\d+\s+[^}]*gpu-metric\.sh memory\}",
            "${execi 3600 echo 2048 / 4096 MiB}", config)
        config = re.sub(
            r"\$\{execibar\s+\d+\s+[0-9,]+\s+[^}]*gpu-metric\.sh memory_percent\}",
            "${execibar 3600 4,259 echo 50}", config)
        config = re.sub(
            r"\$\{execpi\s+\d+\s+/usr/bin/python3\s+[^}]*intel-reader\.py\}",
            '${execpi 3600 /usr/bin/python3 -B "' +
            str(target_theme / "scripts/visual-intel-fixture.py") + '"}', config)
        config = re.sub(
            r"\$\{execi\s+\d+\s+[^}]*gpu-metric\.sh util\}",
            "${execi 3600 echo 25}", config)
        config = re.sub(
            r"\$\{execibar\s+\d+\s+[0-9,]+\s+[^}]*gpu-metric\.sh util\}",
            "${execibar 3600 4,259 echo 25}", config)
        config = re.sub(
            r"\$\{execpi\s+\d+\s+/usr/bin/python3\s+[^}]*temperature-panel\.py\}",
            '${execpi 3600 /usr/bin/bash "' + str(target_theme / "scripts/visual-temperature-fixture.sh") + '"}', config)
    if sorted(graphic_dimensions(config)) != sorted(expected_dimensions):
        raise ValueError("visual fixture changed original bar or graph dimensions")
    if str(source_theme) in config:
        raise ValueError("visual config retains executable source-theme path")
    config_path.write_text(config)

    if legacy_opt01:
        intel_fixture = target_theme / "scripts" / "visual-intel-fixture.py"
        if intel_fixture.is_symlink() or intel_fixture.exists():
            raise ValueError("refusing to overwrite visual Intel fixture")
        intel_fixture.write_text('print("${alignr}42.00%")\nprint("${execbar 4,259 echo 42}")\n')
        temperature_fixture = target_theme / "scripts" / "visual-temperature-fixture.sh"
        temperature_fixture.write_text("""#!/usr/bin/env bash
printf '${font NotoSans:size=9}CPU PACKAGE${alignr}${color d6dde5}42°C${color}\\n'
printf '${font NotoSans:size=9}CPU PROMEDIO${alignr}${color d6dde5}40°C${color}\\n'
printf '${font NotoSans:size=9}NVIDIA${alignr}${color d6dde5}43°C${color}'
""")
        temperature_fixture.chmod(0o700)
    else:
        if not hardware.is_file() or hardware.is_symlink():
            raise ValueError("hardware metrics module missing or symlinked")
        hardware.write_text(SYNTHETIC_HARDWARE)

    lua = target_theme / "lua" / "bosh-to-the-basic.lua"
    if not lua.is_file() or lua.is_symlink():
        raise ValueError("Lua module missing or symlinked")
    lua_text = lua.read_text()
    lua_text = lua_text.replace('"${cpu cpu" .. n .. "}"', '"35"')
    lua_text = lua_text.replace('"${downspeed " .. iface .. "}"', '"1.0 MiB"')
    lua_text = lua_text.replace('"${upspeed " .. iface .. "}"', '"128 KiB"')
    lua_text = lua_text.replace('"${totaldown " .. iface .. "}"', '"1.0 GiB"')
    lua_text = lua_text.replace('"${totalup " .. iface .. "}"', '"128 MiB"')
    lua_text = lua_text.replace("swap_present = 0", "swap_present = 1")
    lua.write_text(lua_text)

    network = target_theme / "scripts" / "network-info.sh"
    if not network.is_file() or network.is_symlink():
        raise ValueError("network script missing or symlinked")
    if legacy_opt01:
        net_text = """#!/usr/bin/env bash
printf '${color2}${font NotoSans:bold:size=10}RED · enp0s3${color}\\n'
printf '${font NotoSans:size=9}IP ${alignr}192.0.2.10\\n'
printf '${font NotoSans:size=8}${lua_parse bosh_center_row title}\\n'
printf '${font NotoSans:size=9}${lua_parse bosh_center_row speed enp0s3}\\n'
printf '${goto 5}${execgraph "echo 35" 22,125 ffd54f ffd54f}${goto 139}${execgraph "echo 15" 22,125 2b96c0 2b96c0}\\n'
printf '${font NotoSans:size=8}${lua_parse bosh_center_row total enp0s3}\\n'
"""
    else:
        net_text = network.read_text().replace(
            "printf '${font NotoSans:size=9}IP ${alignr}${addr %s}\\n' \"$iface\"",
            "printf '${font NotoSans:size=9}IP ${alignr}192.0.2.10\\n'",
        )
    network.write_text(net_text)
    return expected_dimensions


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source_theme", type=Path)
    parser.add_argument("target_theme", type=Path)
    args = parser.parse_args()
    print(apply_visual_fixture(args.source_theme, args.target_theme))
