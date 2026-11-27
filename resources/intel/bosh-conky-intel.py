#!/usr/bin/python3
"""Publish one numeric Intel Render/3D sample for the unprivileged panel."""

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

RUNTIME = Path("/run/bosh-conky")


def busy_percent(samples):
    try:
        raw = samples[-1]["engines"]["Render/3D"]["busy"]
        if isinstance(raw, bool):
            raise ValueError("boolean metric")
        value = float(raw)
    except (KeyError, IndexError, TypeError, OverflowError) as error:
        raise ValueError("missing Intel sample") from error
    if not math.isfinite(value) or not 0 <= value <= 100:
        raise ValueError("invalid Intel sample")
    return value


def sample():
    result = subprocess.run(
        ["/usr/bin/intel_gpu_top", "-d", "pci:vendor=8086", "-J", "-s", "1000", "-n", "2"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, timeout=8, check=True,
    )
    return busy_percent(json.loads(result.stdout))


def publish(directory, value):
    # The systemd RuntimeDirectory is writable only by this service.
    with tempfile.NamedTemporaryFile(dir=directory, mode="w", delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(f"{value:.2f}\n")
            stream.flush()
            os.fchmod(stream.fileno(), 0o644)
            os.replace(temporary, directory / "intel-load")
        finally:
            temporary.unlink(missing_ok=True)


def update(directory):
    try:
        publish(directory, sample())
    except (OSError, ValueError, subprocess.SubprocessError):
        (directory / "intel-load").unlink(missing_ok=True)
        return False
    return True


def main():
    while True:
        started = time.monotonic()
        if not update(RUNTIME):
            print("Intel PMU sample unavailable", file=sys.stderr)
            return 1
        time.sleep(max(0, 5 - (time.monotonic() - started)))


if __name__ == "__main__":
    sys.exit(main())
