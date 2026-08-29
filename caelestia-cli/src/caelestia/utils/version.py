import os
import shutil
import subprocess
import sys
from pathlib import Path

from caelestia.utils.dots.legacy import LEGACY_META_PKG, detect_legacy_repo
from caelestia.utils.dots.packages import ArchInstaller
from caelestia.utils.dots.source import DotsSource, SourceError
from caelestia.utils.dots.state import DotsState
from caelestia.utils.paths import config_dir

PKGS = ("caelestia-shell", "caelestia-cli", "quickshell")
INDENT = "    "


def _header(text: str, suffix: str = "") -> None:
    suffix = f" {suffix}" if suffix else ""
    if sys.stdout.isatty():
        print(f"\033[1;36m{text}\033[0m{suffix}")
    else:
        print(f"{text}{suffix}")


def _rows(pairs: list[tuple[str, str]], align: bool = False) -> None:
    dim = sys.stdout.isatty()
    width = max((len(key) for key, _ in pairs), default=0) if align else 0
    for key, value in pairs:
        if dim:
            value = f"\033[2m{value}\033[0m"
        label = key.ljust(width) if align else f"{key}:"
        print(f"{INDENT}{label}  {value}" if align else f"{INDENT}{label} {value}")


def _commit(commit: str, message: str) -> str:
    sha = commit[:7]
    subject = message.splitlines()[0] if message else ""
    return f"{sha} ({subject})" if subject else sha


def _commit_from_meta(meta: tuple[str, str] | None) -> str:
    if meta:
        commit, message = meta
        return _commit(commit, message)
    return "unknown"


def fetch_git_metadata(repo_dir: Path, branch: str = "upstream/main") -> tuple[str, str] | None:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(repo_dir), "show", "-s", "--format=%H%x00%s", branch],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    commit, separator, message = output.rstrip("\n").partition("\0")
    return (commit, message) if separator else None


def print_packages() -> tuple[str, str] | None:
    if shutil.which("pacman"):
        _header("Packages (Arch):")
        installer = ArchInstaller("")
        installed = [(pkg, installer.query(pkg)) for pkg in PKGS]
        missing = [(pkg, "not installed") for pkg, result in installed if result is None]
        present = [result for _, result in installed if result is not None]
        _rows(missing + present, align=True)
        return installer.query(LEGACY_META_PKG)
    else:
        _header("Ecosystem Components:")
        components = [
            ("Hyprland", "Hyprland"),
            ("Quickshell", "qs"),
            ("Caelestia CLI", "caelestia"),
            ("Audio CAVA", "cava"),
            ("Foot Terminal", "foot"),
            ("Fish Shell", "fish"),
        ]
        results = []
        for name, bin_cmd in components:
            p = shutil.which(bin_cmd)
            status = f"active ({p})" if p else "not installed"
            results.append((name, status))
        _rows(results, align=True)
        return None


def print_legacy_install(meta_package: tuple[str, str] | None) -> None:
    legacy_path = detect_legacy_repo()
    if legacy_path is None and meta_package is None:
        return

    print()
    _header("Legacy install detected:")
    meta_row = (LEGACY_META_PKG, "not installed") if meta_package is None else meta_package
    _rows([("Legacy dots path", str(legacy_path or "not found")), meta_row])


def print_dots_version() -> None:
    state = DotsState.load()
    if state.applied_rev is None:
        _header("Dots:", "Caelestia Debian / Hybrid Port")
        return

    _header("Dots:")
    source = DotsSource()
    try:
        message = source.commit_message_at(state.applied_rev)
    except (SourceError, FileNotFoundError):
        message = ""
    components = ", ".join(state.enabled_components) or "none"
    _rows(
        [
            ("Commit", _commit(state.applied_rev, message)),
            ("Components", components),
            ("AUR helper", state.aur_helper if shutil.which("pacman") else "Debian APT"),
        ]
    )


def print_version() -> None:
    meta_package = print_packages()
    print_legacy_install(meta_package)

    print()
    print_dots_version()

    print()
    try:
        if os.path.exists("/usr/lib/caelestia/version"):
            shell_ver = subprocess.check_output(["/usr/lib/caelestia/version", "-s"], text=True).strip()
        elif os.path.exists("/etc/xdg/quickshell/caelestia/shell.qml"):
            shell_ver = "Caelestia Shell (Quickshell QML 0.3.1+)"
        else:
            shell_ver = "installed"
        _header("Shell:")
        print(f"{INDENT}{shell_ver}")
    except Exception:
        _header("Shell:", "active")

    print()
    if shutil.which("qs"):
        try:
            qs_ver = subprocess.check_output(["qs", "--version"], text=True).strip()
            _header("Quickshell:")
            print(f"{INDENT}{qs_ver}")
        except Exception:
            _header("Quickshell:", "installed")
    else:
        _header("Quickshell:", "not in PATH")

    local_shell_dir = config_dir / "quickshell/caelestia"
    if local_shell_dir.exists():
        print()
        _header("Local Shell Configuration:")
        upstream_metadata = fetch_git_metadata(local_shell_dir)
        local_metadata = fetch_git_metadata(local_shell_dir, "HEAD")
        _rows(
            [
                ("Status", "loaded from /etc/xdg/quickshell/caelestia"),
            ]
        )
