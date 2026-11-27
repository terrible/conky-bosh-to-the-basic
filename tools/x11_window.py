#!/usr/bin/env python3
"""Validate a Conky X11 window using its log-reported XID or _NET_WM_PID."""
import argparse
import ctypes
import ctypes.util
import os
from pathlib import Path
import re
import stat
import sys
import time


class XWindowAttributes(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_int), ("y", ctypes.c_int),
        ("width", ctypes.c_int), ("height", ctypes.c_int),
        ("border_width", ctypes.c_int), ("depth", ctypes.c_int),
        ("visual", ctypes.c_void_p), ("root", ctypes.c_ulong),
        ("window_class", ctypes.c_int), ("bit_gravity", ctypes.c_int),
        ("win_gravity", ctypes.c_int), ("backing_store", ctypes.c_int),
        ("backing_planes", ctypes.c_ulong), ("backing_pixel", ctypes.c_ulong),
        ("save_under", ctypes.c_int), ("colormap", ctypes.c_ulong),
        ("map_installed", ctypes.c_int), ("map_state", ctypes.c_int),
        ("all_event_masks", ctypes.c_long), ("your_event_mask", ctypes.c_long),
        ("do_not_propagate_mask", ctypes.c_long),
        ("override_redirect", ctypes.c_int), ("screen", ctypes.c_void_p),
    ]


class XErrorEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int), ("display", ctypes.c_void_p),
        ("resourceid", ctypes.c_ulong), ("serial", ctypes.c_ulong),
        ("error_code", ctypes.c_ubyte), ("request_code", ctypes.c_ubyte),
        ("minor_code", ctypes.c_ubyte),
    ]


