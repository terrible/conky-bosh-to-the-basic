"""Conky X11 backend feature probe and configuration normalization."""
import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

UNKNOWN_BACKEND = re.compile(r"(?:unknown|unrecognized|invalid).{0,60}output_backend|output_backend.{0,60}(?:unknown|unrecognized|invalid)", re.I | re.S)


def supports_output_backend(output, returncode=0):
    """Require the probe's positive marker; a quiet successful exit proves nothing."""
    return returncode == 0 and "backend-probe" in output and not bool(UNKNOWN_BACKEND.search(output))


def detect_output_backend(conky):
    with tempfile.TemporaryDirectory(prefix="bosh-conky-probe-") as temp:
        config = Path(temp) / "probe.conf"
        config.write_text("conky.config = { output_backend = 'x11', out_to_console = true, out_to_x = false, total_run_times = 1, update_interval = 0.1 }\nconky.text = 'backend-probe'\n")
        env = dict(os.environ, HOME=temp, LC_ALL="C")
        env.pop("WAYLAND_DISPLAY", None)
        env.pop("WAYLAND_SOCKET", None)
        env.pop("DISPLAY", None)
        env.pop("DBUS_SESSION_BUS_ADDRESS", None)
        env["XDG_CONFIG_HOME"] = str(Path(temp) / "config")
        env["XDG_DATA_HOME"] = str(Path(temp) / "data")
        env["XDG_CACHE_HOME"] = str(Path(temp) / "cache")
        env["XDG_STATE_HOME"] = str(Path(temp) / "state")
        result = subprocess.run([conky, "-c", str(config)], capture_output=True,
                                text=True, errors="replace", timeout=5, env=env)
        output = result.stdout + "\n" + result.stderr
        if "backend-probe" not in output:
            raise RuntimeError("Conky backend capability probe returned no positive marker: " + output[-1000:])
        if UNKNOWN_BACKEND.search(output):
            return False
        if result.returncode:
            raise RuntimeError("Conky backend capability probe failed: " + output[-1000:])
        return True


def normalize_config(source, destination, conky, xinerama_head=None):
    modern = detect_output_backend(conky)
    text = Path(source).read_text()
    text = normalize_text(text, str(Path(destination).parent), modern, xinerama_head)
    Path(destination).write_text(text)
    return "output_backend=x11" if modern else "out_to_x=true (legacy)"


def normalize_text(text, theme_dir, modern, xinerama_head=None):
    text = text.replace("@CONKY_DIR@", theme_dir)
    text = re.sub(r"(?m)^\s*(?:output_backend|out_to_x)\s*=.*\n", "", text)
    if modern:
        text = re.sub(r"(?m)^(\s*)xftalpha(\s*=)", r"\1text_alpha\2", text)
        text = re.sub(r"(?m)^(\s*)own_window_colour(\s*=)", r"\1own_window_color\2", text)
    else:
        text = re.sub(r"(?m)^(\s*)text_alpha(\s*=)", r"\1xftalpha\2", text)
        text = re.sub(r"(?m)^(\s*)own_window_color(\s*=)", r"\1own_window_colour\2", text)
    if xinerama_head is not None:
        text, count = re.subn(r"(?m)^(\s*xinerama_head\s*=\s*)\d+", rf"\g<1>{xinerama_head}", text)
        if count != 1:
            raise ValueError("expected exactly one xinerama_head setting in copied Conky config")
    key = "output_backend = 'x11'," if modern else "out_to_x = true,"
    text = text.replace("conky.config = {", "conky.config = {\n    " + key, 1)
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--conky", default=shutil.which("conky") or "conky")
    parser.add_argument("--xinerama-head", type=int)
    args = parser.parse_args()
    print(normalize_config(args.source, args.destination, args.conky, args.xinerama_head))


if __name__ == "__main__":
    main()
