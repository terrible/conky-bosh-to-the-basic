"""User-scoped installer for a fixed set of theme files (Linux, stdlib only)."""
import argparse
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import stat
import subprocess
import sys

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from conky_backend import detect_output_backend, normalize_text

SOURCE = Path(__file__).resolve().parents[1] / "bosh-to-the-basic"
CONF = "bosh-to-the-basic.conf"
START = "startup/bosh-to-the-basic-startup.sh"
FILES = (
    CONF, START, "README-FEDORA45.txt", "lua/bosh-to-the-basic.lua",
    "scripts/network-info.sh", "scripts/distro-info.sh", "scripts/cpu-temp.sh",
    "scripts/gpu-metric.sh", "scripts/intel-gpu-metric.sh", "scripts/intel-reader.py",
    "scripts/temperature-panel.py", "scripts/hardware_metrics.py",
)
DESKTOP = "autostart/conky.desktop"
LEGACY = "autostart/conky-bosh-to-the-basic.desktop"
LIMIT = 16 * 1024 * 1024
STATE_LIMIT = 128 * 1024 * 1024
DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


class Refused(ValueError):
    """Input, permissions or installation state require human attention."""


def checked_path(value):
    path = Path(value)
    if (not path.is_absolute() or ".." in path.parts or
            any(not (c.isalnum() or c in "/ _.-+") for c in str(path))):
        raise Refused(f"Ruta incompatible: {path}")
    return path


def check_writable(home, path):
    """Preflight the nearest existing destination directory without creating it."""
    while True:
        try:
            with directory(home, path) as fd:
                if not os.access(".", os.W_OK | os.X_OK, dir_fd=fd):
                    raise Refused(f"Directorio sin permiso de escritura: {path}")
            return
        except FileNotFoundError:
            if path == home:
                raise
            path = path.parent


def real_dir(fd, private=False):
    info = os.fstat(fd)
    if info.st_uid != os.getuid() or info.st_mode & (0o077 if private else 0o022):
        raise Refused("Directorio con propietario o permisos inseguros")


