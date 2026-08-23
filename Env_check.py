import json
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / '.vid-download'
MARKER_FILE = CONFIG_DIR / 'setup_complete.json'
CONFIG_DIR.mkdir(exist_ok=True, parents=True)

IS_WINDOWS = sys.platform == 'win32'
IS_MAC = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')

_DENO_INSTALL_CMD = {
    'WIN': 'irm https://deno.land/install.ps1 | iex',
    'MAC/LIN': 'curl -fsSL https://deno.land/install.sh | sh',
}


def ensure_env_ready() -> None:
    """Ensures Deno and ffmpeg are both available before entering the CLI app.

    Tracks each tool's status independently in the marker file, so a partial
    setup (e.g. ffmpeg reinstalled/removed later) doesn't force a redundant
    Deno check, and vice versa.
    """
    status = _load_status()

    if not status.get('deno'):
        _ensure_deno()
        status['deno'] = True
        _save_status(status)

    if not status.get('ffmpeg'):
        _ensure_ffmpeg()
        status['ffmpeg'] = True
        _save_status(status)


def _load_status() -> dict:
    if MARKER_FILE.exists():
        try:
            return json.loads(MARKER_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_status(status: dict) -> None:
    MARKER_FILE.write_text(json.dumps(status))


def _ensure_deno() -> None:
    if shutil.which('deno'):
        _sanity_check(['deno', '--version'], "Deno")
        return

    ans = input("Deno runtime is not installed. Install now? [Y/n]: ").strip().lower()
    if ans not in ('', 'y', 'yes'):
        print("Skipping Deno install. Some sites may fail to download without it.")
        return

    print("Installing Deno runtime...")
    if IS_WINDOWS:
        result = subprocess.run(['powershell', '-NoProfile', '-Command', _DENO_INSTALL_CMD['WIN']])
    else:
        result = subprocess.run(_DENO_INSTALL_CMD['MAC/LIN'], shell=True)

    if result.returncode != 0:
        print("Deno install failed. Install it manually from https://deno.land, then re-run this tool.")
        raise SystemExit(1)

    _sanity_check(['deno', '--version'], "Deno", allow_path_miss=True)


# ---------------------------------------------------------------------------
# ffmpeg
# ---------------------------------------------------------------------------

def _ensure_ffmpeg() -> None:
    if shutil.which('ffmpeg'):
        _sanity_check(['ffmpeg', '-version'], "ffmpeg")
        return

    ans = input("ffmpeg is not installed (required for all downloads). Install now? [Y/n]: ").strip().lower()
    if ans not in ('', 'y', 'yes'):
        print("Skipping ffmpeg install. Downloads will fail without it.")
        return

    print("Installing ffmpeg...")
    installed = False

    if IS_WINDOWS:
        installed = _try_install(['winget', 'install', '--id=Gyan.FFmpeg', '-e',
                                   '--accept-source-agreements', '--accept-package-agreements'])
        if not installed and shutil.which('choco'):
            installed = _try_install(['choco', 'install', 'ffmpeg', '-y'])

    elif IS_MAC:
        if shutil.which('brew'):
            installed = _try_install(['brew', 'install', 'ffmpeg'])
        else:
            print(
                "Homebrew isn't installed, so ffmpeg can't be installed automatically.\n"
                "Install Homebrew from https://brew.sh and re-run this tool, "
                "or install ffmpeg directly from https://ffmpeg.org/download.html."
            )
            raise SystemExit(1)

    elif IS_LINUX:
        if shutil.which('apt-get'):
            installed = _try_install(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'])
        elif shutil.which('dnf'):
            installed = _try_install(['sudo', 'dnf', 'install', '-y', 'ffmpeg'])
        elif shutil.which('pacman'):
            installed = _try_install(['sudo', 'pacman', '-S', '--noconfirm', 'ffmpeg'])
        else:
            print(
                "No supported package manager found (apt/dnf/pacman) FIGURE IT OUT, Sherlock.\n"
                "Install ffmpeg on whatever distro you using this week then re-run this tool.\n"
                "On second thought why you need this tool you are LINUX user.\n"
                "Ya And if you are a Arch user just remember 'YOU USE ARCH BTW'.\n"
                "And if you are a KALI Linux user just stop man we know u aint a hacker :) ."
            )
            raise SystemExit(1)

    if not installed:
        print(
            "Automatic ffmpeg install didn't complete. Install it manually from "
            "https://ffmpeg.org/download.html, then re-run this tool."
        )
        raise SystemExit(1)

    _sanity_check(['ffmpeg', '-version'], "ffmpeg", allow_path_miss=True)


def _try_install(cmd) -> bool:
    try:
        result = subprocess.run(cmd)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _sanity_check(cmd, label, allow_path_miss=False) -> None:
    """Confirms a tool actually runs, not just that a which() lookup succeeded."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        if allow_path_miss:
            print(
                f"{label} was installed but isn't on PATH yet in this session. "
                "Restart your terminal and re-run this tool."
            )
            raise SystemExit(1)
        raise

    if result.returncode != 0:
        print(f"{label} found but failed to run:\n{result.stderr}")
        raise SystemExit(1)