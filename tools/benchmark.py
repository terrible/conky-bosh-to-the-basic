"""Measure the GPU polling model or run paired Conky trials in a disposable desktop."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import statistics
import subprocess
import sys
import tempfile
import time

SCRIPTS = Path(__file__).resolve().parents[1] / "bosh-to-the-basic/scripts"


def order(pairs):
    for index in range(pairs):
        yield ("candidate", "OPT-01") if index % 2 else ("OPT-01", "candidate")


def usage(stat):
    for line in stat.read_text().splitlines():
        key, value = line.split()
        if key == "usage_usec":
            return int(value)
    raise ValueError("cpu.stat lacks usage_usec")


def cpu_percent(start, end, seconds):
    if end < start or seconds <= 0:
        raise ValueError("invalid accounting interval")
    return (end - start) / (10000 * seconds)


def child_cpu():
    r = resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


REFERENCE = {
    "cpu-temp.sh": "dad1afb985721689b78cf1effe8e81ff0c206444a572a8bfbfc6a32e3daae31d",
    "gpu-metric.sh": "042a7b788df0c06cc738c4713000c78e6b8c66c13f5c667650e29a8060f3e16c",
    "intel-reader.py": "1a12a0be649a505be7a2b13827d90a5feb119209c98a1514933a8bd6d88fadbb",
    "temperature-panel.py": "3f063b6749f6f4c87680638645a1a847df2a890c3c49a31d3785db93251aa3e6",
}


def reference_commands(reference, base):
    """Replay the audited GPU and thermal helpers with two fixture path substitutions."""
    scripts = base / "reference"
    scripts.mkdir()
    for name, checksum in REFERENCE.items():
        source = (reference / "scripts" / name).read_bytes()
        if hashlib.sha256(source).hexdigest() != checksum:
            raise ValueError("unknown reference helper: " + name)
        source = source.replace(b"/sys/class/hwmon", bytes(base / "hwmon"))
        source = source.replace(b"/run/bosh-conky/intel-load", bytes(base / "intel-load"))
        (scripts / name).write_bytes(source)
    commands = [["bash", scripts / "gpu-metric.sh", key] for key in ("memory", "memory_percent", "util", "util")]
    commands.extend([[sys.executable, "-IB", scripts / name]
                     for name in ("intel-reader.py", "temperature-panel.py")])
    return commands


def simulated(pairs, reference=None):
    # Model the five requests present in the reference .conf + temperature helper.
    # Do not equate this mock or its child CPU time with desktop CPU usage.
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp)
        mock = base / "nvidia-smi"
        mock.write_text("""#!/bin/sh
echo call >> "$BENCH_CALLS"
case "$*" in
    *memory.used*utilization*|*utilization*memory.used*|*temperature*memory.used*) echo "$BENCH_ROW" ;;
    *memory.used*) echo '100, 1000' ;;
    *temperature*) echo 48 ;;
    *) echo 23 ;;
