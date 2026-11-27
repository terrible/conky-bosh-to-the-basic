"""Shared safety checks for isolated QA runs."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys

# Provenance: original config SHA-256 was recorded during the OPT-01 audit before
# path normalization. The second digest was independently computed after replacing
# the audited absolute theme root with @CONKY_DIR@. All other hashes are raw file
# hashes from the same five-file audit record.
OPT01_FINGERPRINTS = {
    "bosh-to-the-basic.conf": "4545a1a845edaebc4dfab3063e79ccc164abc7ecad7de015ccc97a454c0d114f",
    "lua/bosh-to-the-basic.lua": "9bb633cbf17348954e22e6a7f43e13a8cf7e391563852e0aac5a810088e0746e",
    "scripts/network-info.sh": "1235c7561837b70bb6217c9ef98efb5469cd12e6c6ad75273f9296a41b93e080",
    "scripts/intel-reader.py": "1a12a0be649a505be7a2b13827d90a5feb119209c98a1514933a8bd6d88fadbb",
    "scripts/temperature-panel.py": "3f063b6749f6f4c87680638645a1a847df2a890c3c49a31d3785db93251aa3e6",
}
OPT01_NORMALIZED_FINGERPRINTS = {
    "bosh-to-the-basic.conf": "ddcffddeb58af8440de3ecf76848fe92e6b7f3b0972b129a3e1deb0a5035a7b8",
}


@dataclass(frozen=True)
class NvidiaWindowMetrics:
    queries: int
    failed: int
    wrapper_cpu_seconds: float


def _root_forms(root):
    value = str(Path(root).resolve(strict=False))
    return tuple(dict.fromkeys((value, value.replace(" ", r"\ "))))


def relocate_config(text, source_root, target_root):
    target = str(Path(target_root).resolve(strict=False))
    result = text
    sources = _root_forms(source_root)
    result = result.replace(sources[0], target)
    if len(sources) > 1:
        result = result.replace(sources[1], target.replace(" ", r"\ "))
    if any(source in result for source in _root_forms(source_root)):
        raise ValueError("executable config still references the source theme")
    assert_no_production_reference(result)
    return result


def production_theme_root(environ=None):
    env = os.environ if environ is None else environ
    config_home = Path(env.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "conky" / "bosh-to-the-basic"


def assert_no_production_reference(text, production_root=None):
    root = production_theme_root() if production_root is None else Path(production_root)
    if any(form in text for form in _root_forms(root)):
        raise ValueError("executable config still references the active production theme")


def verify_opt01_reference(root, expected=OPT01_FINGERPRINTS,
                           normalized_expected=OPT01_NORMALIZED_FINGERPRINTS):
    theme = Path(root)
    if theme.is_symlink() or not theme.is_dir():
        raise ValueError("OPT-01 reference must be a real theme directory")
    theme = theme.resolve(strict=True)
    actual = {}
    for relative, digest in expected.items():
        path = theme / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"OPT-01 reference file is not regular: {relative}")
        data = path.read_bytes()
        found = hashlib.sha256(data).hexdigest()
        if relative == "bosh-to-the-basic.conf":
            normalized_data = data
            for source in _root_forms(theme):
                normalized_data = normalized_data.replace(source.encode(), b"@CONKY_DIR@")
            normalized_found = hashlib.sha256(normalized_data).hexdigest()
            if found != digest and normalized_found != normalized_expected.get(relative):
                raise ValueError(f"OPT-01 original/normalized fingerprint mismatch: {relative}")
        elif found != digest:
            raise ValueError(f"OPT-01 fingerprint mismatch: {relative}")
        actual[relative] = found
    return actual


def nvidia_window_metrics(events, start_ns, end_ns):
    if end_ns <= start_ns:
        raise ValueError("invalid monotonic measurement window")
    starts, ends = {}, {}
    for event in events:
        call_id = event.get("id")
        stamp = event.get("monotonic_ns")
        if not call_id or not isinstance(stamp, int):
            raise ValueError("malformed NVIDIA event")
        target = starts if event.get("event") == "start" else ends if event.get("event") == "end" else None
        if target is None or call_id in target:
            raise ValueError("duplicate or unknown NVIDIA event")
        target[call_id] = event
    selected = 0
    failed = 0
    wrapper_cpu = 0.0
    for call_id, begin in starts.items():
        start = begin["monotonic_ns"]
        finish_event = ends.get(call_id)
        finish = finish_event["monotonic_ns"] if finish_event else None
        overlaps = start < end_ns and (finish is None or finish > start_ns)
        if not overlaps:
            continue
        if finish is None or finish < start:
            raise ValueError("NVIDIA query overlaps measurement without a completed result")
        if start < start_ns or start >= end_ns or finish > end_ns:
            raise ValueError("NVIDIA query crosses measurement boundary")
        selected += 1
        failed += int(finish_event.get("return_code", 0) != 0)
        cpu = finish_event.get("wrapper_cpu_seconds")
        if not isinstance(cpu, (int, float)) or cpu < 0:
            raise ValueError("invalid NVIDIA wrapper CPU record")
        wrapper_cpu += float(cpu)
    orphaned = set(ends) - set(starts)
    if orphaned:
        raise ValueError("NVIDIA completion without a start record")
    return NvidiaWindowMetrics(selected, failed, wrapper_cpu)


def verify_x11_window(checker, pid, env, log_path=None):
    command = [sys.executable, str(checker), str(pid)]
    if log_path is not None:
        command.extend(("--log", str(log_path)))
    result = subprocess.run(command, capture_output=True,
                            text=True, errors="replace", timeout=7, env=dict(env))
    if result.returncode:
        raise RuntimeError("X11 window probe failed: " + result.stderr[-500:])
    fields = result.stdout.split()
    if len(fields) != 3 or not re.fullmatch(r"0x[0-9a-fA-F]+", fields[0]):
        raise RuntimeError("X11 probe lacks positive window evidence")
    try:
        width, height = int(fields[1]), int(fields[2])
    except ValueError as error:
        raise RuntimeError("X11 probe returned invalid dimensions") from error
    if width < 1 or height < 1:
        raise RuntimeError("X11 window is not visible with positive geometry")
    return fields[0], width, height


def smoke_timing(smoke_test):
    return (3, 5, 1) if smoke_test else (30, 60, 3)


def build_scoped_process_argv(unit, process_env, command, systemd_run="systemd-run"):
    if not re.fullmatch(r"[A-Za-z0-9_.@-]+", unit):
        raise ValueError("invalid transient systemd unit name")
    assignments = []
    for key, value in process_env.items():
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", key) or "\x00" in str(value) or "\n" in str(value):
            raise ValueError("invalid isolated process environment")
        assignments.append(f"{key}={value}")
    return [systemd_run, "--user", "--scope", "--unit=" + unit,
            "/usr/bin/env", "-u", "WAYLAND_DISPLAY", "-u", "WAYLAND_SOCKET",
            "-u", "XDG_SESSION_TYPE", *assignments, *map(str, command)]