class X11:
    def __init__(self, display_name):
        library = ctypes.util.find_library("X11")
        if not library:
            raise RuntimeError("libX11 is unavailable")
        self.lib = ctypes.CDLL(library)
        self.lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.lib.XOpenDisplay.restype = ctypes.c_void_p
        self.display = self.lib.XOpenDisplay(display_name.encode())
        if not self.display:
            raise RuntimeError("cannot open the isolated DISPLAY")
        self.lib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        self.lib.XDefaultRootWindow.restype = ctypes.c_ulong
        self.lib.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.lib.XInternAtom.restype = ctypes.c_ulong
        self.lib.XQueryTree.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ulong)), ctypes.POINTER(ctypes.c_uint)]
        self.lib.XQueryTree.restype = ctypes.c_int
        self.lib.XGetWindowProperty.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.c_ulong, ctypes.c_long, ctypes.c_long, ctypes.c_int, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong),
            ctypes.POINTER(ctypes.POINTER(ctypes.c_ubyte))]
        self.lib.XGetWindowProperty.restype = ctypes.c_int
        self.lib.XGetGeometry.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
            ctypes.POINTER(ctypes.c_uint)]
        self.lib.XGetGeometry.restype = ctypes.c_int
        self.lib.XGetWindowAttributes.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
                                                   ctypes.POINTER(XWindowAttributes)]
        self.lib.XGetWindowAttributes.restype = ctypes.c_int
        self.lib.XFree.argtypes = [ctypes.c_void_p]
        self.lib.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.lib.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.lib.XSetErrorHandler.argtypes = [ctypes.c_void_p]
        self.lib.XSetErrorHandler.restype = ctypes.c_void_p
        self._errors = []
        callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p,
                                         ctypes.POINTER(XErrorEvent))
        self._error_callback = callback_type(self._on_error)
        self._previous_error_handler = self.lib.XSetErrorHandler(
            ctypes.cast(self._error_callback, ctypes.c_void_p))
        self.atom_pid = self.lib.XInternAtom(self.display, b"_NET_WM_PID", 0)
        self.atom_cardinal = self.lib.XInternAtom(self.display, b"CARDINAL", 0)

    def _on_error(self, _display, event):
        self._errors.append((event.contents.error_code, event.contents.resourceid,
                             event.contents.request_code))
        return 0

    def sync(self):
        self.lib.XSync(self.display, 0)
        if self._errors:
            code, resource, request = self._errors.pop(0)
            self._errors.clear()
            raise RuntimeError(
                f"Xlib error {code} on resource 0x{resource:x} (request {request})"
            )

    def root_window(self):
        return int(self.lib.XDefaultRootWindow(self.display))

    def children(self, window):
        root = ctypes.c_ulong()
        parent = ctypes.c_ulong()
        children = ctypes.POINTER(ctypes.c_ulong)()
        count = ctypes.c_uint()
        status = self.lib.XQueryTree(self.display, window, ctypes.byref(root),
                                     ctypes.byref(parent), ctypes.byref(children),
                                     ctypes.byref(count))
        self.sync()
        if not status:
            raise RuntimeError(f"XQueryTree failed for window 0x{window:x}")
        try:
            return [int(children[i]) for i in range(count.value)] if children else []
        finally:
            if children:
                self.lib.XFree(children)

    def pid(self, window):
        actual_type = ctypes.c_ulong()
        actual_format = ctypes.c_int()
        count = ctypes.c_ulong()
        after = ctypes.c_ulong()
        data = ctypes.POINTER(ctypes.c_ubyte)()
        status = self.lib.XGetWindowProperty(
            self.display, window, self.atom_pid, 0, 1, 0, self.atom_cardinal,
            ctypes.byref(actual_type), ctypes.byref(actual_format),
            ctypes.byref(count), ctypes.byref(after), ctypes.byref(data))
        self.sync()
        try:
            if status or not data or actual_format.value != 32 or count.value != 1:
                return None
            return int(ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[0])
        finally:
            if data:
                self.lib.XFree(data)

    def geometry(self, window):
        root = ctypes.c_ulong()
        x = ctypes.c_int()
        y = ctypes.c_int()
        width = ctypes.c_uint()
        height = ctypes.c_uint()
        border = ctypes.c_uint()
        depth = ctypes.c_uint()
        status = self.lib.XGetGeometry(
            self.display, window, ctypes.byref(root), ctypes.byref(x), ctypes.byref(y),
            ctypes.byref(width), ctypes.byref(height), ctypes.byref(border),
            ctypes.byref(depth))
        self.sync()
        if not status:
            raise RuntimeError("cannot read matched window geometry")
        return width.value, height.value

    def visible(self, window):
        attributes = XWindowAttributes()
        status = self.lib.XGetWindowAttributes(self.display, window,
                                               ctypes.byref(attributes))
        self.sync()
        if not status:
            raise RuntimeError("cannot read matched window visibility")
        if attributes.map_state != 2:  # IsViewable
            raise RuntimeError("matched Conky window is not mapped and viewable")

    def close(self):
        try:
            self.sync()
        finally:
            self.lib.XSetErrorHandler(self._previous_error_handler)
            self.lib.XCloseDisplay(self.display)


def conky_window_xid(log_path):
    path = Path(log_path)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("Conky log must be a regular non-symlink file")
    text = path.read_text(errors="replace")
    matches = re.findall(r"drawing to created window\s+(0x[0-9a-fA-F]+)", text)
    xids = list(dict.fromkeys(int(match, 16) for match in matches))
    if not xids:
        raise RuntimeError("Conky log has not reported a created window")
    if len(xids) != 1:
        raise RuntimeError(f"Conky log reports ambiguous window XIDs: {xids}")
    return xids[0]


def wait_for_conky_window_xid(log_path, pid, *, timeout=5, interval=0.1):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return conky_window_xid(log_path)
        except RuntimeError as error:
            if "has not reported a created window" not in str(error):
                raise
            if not Path(f"/proc/{pid}").exists():
                raise RuntimeError(f"Conky PID {pid} exited before reporting its X11 window") from error
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError(
                    f"Conky PID {pid} did not report an X11 window within {timeout:g}s"
                ) from error
            time.sleep(min(interval, remaining))


