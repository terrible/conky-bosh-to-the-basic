#!/usr/bin/env python3
"""Run one isolated Conky sample in the caller's transient systemd scope."""
import argparse
import csv
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

try:
    from qa_runtime import nvidia_window_metrics, verify_x11_window
except ImportError:
    from tools.qa_runtime import nvidia_window_metrics, verify_x11_window

CGROUP_ROOT = Path("/sys/fs/cgroup")
RENDER_FAILURE = re.compile(
    r"\[(?:error|fatal)\]|lua.*(?:error|failed)|(?:unknown|invalid) (?:setting|key)|"
    r"failed to (?:open|load|create)|cannot open display|unable to open display",
    re.I,
)


def read_cpu_usec(path):
    for line in path.read_text().splitlines():
        key, value = line.split()
        if key == "usage_usec":
            return int(value)
    raise RuntimeError("cgroup cpu.stat has no usage_usec")


def cgroup_for_pid(pid):
    for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines():
        if line.startswith("0::"):
            relative = line[3:]
            path = (CGROUP_ROOT / relative.lstrip("/")).resolve(strict=True)
            if not path.is_relative_to(CGROUP_ROOT):
                raise RuntimeError("cgroup path escapes cgroup v2 mount")
            return path
    raise RuntimeError("process is not in cgroup v2")


def process_ids(cgroup):
    return {int(value) for value in (cgroup / "cgroup.procs").read_text().split()}


def rss_kib(pid):
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1])
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        pass
    return 0


def proc_cpu_ticks(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    return int(fields[11]) + int(fields[12])


def nvidia_events(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def wait_alive(process, duration, cgroup, worker_pid, log_path):
    deadline = time.monotonic() + duration
    panel_peak = wrapper_peak = 0
    while True:
        if process.poll() is not None:
            raise RuntimeError(f"Conky exited early with status {process.returncode}")
        members = process_ids(cgroup)
        if process.pid not in members:
            raise RuntimeError("Conky escaped the benchmark cgroup")
        if worker_pid not in members:
            raise RuntimeError("benchmark worker escaped its dedicated cgroup")
        worker_peak = rss_kib(worker_pid)
        wrapper_peak = max(wrapper_peak, worker_peak)
        panel_peak = max(panel_peak, sum(rss_kib(pid) for pid in members if pid != worker_pid))
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            log_path.flush()
            content = Path(log_path.name).read_text(errors="replace")
            failure = RENDER_FAILURE.search(content)
            if failure:
                raise RuntimeError(f"Conky render log reports failure: {failure.group(0)}")
            return panel_peak, wrapper_peak
        time.sleep(min(0.2, remaining))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--warmup", type=float, default=30)
    parser.add_argument("--measure", type=float, default=60)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--nvidia-log", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--sample", required=True, type=int)
    parser.add_argument("--unit-name", required=True)
    parser.add_argument("--x11-window-checker", required=True, type=Path)
    args = parser.parse_args()

    config = args.config.resolve(strict=True)
    cgroup = cgroup_for_pid(os.getpid())
    if cgroup.name != args.unit_name + ".scope":
        raise RuntimeError(f"process is outside its dedicated transient scope: {cgroup.name}")
    if process_ids(cgroup) != {os.getpid()}:
        raise RuntimeError("benchmark scope is not exclusive before Conky launch")
    cpu_stat = cgroup / "cpu.stat"
    if not cpu_stat.is_file():
        raise RuntimeError("cgroup cpu.stat is unavailable")

    def check_window(pid):
        log.flush()
        window_id, width, height = verify_x11_window(
            args.x11_window_checker, pid, os.environ.copy(), args.log
        )
        return window_id, width, height

    process = None
    with args.log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            ["conky", "-c", str(config)], stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True, close_fds=True,
        )
        try:
            wait_alive(process, 3, cgroup, os.getpid(), log)
            window = check_window(process.pid)
            warm_panel_peak, warm_wrapper_peak = wait_alive(
                process, args.warmup, cgroup, os.getpid(), log
            )
            if check_window(process.pid) != window:
                raise RuntimeError("Conky window changed or became invalid during warmup")
            start_cpu = read_cpu_usec(cpu_stat)
            worker_start = proc_cpu_ticks(os.getpid())
            start = time.monotonic()
            start_ns = time.monotonic_ns()
            panel_peak, wrapper_peak = wait_alive(
                process, args.measure, cgroup, os.getpid(), log
            )
            end_cpu = read_cpu_usec(cpu_stat)
            worker_end = proc_cpu_ticks(os.getpid())
            end_ns = time.monotonic_ns()
            elapsed = time.monotonic() - start
            if process.poll() is not None:
                raise RuntimeError(f"Conky exited before sample completed: {process.returncode}")
            if check_window(process.pid) != window:
                raise RuntimeError("Conky window changed or became invalid during measurement")
            log.flush()
            os.fsync(log.fileno())
            content = Path(log.name).read_text(errors="replace")
            failure = RENDER_FAILURE.search(content)
            if failure:
                raise RuntimeError(f"Conky render log reports failure: {failure.group(0)}")
        finally:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                    process.wait(timeout=5)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait()

    nvidia = nvidia_window_metrics(nvidia_events(args.nvidia_log), start_ns, end_ns)
    cpu_seconds = (end_cpu - start_cpu) / 1_000_000
    cpu_percent = 100 * cpu_seconds / elapsed
    worker_ticks = worker_end - worker_start
    tick_hz = os.sysconf("SC_CLK_TCK")
    wrapper_cpu = worker_ticks / tick_hz
    panel_cpu = max(0.0, cpu_seconds - wrapper_cpu)
    query_count = nvidia.queries
    queries_per_minute = query_count * 60 / elapsed
    row = [args.variant, args.sample, f"{elapsed:.3f}", f"{cpu_seconds:.6f}",
           f"{cpu_percent:.3f}", f"{panel_cpu:.6f}", f"{wrapper_cpu:.6f}",
           f"{nvidia.wrapper_cpu_seconds:.6f}",
           panel_peak * 1024, wrapper_peak * 1024, query_count,
           nvidia.failed, f"{queries_per_minute:.3f}", str(window[0]),
           f"{window[1]}x{window[2]}",
           str(args.log)]
    with args.csv.open("a", newline="") as stream:
        csv.writer(stream).writerow(row)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"benchmark sample invalid: {error}", file=os.sys.stderr)
        raise SystemExit(1)
