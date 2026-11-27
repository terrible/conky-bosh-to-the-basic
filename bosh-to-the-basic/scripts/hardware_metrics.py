"""Read one hardware snapshot for the unprivileged Conky client."""
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from typing import NamedTuple


HWMON = Path("/sys/class/hwmon")
INTEL_FILE = Path("/run/bosh-conky/intel-load")
NVIDIA_FIELDS = "memory.used,memory.total,utilization.gpu,temperature.gpu"
NVIDIA_TEMPERATURE = re.compile(r"\d+(?:\.\d+)?\Z")


def intel_load(path=INTEL_FILE, now=None):
    """Consume the collector's atomic snapshot without blocking on special files."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o022:
                return None
            age = (time.time() if now is None else now) - info.st_mtime
            if not 0 <= age <= 15:
                return None
            raw = os.read(fd, 65)
            if len(raw) > 64:
                return None
            value = float(raw)
            return value if math.isfinite(value) and 0 <= value <= 100 else None
        finally:
            os.close(fd)
    except (OSError, ValueError):
        return None


def sysfs_text(path):
    try:
        with path.open("rb") as stream:
            raw = stream.read(65)
        if len(raw) <= 64:
            return raw.decode("ascii").strip()
    except (OSError, UnicodeError):
        pass
    return ""


def cpu_temperatures(root=HWMON):
    """Scan labeled CPU sensors once. Keep OPT-01's round-then-average rule."""
    package = None
    amd = {}
    cores = []
    for device in sorted(root.glob("hwmon*")):
        name = sysfs_text(device / "name")
        if name not in ("coretemp", "k10temp"):
            continue
        for label_file in device.glob("temp*_label"):
            label = sysfs_text(label_file)
            raw = sysfs_text(label_file.with_name(label_file.name[:-5] + "input"))
            if not raw.isdecimal() or int(raw) > 150000:
                continue
            degrees = round(int(raw) / 1000)
            if name == "k10temp":
                if label in ("Tctl", "Tdie"):
                    amd.setdefault(label, degrees)
            elif label == "Package id 0":
                package = degrees
            elif re.fullmatch(r"Core [0-9]+", label):
                cores.append(degrees)
    if package is None:
        package = amd.get("Tdie", amd.get("Tctl"))
    return package, round(sum(cores) / len(cores)) if cores else None


class Nvidia(NamedTuple):
    memory: tuple | None = None
    util: int | None = None
    temp: float | None = None


def parse_nvidia_temperature(raw):
    """Parse NVIDIA's integer or decimal Celsius field without weakening other fields."""
    if not NVIDIA_TEMPERATURE.fullmatch(raw):
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if math.isfinite(value) and 0 <= value <= 150 else None


def nvidia_snapshot(binary="nvidia-smi", timeout=1.5):
    """OPT-01 shows the first GPU. Query its four integer fields at once."""
    try:
        result = subprocess.run(
            [binary, "-i", "0", "--query-gpu=" + NVIDIA_FIELDS, "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True, timeout=timeout,
        )
        raw = result.stdout.decode("ascii").strip()
        fields = [value.strip() for value in raw.split(",")]
        if len(raw) > 128 or len(fields) != 4:
            return Nvidia()
        used, total, util = [int(value) if value.isdecimal() else None for value in fields[:3]]
        temp = parse_nvidia_temperature(fields[3])
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
        return Nvidia()
    memory = None
    if used is not None and total and used <= total:
        memory = used, total
    return Nvidia(memory, util if util is not None and util <= 100 else None, temp)


def memory_display(snapshot):
    return "%d / %d MiB" % snapshot.memory if snapshot.memory else None


def memory_percent(snapshot):
    if snapshot.memory:
        used, total = snapshot.memory
        return round(100 * used / total)
    return None


def legacy_value(device, metric):
    """Scalar entry points used by installations calling the original scripts."""
    if device == "cpu":
        package, average = cpu_temperatures()
        return {"package": package, "avg": average}.get(metric)
    if device == "intel":
        load = intel_load()
        return round(load) if load is not None else None
    snapshot = nvidia_snapshot()
    temp = snapshot.temp
    if temp is not None and temp.is_integer():
        temp = int(temp)  # Preserve the legacy scalar script's integer output.
    return {"temp": temp, "util": snapshot.util, "memory": memory_display(snapshot),
            "memory_percent": memory_percent(snapshot)}.get(metric)


if __name__ == "__main__":
    value = legacy_value(*sys.argv[1:])
    print("--" if value is None else value, end="")