@contextmanager
def directory(home, path, create=False):
    """Walk relative to a pinned HOME. Never traverse a descendant symlink."""
    fd = os.open(home, DIRECTORY)
    try:
        real_dir(fd)
        for name in path.relative_to(home).parts:
            if create:
                try:
                    os.mkdir(name, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(name, DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = child
            real_dir(fd)
        yield fd
    finally:
        os.close(fd)


def snapshot(home, path, limit=LIMIT):
    try:
        with directory(home, path.parent) as parent:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as f:
                info = os.fstat(f.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                    raise Refused(f"Se esperaba un archivo regular propio: {path.name}")
                data = f.read(limit + 1)
                if len(data) > limit:
                    raise Refused(f"Archivo demasiado grande: {path.name}")
                # Only ordinary permissions may be restored.
                return data, info.st_mode & 0o777
    except FileNotFoundError:
        return None


def write_file(home, path, value):
    with directory(home, path.parent, create=value is not None) as fd:
        if value is None:
            os.unlink(path.name, dir_fd=fd)
        else:
            data, mode = value
            name = ".bosh-" + secrets.token_hex(12)
            tmp = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                          0o600, dir_fd=fd)
            try:
                with os.fdopen(tmp, "wb") as f:
                    f.write(data)
                    f.flush()
                    os.fchmod(f.fileno(), mode)
                    os.fsync(f.fileno())
                os.replace(name, path.name, src_dir_fd=fd, dst_dir_fd=fd)
            finally:
                try:
                    os.unlink(name, dir_fd=fd)
                except FileNotFoundError:
                    pass
        os.fsync(fd)


def digest(value):
    if value is None:
        return None
    data, mode = value
    return f"{mode:o}:" + hashlib.sha256(data).hexdigest()


def pack(value):
    if value is None:
        return None
    data, mode = value
    return {"data": base64.b64encode(data).decode(), "mode": mode, "digest": digest(value)}


def unpack(record):
    if record is None:
        return None
    value = base64.b64decode(record["data"], validate=True), record["mode"]
    if not isinstance(value[1], int) or not 0 <= value[1] <= 0o777 or digest(value) != record["digest"]:
        raise Refused("Respaldo dañado")
    return value


def state_json(data):
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > STATE_LIMIT:
        raise Refused("El estado supera el límite de recuperación")
    return encoded, 0o600


def load_json(home, path):
    contents = snapshot(home, path, STATE_LIMIT)
    if contents is None:
        return None
    if contents[1] != 0o600:
        raise Refused(f"Permisos inseguros en {path.name}")
    return json.loads(contents[0])


class Installation:
    def __init__(self):
        self.home = checked_path(os.environ["HOME"])
        if self.home == Path("/") or self.home.resolve(strict=True) != self.home:
            raise Refused("HOME no es un directorio personal seguro")
        config = checked_path(os.getenv("XDG_CONFIG_HOME") or self.home / ".config")
        state = checked_path(os.getenv("XDG_STATE_HOME") or self.home / ".local/state")
        self.state = state / "bosh-to-the-basic"
        self.theme = checked_path(os.getenv("CONKY_TARGET") or config / "conky/bosh-to-the-basic")
        auto = checked_path(os.getenv("CONKY_AUTOSTART") or config / "autostart")
        roots = (self.theme, auto, self.state)
        for path in roots:
            if self.home not in path.parents or any(other in path.parents for other in roots):
                raise Refused("Los destinos deben estar separados y dentro de HOME")
        if len(set(roots)) != len(roots):
            raise Refused("Los destinos se solapan")
        project = SOURCE.parent
        if any(path == project or path in project.parents or project in path.parents for path in roots):
            raise Refused("Un destino se solapa con el repositorio")
        self.identity = [str(path.relative_to(self.home)) for path in roots]
        self.paths = {name: self.theme / name for name in FILES}
        self.paths.update({DESKTOP: auto / "conky.desktop", LEGACY: auto / "conky-bosh-to-the-basic.desktop"})
        self.manifest = self.state / "manifest.json"
        self.journal = self.state / "transaction.json"

    def expected(self):
        conky = shutil.which("conky")
        distro = platform.freedesktop_os_release().get("ID", "linux")
        packages = {"arch": "conky, cairo, noto-fonts", "endeavouros": "conky, cairo, noto-fonts",
                    "fedora": "conky, cairo, google-noto-sans-fonts"}
        print(f"Preflight {distro}. Requiere Python 3, Conky con Lua/Cairo, X11/Xwayland y Noto Sans.")
        if not conky:
            raise Refused("Falta Conky. Dependencias: " + packages.get(distro, "conky, cairo, Noto Sans"))
        probe = subprocess.run([conky, "-v"], capture_output=True, timeout=5, check=True,
                               text=True, errors="replace", env=dict(os.environ, LC_ALL="C"))
        features = (probe.stdout + probe.stderr).lower()
        if not all(feature in features for feature in ("lua", "cairo", "x11")):
            raise Refused("La compilación de Conky necesita Lua, Cairo y X11")
        try:
            modern_backend = detect_output_backend(conky)
        except (OSError, subprocess.SubprocessError, RuntimeError) as error:
            raise Refused(f"No se pudo verificar el backend X11 de Conky: {error}") from error
        if not shutil.which("flock"):
            raise Refused("Falta flock (util-linux) para evitar el doble arranque")
        payload = {}
        for name in FILES:
            path = SOURCE / name
            if path.resolve(strict=True) != path or not path.is_file():
                raise Refused(f"Recurso ausente o inseguro: {name}")
            data = path.read_bytes()
            if name == CONF:
                text = normalize_text(data.decode("utf-8"), str(self.theme), modern_backend)
                data = text.encode("utf-8")
            payload[name] = data, 0o755 if name.endswith(".sh") else 0o644
        entry = ('[Desktop Entry]\nType=Application\nName=Conky Bosh To The Basic\n'
                 f'Exec="{self.theme / START}"\nTerminal=false\nX-KDE-autostart-enabled=true\n')
        payload[DESKTOP] = entry.encode(), 0o644
        return payload

    def legacy(self, value):
        if value is None:
            return False
        # Exact signature of the v1 installer, including its target. Foreign
        # entries and customized commands require an explicit manual migration.
        pattern = (r'\[Desktop Entry\]\nType=Application\nName=Conky Bosh To The Basic\n'
                   r'Comment=Monitor del sistema\nExec=/bin/sh -c "sleep 8; /[\w./ +\-]*conky -c '
                   + re.escape(str(self.theme / CONF)) +
                   r' -d"\nTerminal=false\nX-KDE-autostart-enabled=true\n?')
        return re.fullmatch(pattern, value[0].decode(errors="replace")) is not None

    def validate(self, record):
        if not isinstance(record, dict) or record.get("version") != 1 or record.get("roots") != self.identity:
            raise Refused("Estado incompatible con los destinos")
        if not isinstance(record["files"], dict) or record["files"].keys() - self.paths.keys():
            raise Refused("Rutas desconocidas en el estado")
        for row in record["files"].values():
            unpack(row["original"])
            installed = row["installed"]
            if installed is not None and not re.fullmatch(r"[0-7]{1,3}:[0-9a-f]{64}", installed):
                raise Refused("Huella inválida en el estado")

    def record(self, files):
        return {"version": 1, "roots": self.identity, "files": files, "id": secrets.token_hex(16)}

    def recover(self, journal, manifest):
        self.validate(journal)
        if not manifest or journal["id"] != manifest["id"]:
            # Check every current value before attempting a partial rollback.
            undo = []
            for key, row in journal["files"].items():
                before = unpack(row["original"])
                now = snapshot(self.home, self.paths[key])
                if now != before:
                    if digest(now) != row["installed"]:
                        raise Refused("Recuperación detenida por edición concurrente: " + key)
                    undo.append((self.paths[key], before))
            for path, before in reversed(undo):
                write_file(self.home, path, before)
        write_file(self.home, self.journal, None)

    def run(self, action, dry, verify):
        with directory(self.home, self.home) as lock:
            # A pinned, per-user inode, including the first install before state exists.
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.process(action, dry, verify)

    def process(self, action, dry, verify):
        try:
            with directory(self.home, self.state) as fd:
                real_dir(fd, private=True)
        except FileNotFoundError:
            pass
        manifest = load_json(self.home, self.manifest)
        if manifest is not None:
            self.validate(manifest)
            if manifest.get("active") is not bool(manifest["files"]):
                raise Refused("Estado de instalación incoherente")
            if manifest["files"] and (set(FILES) | {DESKTOP}) - manifest["files"].keys():
                raise Refused("Faltan archivos obligatorios en el manifiesto")
        journal = load_json(self.home, self.journal)
        if journal is not None:
            if dry or verify:
                raise Refused("Transacción pendiente. Repita la operación normal para recuperarla.")
            self.recover(journal, manifest)
        rows = manifest["files"] if manifest else {}
        current = {key: snapshot(self.home, self.paths[key]) for key in rows}
        if verify:
            if not rows or any(digest(current[k]) != row["installed"] for k, row in rows.items()):
                raise Refused("Instalación ausente, incompleta o modificada")
            print("Integridad verificada.")
            return
        next_rows, desired, edits = {}, {}, {}
        if action == "install":
            payload = self.expected()
            for key in (*payload, LEGACY):
                if key not in current:
                    current[key] = snapshot(self.home, self.paths[key])
            for key, row in rows.items():
                if digest(current[key]) != row["installed"]:
                    raise Refused("Archivo administrado cambiado o ausente: " + key)
            for key in (DESKTOP, LEGACY):
                if current[key] is not None and key not in rows and not self.legacy(current[key]):
                    raise Refused("Autostart existente no reconocido: " + key)
            if current[LEGACY] is not None or LEGACY in rows:
                payload[LEGACY] = None
            for key, value in payload.items():
                original = rows[key]["original"] if key in rows else pack(current[key])
                next_rows[key] = {"original": original, "installed": digest(value)}
                desired[key] = value
        else:
            for key, row in rows.items():
                if digest(current[key]) != row["installed"]:
                    if current[key] is None:
                        print("Se conserva la eliminación local:", key)
                        continue
                    if row["original"] is None:
                        print("Se conserva el cambio local:", key)
                        continue
                    edits[key] = pack(current[key])
                    print("Edición guardada en el respaldo privado:", key)
                desired[key] = unpack(row["original"])

        changes = {k: v for k, v in desired.items() if current[k] != v}
        if changes or rows != next_rows:
            for parent in {self.paths[k].parent for k in changes} | {self.state}:
                check_writable(self.home, parent)
        if dry or (not changes and rows == next_rows):
            print(f"{len(changes)} cambios previstos." if dry else "Sin cambios.")
            return
        record = self.record(next_rows)
        record["active"] = bool(next_rows)
        serialized = state_json(record)
        journal = self.record({k: {"original": pack(current[k]), "installed": digest(v)}
                               for k, v in changes.items()})
        journal["id"] = record["id"]
        if action == "uninstall" and manifest:
            archive = self.state / ("backup-" + secrets.token_hex(12) + ".json")
            write_file(self.home, archive, state_json(dict(manifest, edits=edits)))
        write_file(self.home, self.journal, state_json(journal))
        try:
            for key, value in changes.items():
                path = self.paths[key]
                if snapshot(self.home, path) != current[key]:
                    raise Refused("Cambio concurrente: " + key)
                write_file(self.home, path, value)
                if snapshot(self.home, path) != value:
                    raise Refused("Falló la verificación de escritura: " + key)
            write_file(self.home, self.manifest, serialized)
        except BaseException:
            self.recover(journal, load_json(self.home, self.manifest))
            raise
        write_file(self.home, self.journal, None)
        print(f"Operación completada. {len(changes)} archivos. Estado privado en {self.state}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if os.getuid() == 0 or os.getuid() != os.geteuid():
        parser.exit(1, "Se requiere una sesión de usuario sin privilegios.\n")
    os.umask(0o077)
    try:
        Installation().run(args.action, args.dry_run, args.verify)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"Bosh: {exc}\n")


if __name__ == "__main__":
    main()