esac
""")
        mock.chmod(0o700)
        calls = base / "calls"
        env = dict(os.environ, BENCH_CALLS=str(calls), BENCH_ROW="100, 1000, 23, 48",
                   PYTHONDONTWRITEBYTECODE="1", PATH=f"{base}:/usr/bin:/bin")
        legacy = reference_commands(reference, base) if reference else None
        sensor = base / "hwmon/hwmon0"
        sensor.mkdir(parents=True)
        (sensor / "name").write_text("coretemp")
        for index, label in enumerate(["Package id 0", "Core 0", "Core 1"], 1):
            (sensor / f"temp{index}_label").write_text(label)
            (sensor / f"temp{index}_input").write_text("48000")
        driver = ('import runpy,sys; from pathlib import Path; '
                  'sys.path.insert(0, str(Path(sys.argv[1]).parent)); m=runpy.run_path(sys.argv[1]); '
                  'print(m["full_panel"](hwmon=Path(sys.argv[2]), intel_file=Path(sys.argv[3]), '
                  'nvidia_bin=sys.argv[4]))')
        results = []
        for sequence in order(pairs):
            for label in sequence:
                calls.write_text("")
                (base / "intel-load").write_text("25.50")
                before = child_cpu()
                start = time.monotonic()
                if label == "candidate":
                    out = subprocess.check_output(
                        [sys.executable, "-IB", "-c", driver, str(SCRIPTS / "temperature-panel.py"),
                         str(base / "hwmon"), str(base / "intel-load"), str(mock)],
                        env=env, text=True, timeout=5)
                    if not all(marker in out for marker in ("GPU NVIDIA LOAD", "100 / 1000 MiB", "23%", "48°C", "25.50%")):
                        raise ValueError("missing candidate GPU output")
                elif legacy:
                    outputs = [subprocess.check_output(cmd, env=env, text=True, timeout=4) for cmd in legacy]
                    if [v.strip() for v in outputs[:4]] != ["100 / 1000 MiB", "10", "23", "23"] or "48°C" not in outputs[-1]:
                        raise ValueError("unexpected reference sample")
                else:
                    for field in ("memory.used,memory.total",) * 2 + ("utilization.gpu",) * 2 + ("temperature.gpu",):
                        subprocess.run([mock, f"--query-gpu={field}", "--format=csv,noheader,nounits"],
                                       env=env, stdout=subprocess.DEVNULL, check=True, timeout=2)
                count = len(calls.read_text().splitlines())
                if count != (1 if label == "candidate" else 5):
                    raise ValueError(f"unexpected NVIDIA queries for {label}: {count}")
                results.append(dict(label=label, queries=count, child_cpu_ms=round((child_cpu()-before)*1000, 3),
                                    elapsed_ms=round((time.monotonic()-start)*1000, 3)))
        return {"mode": "synthetic", "baseline": "audited GPU and thermal helpers" if legacy else "query replay only",
                "candidate": "combined GPU and thermal helper", "runs": results}


def dedicated_group():
    # The caller supplies an already-delegated, otherwise empty cgroup v2.
    line = next((s for s in Path("/proc/self/cgroup").read_text().splitlines() if s.startswith("0::")), "")
    relative = Path(line[3:])
    if not relative.is_absolute() or relative == Path("/") or ".." in relative.parts:
        raise ValueError("a dedicated non-root cgroup v2 is required")
    group = Path("/sys/fs/cgroup").joinpath(*relative.parts[1:])
    if set((group / "cgroup.procs").read_text().split()) != {str(os.getpid())} or any(d.is_dir() for d in group.iterdir()):
        raise ValueError("benchmark must be the sole process in a dedicated leaf cgroup")
    return group


def check_lab(lab, home, configs):
    if (lab.parent != Path("/tmp") or lab.stat().st_uid != os.getuid()
            or lab.stat().st_mode & 0o077 or lab not in home.resolve().parents):
        raise ValueError("hardware mode needs a private /tmp lab and a separate HOME inside it")
    if any(lab not in path.resolve().parents for path in configs):
        raise ValueError("all configs must be inside the lab")


def real(args):
    if not args.lab or not args.baseline or not args.candidate:
        raise ValueError("hardware mode requires --lab, --baseline and --candidate")
    lab = args.lab.resolve(strict=True)
    configs = {"OPT-01": args.baseline.resolve(strict=True), "candidate": args.candidate.resolve(strict=True)}
    check_lab(lab, Path.home(), configs.values())
    if configs["OPT-01"] == configs["candidate"]:
        raise ValueError("two distinct configs are required")
    runs = []
    for sequence in order(args.pairs):
        for label in sequence:
            group = dedicated_group()
            env = dict(os.environ)
            for var, subdir in (("CONFIG", ".config"), ("DATA", ".local/share"),
                                ("STATE", ".local/state"), ("CACHE", ".cache")):
                env["XDG_" + var + "_HOME"] = str(Path.home() / subdir)
            process = subprocess.Popen(["conky", "-c", str(configs[label])], start_new_session=True, env=env,
                                       stdout=subprocess.DEVNULL)
            try:
                for duration in (args.warmup, args.seconds):
                    start = time.monotonic()
                    before = usage(group / "cpu.stat")
                    try:
                        code = process.wait(timeout=duration)
                    except subprocess.TimeoutExpired:
                        continue
                    raise RuntimeError(f"Conky exited early ({code})")
                percent = cpu_percent(before, usage(group / "cpu.stat"), time.monotonic() - start)
                runs.append(dict(label=label, cpu_percent=percent))
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
    summaries = {}
    for label in configs:
        samples = [r["cpu_percent"] for r in runs if r["label"] == label]
        summaries[label] = {"median": statistics.median(samples), "min": min(samples), "max": max(samples)}
    return {"mode": "hardware; dedicated cgroup v2, CPU percent of one core", "runs": runs,
            "warmup_s": args.warmup, "measurement_s": args.seconds, "summary": summaries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("synthetic", "hardware"), default="synthetic")
    parser.add_argument("--pairs", type=int, default=3)
    parser.add_argument("--warmup", type=int, default=60)
    parser.add_argument("--seconds", type=int, default=300)
    parser.add_argument("--reference", type=Path, help="optional normalized OPT-01 theme for synthetic comparison")
    for option in ("lab", "baseline", "candidate"):
        parser.add_argument("--" + option, type=Path)
    args = parser.parse_args()
    if min(args.pairs, args.warmup, args.seconds) < 1:
        parser.error("positive pairs and durations required")
    try:
        result = simulated(args.pairs, args.reference) if args.mode == "synthetic" else real(args)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Benchmark failed: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
