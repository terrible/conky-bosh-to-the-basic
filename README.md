# Bosh To The Basic

[Español](README.es.md)

**A classic-style Conky system panel, adapted for modern Linux desktops.**

The v1.1.0 engineering candidate is frozen. It passed local and rootless Arch/Fedora-container test suites, isolated Xvfb checks, a physical benchmark, and a maintainer-reported visual inspection on KDE Plasma 6.8.3 Wayland/Xwayland/KWin. Public distribution remains blocked by unresolved upstream licensing.

## What it shows

- Clock, date, uptime, CPU total and up to four per-core bars.
- Memory, optional swap, root storage and top processes.
- Intel and NVIDIA GPU load, NVIDIA memory and available temperatures.
- Active network interface, address, transfer totals and separate traffic graphs.
- A 273 px configured panel using the frozen OPT-01 typography, spacing and blue/yellow palette.

Optional hardware sources degrade to `N/D` or are omitted where OPT-01 is conditional. NVIDIA uses `nvidia-smi`; the Intel collector is an optional repository resource and is not installed or enabled by the theme installer.

## Architecture

Conky renders the X11 configuration and Lua/Cairo text and graph helpers. Python reads one bounded hardware snapshot and renders the GPU and temperature rows. Small Bash helpers detect network and distribution information. The user-scoped Python installer manages the theme, autostart migration, private backups and rollback; the matching uninstaller preserves later user edits. Neither installs system packages or requires root.

## Compatibility evidence

| Environment | Evidence | Limit |
|---|---|---|
| EndeavourOS host | 90 automated tests; isolated Conky/Xvfb smoke and physical benchmark | Physical validation on the QA host; no claim for other hardware |
| Arch Linux | 90 tests in a rootless, network-disabled container | Not a full KDE desktop test |
| Fedora | 90 tests in a rootless, network-disabled container | Not a full KDE desktop test |
| X11/Xvfb | Isolated render and synthetic pixel comparison; explicit X11 backend | Xvfb has no compositor |
| KDE Plasma 6.8.3 Wayland/Xwayland/KWin | Maintainer-reported QA-21.4 inspection on a separate output confirmed transparency, position, design, fonts, colors, Intel bar, NVIDIA VRAM/load/decimal temperature, CPU, RAM, storage, network and processes | The temporary window used a distinct class; KWin rules for the installed/original class were not validated |
| Native Wayland backend | Not supported as the reference renderer | Do not switch from X11/Xwayland |

Conky needs Lua, Cairo and X11 support. Noto Sans is used by the panel. The target distributions are Arch Linux, EndeavourOS and Fedora KDE; container results establish software-test coverage only, not full desktop support.

## Performance evidence

On the QA-21.3 EndeavourOS test host (Intel Core i5-3330, GTX 1650), three alternating 60-second samples per variant produced median one-core CPU of **9.845% for OPT-01** and **4.310% for the candidate** (about 56% lower in this run). NVIDIA polling was 48 versus 12 queries per minute, with no failed queries. Both panels measured 283×893 during the physical runs. These are measurements from one host and the isolated Xvfb/cgroup protocol, not a promise for other systems. Full samples and methodology are in [the performance report](docs/PERFORMANCE.md); QA-19 results remain historical there.

The corrected synthetic Xvfb comparison measured 283×927 for both variants with ImageMagick AE=0; physical Xvfb smoke/benchmark geometry was 283×893 for both. Xvfb does not validate KWin composition or real Wayland transparency; QA-21.4 is a separate human-reported desktop inspection.

Conky emitted a font-initialization warning in the test logs. The maintainer reported no visible font defect in QA-21.4; the warning is documented and was not suppressed.

## Candidate evaluation

**Do not distribute or install this candidate for general use while its license gate is unresolved.** For authorized maintainer QA in a disposable HOME, the implemented interface is:

```sh
./install.sh --dry-run
./install.sh
./install.sh --verify
./uninstall.sh --dry-run
./uninstall.sh
```

The installer does not fetch dependencies. Install Conky and fonts using your distribution's package manager only when preparing a separate test environment. See [installation](docs/INSTALL.md), [recovery](docs/RECOVERY.md) and [security](SECURITY.md).

For development, run `make test`, `make audit`, `make doctor` and `make benchmark`. The benchmark Make target is synthetic; it does not measure physical panel CPU. GitHub Actions is prepared for tests and static checks, but no remote run or publication is claimed.

## Bosh Linux ecosystem

Bosh To The Basic, Bosh Terminal and the planned Bosh Desktop are separate, modular projects. This repository contains only the Conky panel and its installer, resources and QA tools.

## History and credits

This project revives a classic Conky appearance and adapts it for a modern Linux setup. The visual lineage is attributed to **Hybrid Back To Basic** by **Haidir (dirn)**, reference version 1.0.1: [upstream Bitbucket repository](https://bitbucket.org/dirn-typo/back-to-basic) and [GNOME-Look project page](https://www.gnome-look.org/p/1578329). The upstream README says the author of the earlier Conky configuration is unknown.

The upstream v1.0.1 tree reviewed for QA-19 contains no `LICENSE`, `COPYING` or copyright notice that establishes redistribution terms. A historical Bosh README's mention of GPLv3 does not prove the terms for the exact derived code. **No license is assigned here; public redistribution is blocked pending evidence and authorization.** See [the license inventory](docs/LICENSE-INVENTORY.md). No wallpaper or third-party preview image is included in this candidate.

The release gate requires a verifiable license/permission covering the v1.0.1-derived files, clarification or permission for the historically incorporated Conky configuration whose author is unknown, and licensing evidence for the five imported OPT-01 files. The maintainer must then choose a compatible license for original contributions and the combined distribution.
