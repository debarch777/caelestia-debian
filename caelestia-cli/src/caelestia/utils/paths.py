import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from caelestia.utils.io import warn

config_dir: Path = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
data_dir: Path = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
state_dir: Path = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local/state"))
cache_dir: Path = Path(os.getenv("XDG_CACHE_HOME", Path.home() / ".cache"))
pictures_dir: Path = Path(os.getenv("XDG_PICTURES_DIR", Path.home() / "Pictures"))
videos_dir: Path = Path(os.getenv("XDG_VIDEOS_DIR", Path.home() / "Videos"))

c_config_dir: Path = config_dir / "caelestia"
c_data_dir: Path = data_dir / "caelestia"
c_state_dir: Path = state_dir / "caelestia"
c_cache_dir: Path = cache_dir / "caelestia"

user_config_path: Path = c_config_dir / "cli.json"

# Robust resolution for package data
_pkg_data_dir = Path(__file__).parent.parent / "data"
_user_shared_data = data_dir / "caelestia/data"

if (_pkg_data_dir / "templates").exists():
    cli_data_dir: Path = _pkg_data_dir
elif (_user_shared_data / "templates").exists():
    cli_data_dir: Path = _user_shared_data
elif Path("/usr/local/share/caelestia/data").exists():
    cli_data_dir: Path = Path("/usr/local/share/caelestia/data")
elif Path("/usr/share/caelestia/data").exists():
    cli_data_dir: Path = Path("/usr/share/caelestia/data")
else:
    cli_data_dir: Path = _pkg_data_dir

templates_dir: Path = cli_data_dir / "templates"
user_templates_dir: Path = c_config_dir / "templates"
theme_dir: Path = c_state_dir / "theme"

config_backup_dir: Path = config_dir.parent / f"{config_dir.name}.bak"
dots_dir: Path = c_state_dir / "dots"
dots_state_path: Path = c_state_dir / "dots-state.json"

scheme_path: Path = c_state_dir / "scheme.json"
scheme_data_dir: Path = cli_data_dir / "schemes"
scheme_cache_dir: Path = c_cache_dir / "schemes"

wallpapers_dir: Path = Path(os.getenv("CAELESTIA_WALLPAPERS_DIR", pictures_dir / "Wallpapers"))
wallpaper_path_path: Path = c_state_dir / "wallpaper/path.txt"
wallpaper_link_path: Path = c_state_dir / "wallpaper/current"
wallpaper_thumbnail_path: Path = c_state_dir / "wallpaper/thumbnail.jpg"
wallpapers_cache_dir: Path = c_cache_dir / "wallpapers"

screenshots_dir: Path = Path(os.getenv("CAELESTIA_SCREENSHOTS_DIR", pictures_dir / "Screenshots"))
screenshots_cache_dir: Path = c_cache_dir / "screenshots"

recordings_dir: Path = Path(os.getenv("CAELESTIA_RECORDINGS_DIR", videos_dir / "Recordings"))
recording_path: Path = c_state_dir / "record/recording.mp4"
recording_notif_path: Path = c_state_dir / "record/notifid.txt"


def get_config() -> dict[str, Any]:
    if not user_config_path.exists():
        return {}

    with user_config_path.open() as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            warn(f"Failed to parse config file: {user_config_path}")
            return {}


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as f:
        f.write(content)
        temp_name = f.name
    os.replace(temp_name, path)


def atomic_dump(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False) as f:
        json.dump(obj, f, indent=2)
        temp_name = f.name
    os.replace(temp_name, path)


def compute_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()
