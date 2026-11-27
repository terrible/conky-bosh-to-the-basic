"""Format Conky markup from one set of samples. No persistent client cache."""
import sys

from hardware_metrics import (HWMON, INTEL_FILE, cpu_temperatures, intel_load,
                              memory_display, memory_percent, nvidia_snapshot)


FONT = "${font NotoSans:size=9}"


def render(label, value, warm, hot):
    color = "${color}"
    display = "N/D"
    if value is not None:
        if value >= hot:
            color = "${color4}"
        elif value >= warm:
            color = "${color3}"
        display = f"{value:.0f}°C"
    return FONT + label + "${alignr}" + color + display + "${color}"


def temperature_rows(hwmon, gpu):
    package, average = cpu_temperatures(hwmon)
    return [render("CPU PACKAGE", package, 70, 85), render("CPU PROMEDIO", average, 70, 85),
            render("NVIDIA", gpu.temp, 75, 85)]


def bar(value):
    return "${lua_bar 4,259 bosh_percent " + str(value) + "}"


def full_panel(hwmon=HWMON, intel_file=INTEL_FILE, nvidia_bin="nvidia-smi"):
    gpu = nvidia_snapshot(nvidia_bin)
    intel = intel_load(intel_file)
    rows = [
        FONT + "GPU MEMORY ${alignr}" + (memory_display(gpu) or "N/D"),
        bar(memory_percent(gpu) or 0),
        FONT + "GPU INTEL LOAD ${alignr}" + (f"{intel:.2f}%" if intel is not None else "N/D"),
        # OPT-01's Intel reader emits an execbar row for a valid measurement.
        # Keep the same row with a Lua bar, avoiding an extra child process.
        *( [bar(intel)] if intel is not None else [] ),
        *( [" "] if intel is None else [] ),
        FONT + "GPU NVIDIA LOAD ${alignr}" + (f"{gpu.util}%" if gpu.util is not None else "N/D"),
        bar(gpu.util or 0),
        "",
        "${color2}${font NotoSans:bold:size=10}TEMPERATURA${color}",
        *temperature_rows(hwmon, gpu),
    ]
    return "\n".join(rows)


if __name__ == "__main__":
    if sys.argv[1:] == ["--all"]:
        print(full_panel(), end="")
    else:
        print("\n".join(temperature_rows(HWMON, nvidia_snapshot())), end="")
