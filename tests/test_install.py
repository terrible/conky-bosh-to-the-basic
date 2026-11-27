import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONF = "bosh-to-the-basic.conf"


class InstallTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="bosh install ")
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.config = self.home / "custom config"
        self.theme = self.config / "conky/bosh-to-the-basic"
        self.auto = self.config / "autostart"
        self.state = self.home / "state/bosh-to-the-basic"
        self.bin = self.home / "bin"
        self.bin.mkdir()
        conky = self.bin / "conky"
        conky.write_text("#!/bin/sh\nif [ \"$1\" = -c ]; then printf 'backend-probe\\n'; "
                         "else printf 'conky 1.25.0\\nLua bindings: Cairo\\nX11:\\n'; fi\n")
        conky.chmod(0o700)
        self.env = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.config),
                        CONKY_TARGET=str(self.theme), CONKY_AUTOSTART=str(self.auto),
                        XDG_STATE_HOME=str(self.state.parent), PATH=f"{self.bin}:/usr/bin:/bin",
                        PYTHONDONTWRITEBYTECODE="1")

    def cli(self, *args, name="install", ok=True):
        run = subprocess.run(["bash", str(ROOT / (name + ".sh")), *args], env=self.env,
                             capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode == 0, ok, run.stdout + run.stderr)
        return run

    def test_dry_run_then_idempotent_install(self):
        self.cli("--dry-run")
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.parent.exists())
        self.cli()
        config = self.theme / CONF
        self.assertNotIn("@CONKY_DIR@", config.read_text())
        self.assertIn(str(self.theme), config.read_text())
        self.assertIn("output_backend = 'x11'", config.read_text())
        desktop = (self.auto / "conky.desktop").read_text()
        self.assertNotIn("sh -c", desktop)
        before = [p.stat().st_mtime_ns for p in (config, self.state / "manifest.json")]
        self.cli()
        self.cli("--verify")
        self.assertEqual(before, [p.stat().st_mtime_ns for p in (config, self.state / "manifest.json")])
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)

    def test_legacy_conky_receives_out_to_x_not_modern_key(self):
        (self.bin / "conky").write_text(
            "#!/bin/sh\nif [ \"$1\" = -v ]; then echo 'Conky Lua Cairo X11'; "
            "else printf 'backend-probe\\nUnknown setting \\\"output_backend\\\"\\n'; fi\n"
        )
        (self.bin / "conky").chmod(0o700)
        self.cli()
        config = (self.theme / CONF).read_text()
        self.assertIn("out_to_x = true", config)
        self.assertNotIn("output_backend", config)

    def test_legacy_migration_and_restore(self):
        self.auto.mkdir(parents=True)
        self.theme.mkdir(parents=True)
        old = self.auto / "conky-bosh-to-the-basic.desktop"
        content = ('[Desktop Entry]\nType=Application\nName=Conky Bosh To The Basic\n'
                   f'Comment=Monitor del sistema\nExec=/bin/sh -c "sleep 8; /usr/bin/conky -c {self.theme}/{CONF} -d"\n'
                   'Terminal=false\nX-KDE-autostart-enabled=true\n')
        old.write_text(content)
        config = self.theme / CONF
        config.write_text("prior version")
        self.cli()
        self.assertFalse(old.exists())
        self.cli(name="uninstall")
        self.assertEqual(old.read_text(), content)
        self.assertEqual(config.read_text(), "prior version")
        self.assertFalse((self.auto / "conky.desktop").exists())

    def test_uninstall_preserves_user_changes(self):
        self.cli()
        (self.theme / CONF).write_text("local change")
        custom = self.theme / "mine.txt"
        custom.write_text("mine")
        self.cli("--verify", ok=False)
        self.cli(ok=False)
        self.cli("--dry-run", name="uninstall")
        self.assertTrue((self.auto / "conky.desktop").exists())
        self.cli(name="uninstall")
        self.assertEqual((self.theme / CONF).read_text(), "local change")
        self.assertEqual(custom.read_text(), "mine")
        self.assertFalse((self.theme / "scripts/network-info.sh").exists())
        self.cli(name="uninstall")

    def test_foreign_autostart_preserved(self):
        self.auto.mkdir(parents=True)
        foreign = self.auto / "conky.desktop"
        foreign.write_text("[Desktop Entry]\nName=Personal Conky\n")
        self.cli(ok=False)
        self.assertIn("Personal", foreign.read_text())
        self.assertFalse(self.theme.exists())

    def test_symlink_or_invalid_target_refused(self):
        self.config.symlink_to(self.bin, target_is_directory=True)
        self.cli(ok=False)
        self.assertFalse((self.bin / "autostart").exists())
        self.config.unlink()
        for value in ("../relative", "/", str(self.home), str(self.home / 'bad$dir')):
            with self.subTest(value=value):
                self.env["CONKY_TARGET"] = value
                self.cli(ok=False)

    def test_missing_outputs_and_permissions(self):
        self.cli()
        (self.theme / "scripts/network-info.sh").unlink()
        self.cli("--verify", ok=False)
        self.cli(name="uninstall")
        self.auto.chmod(0o500)
        self.addCleanup(self.auto.chmod, 0o700)
        if os.geteuid() != 0:
            self.cli(ok=False)
            self.assertFalse((self.theme / CONF).exists())

    def test_tampered_manifest_cannot_select_other_file(self):
        self.cli()
        path = self.state / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["files"]["../../outside"] = None
        path.write_text(json.dumps(manifest))
        self.cli(name="uninstall", ok=False)
        self.assertTrue((self.theme / CONF).exists())

    def test_manifest_missing_required_row(self):
        self.cli()
        path = self.state / "manifest.json"
        manifest = json.loads(path.read_text())
        del manifest["files"]["scripts/network-info.sh"]
        path.write_text(json.dumps(manifest))
        self.cli("--verify", ok=False)

    def test_restore_predecessor_and_save_edited_content(self):
        import base64
        self.theme.mkdir(parents=True)
        config = self.theme / CONF
        config.write_text("old")
        self.cli()
        config.write_text("user edits")
        self.cli(name="uninstall")
        self.assertEqual(config.read_text(), "old")
        archive = json.loads(next(self.state.glob("backup-*.json")).read_text())
        self.assertEqual(base64.b64decode(archive["edits"][CONF]["data"]), b"user edits")

    def test_partial_failure_rolls_back(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bosh_install", ROOT / "installer/manage.py")
        manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manager)
        self.theme.mkdir(parents=True)
        config = self.theme / CONF
        config.write_text("old version")
        original_write = manager.write_file

        def fail_once(home, path, value):
            if path == self.auto / "conky.desktop":
                raise PermissionError("injected write failure")
            original_write(home, path, value)

        with patch.dict(os.environ, self.env), patch.object(manager, "write_file", fail_once):
            with self.assertRaises(PermissionError):
                manager.Installation().run("install", False, False)
        self.assertEqual(config.read_text(), "old version")
        self.assertFalse((self.state / "manifest.json").exists())
        self.assertFalse((self.state / "transaction.json").exists())
        self.assertFalse((self.theme / "scripts/network-info.sh").exists())

    def test_private_home_lock_prevents_concurrent_install(self):
        import fcntl
        lock = os.open(self.home, os.O_RDONLY)
        self.addCleanup(os.close, lock)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.cli(ok=False)
        self.assertFalse(self.state.exists())

    def test_canonical_legacy_migration(self):
        self.auto.mkdir(parents=True)
        canonical = self.auto / "conky.desktop"
        old = ('[Desktop Entry]\nType=Application\nName=Conky Bosh To The Basic\n'
               f'Comment=Monitor del sistema\nExec=/bin/sh -c "sleep 8; /usr/bin/conky -c {self.theme}/{CONF} -d"\n'
               'Terminal=false\nX-KDE-autostart-enabled=true\n')
        canonical.write_text(old)
        self.cli()
        self.assertNotIn("sh -c", canonical.read_text())
        self.cli(name="uninstall")
        self.assertEqual(old, canonical.read_text())

    def test_launcher_single_instance(self):
        import fcntl
        self.cli()
        sleep = self.bin / "sleep"
        sleep.write_text("#!/bin/sh\nexit 0\n")
        sleep.chmod(0o755)
        marker = self.home / "called"
        (self.bin / "conky").write_text('#!/bin/sh\n: > "$HOME/called"\n')
        lock = os.open(self.theme, os.O_RDONLY)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            subprocess.run([self.theme / "startup/bosh-to-the-basic-startup.sh"],
                           env=self.env, check=True, timeout=3)
            self.assertFalse(marker.exists())
        finally:
            os.close(lock)
        subprocess.run([self.theme / "startup/bosh-to-the-basic-startup.sh"],
                       env=self.env, check=True, timeout=3)
        self.assertTrue(marker.is_file())

    def test_dry_run_detects_unwritable_destination(self):
        self.auto.mkdir(parents=True, mode=0o500)
        self.addCleanup(self.auto.chmod, 0o700)
        self.cli("--dry-run", ok=False)

    def test_source_cache_never_installed(self):
        # Use a disposable copy to exercise the actual packaging boundary.
        with tempfile.TemporaryDirectory(dir=self.home) as temp:
            repo = Path(temp) / "repo"
            shutil.copytree(ROOT / "bosh-to-the-basic", repo / "bosh-to-the-basic")
            shutil.copytree(ROOT / "installer", repo / "installer")
            shutil.copy2(ROOT / "install.sh", repo / "install.sh")
            junk = repo / "bosh-to-the-basic/scripts/mine.backup"
            junk.write_text("synthetic")
            subprocess.run(["bash", repo / "install.sh"], env=self.env, check=True,
                           stdout=subprocess.PIPE, timeout=5)
        self.assertFalse((self.theme / "scripts/mine.backup").exists())

    def test_deleted_user_preference_preserved(self):
        self.theme.mkdir(parents=True)
        (self.theme / CONF).write_text("old")
        self.cli()
        (self.theme / CONF).unlink()
        self.cli(name="uninstall")
        self.assertFalse((self.theme / CONF).exists())
        archive = json.loads(next(self.state.glob("backup-*.json")).read_text())
        self.assertIsNotNone(archive["files"][CONF]["original"])

    def test_refuse_state_larger_than_reader_limit(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bosh_install", ROOT / "installer/manage.py")
        manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manager)
        with patch.object(manager, "STATE_LIMIT", 40, create=True):
            with self.assertRaises(ValueError):
                manager.state_json({"archive": "x" * 40})

    def test_interrupted_first_install_recovers(self):
        self.theme.mkdir(parents=True)
        old = self.theme / CONF
        old.write_text("old version")
        code = """
import os, sys
sys.path.insert(0, sys.argv[1])
import manage
orig = manage.write_file
def write(home, path, value):
    orig(home, path, value)
    if path.name == manage.CONF:
        os._exit(23)
manage.write_file = write
manage.Installation().run('install', False, False)
"""
        proc = subprocess.run([os.sys.executable, "-B", "-c", code, ROOT / "installer"],
                              env=self.env, capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 23, proc.stderr)
        self.assertTrue((self.state / "transaction.json").is_file())
        self.cli("--dry-run", ok=False)
        self.cli(name="uninstall")
        self.assertEqual(old.read_text(), "old version")
        self.assertFalse((self.state / "transaction.json").exists())
