import shutil
from pathlib import Path
import sys
import subprocess

# CONFIGRATIONS
CONFIG_DIR=Path.home()/'.vid-download'
MARKER_FILE=CONFIG_DIR/'setup_complete'
CONFIG_DIR.mkdir(exist_ok=True,parents=True)
IS_WINDOWS=sys.platform=='win32'

# Install Commands
_INSTALL_CMD={'WIN':'irm https://deno.land/install.ps1 | iex',
              'MAC/LIN':'curl -fsSL https://deno.land/install.sh | sh'}

def ensure_env_ready() -> None:
    "Ensures DENO runtime is installed before going to the cli APP"

    if MARKER_FILE.exists(): return

    if not shutil.which('deno'):
        ans=input("DENO runtime is not installed. Install now ? [Y/n]: ").strip().lower()
        if ans not in ('Y','y','','1'):
            print('Skipping the Install\nYou can install DENO manually if you dont like auto install')
            raise SystemExit(1)
        _install_deno()

    _sanity_check()

    MARKER_FILE.write_text("Ready")

def _install_deno() ->None:
    "Installs Deno JS Runtime for Yt-dlp"
    print("Installing Deno Runtime ...")
    if not IS_WINDOWS:
        result=subprocess.run(_INSTALL_CMD['MAC/LIN'],shell=True)
    else:
        result=subprocess.run(['powershell','-NoProfile','-Command',_INSTALL_CMD['WIN']])

    if result.returncode!=0:
        print("DENO INSTALL FAILED. Try running the command manually then re-run this command")
        raise SystemExit(1)

def _sanity_check() -> None:
    "Confirms if Deno is successfully runs and not just in path"
    try:
        result=subprocess.run(['deno','--version'],capture_output=True,text=True)

    except FileNotFoundError:
        print("Deno was installed but isn't on PATH yet. Try restarting your terminal and re-running.")
        raise SystemExit(1)

    if result.returncode!=0:
        print(f'DENO found but failed to run:\n{result.stderr}')
        raise SystemExit(1)