def resolve_window(x11, target_pid, reported_xid=None):
    root = x11.root_window()
    pending = [root]
    seen = set()
    while pending:
        window = pending.pop()
        if window in seen:
            continue
        seen.add(window)
        pending.extend(x11.children(window))

    if reported_xid is not None:
        if reported_xid == root or reported_xid not in seen:
            raise RuntimeError(
                f"Conky-reported XID 0x{reported_xid:x} is not in the isolated X11 window tree"
            )
        owner_pid = x11.pid(reported_xid)
        if owner_pid is not None and owner_pid != target_pid:
            raise RuntimeError(
                f"Conky-reported XID 0x{reported_xid:x} belongs to PID {owner_pid}, "
                f"not PID {target_pid}"
            )
        window = reported_xid
    else:
        found = [window for window in seen if x11.pid(window) == target_pid]
        if len(found) != 1:
            raise RuntimeError(f"expected one window for PID {target_pid}, found {len(found)}")
        window = found[0]

    x11.visible(window)
    width, height = x11.geometry(window)
    if width < 1 or height < 1:
        raise RuntimeError("matched Conky window is empty")
    return window, width, height


def wait_for_stable_window(x11, target_pid, reported_xid=None, *, minimum_width=128,
                           stable_samples=3, interval=0.1, timeout=5):
    deadline = time.monotonic() + timeout
    previous = None
    stable = 0
    last_error = "window geometry did not stabilize"
    while time.monotonic() < deadline:
        try:
            window, width, height = resolve_window(x11, target_pid, reported_xid)
            if width < minimum_width:
                last_error = (f"Conky window is still initializing: {width}x{height}; "
                              f"expected width >= {minimum_width}")
                stable = 0
            elif previous == (window, width, height):
                stable += 1
                if stable >= stable_samples:
                    return window, width, height
            else:
                previous = (window, width, height)
                stable = 1
        except RuntimeError as error:
            last_error = str(error)
            stable = 0
            previous = None
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(interval, remaining))
    raise RuntimeError(f"Conky window failed stable-view validation: {last_error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--log", type=Path,
                        help="Conky stdout/stderr log containing its created XID")
    parser.add_argument("--timeout", type=float, default=5,
                        help="maximum seconds to wait for a stable, visible panel")
    args = parser.parse_args()
    if os.environ.get("BOSH_QA_ISOLATED_X11") != "1":
        raise RuntimeError("refusing X11 probe without the isolated-QA marker")
    display_name = os.environ.get("DISPLAY")
    if not display_name:
        raise RuntimeError("DISPLAY is not set to the isolated X server")
    if not re.fullmatch(r"(?:(?:unix/)?):[0-9]+(?:\.[0-9]+)?", display_name):
        raise RuntimeError("DISPLAY must name a local isolated X server")
    authority = Path(os.environ.get("XAUTHORITY", ""))
    if not authority.is_file() or authority.is_symlink():
        raise RuntimeError("XAUTHORITY must be a private regular file")
    if stat.S_IMODE(authority.stat().st_mode) & 0o077:
        raise RuntimeError("XAUTHORITY permissions must be private (0600 or stricter)")
    started = time.monotonic()
    reported_xid = wait_for_conky_window_xid(args.log, args.pid, timeout=args.timeout) if args.log else None
    x11 = X11(display_name)
    try:
        remaining = args.timeout - (time.monotonic() - started)
        if remaining <= 0:
            raise RuntimeError("Conky startup consumed the X11 window probe timeout")
        window, width, height = wait_for_stable_window(
            x11, args.pid, reported_xid, timeout=remaining)
        print(f"0x{window:x} {width} {height}")
    finally:
        x11.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"X11 window lookup failed: {error}", file=sys.stderr)
        raise SystemExit(1)
