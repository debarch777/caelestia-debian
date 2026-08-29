import json
import os
import shlex
import shutil
import subprocess
from argparse import Namespace
from collections import ChainMap
from typing import Any, Callable, cast

from caelestia.utils import hypr
from caelestia.utils.paths import get_config


def is_subset(superset, subset):
    for key, value in subset.items():
        if key not in superset:
            return False

        if isinstance(value, dict):
            if not is_subset(superset[key], value):
                return False

        elif isinstance(value, str):
            if value.lower() not in str(superset[key]).lower():
                return False

        elif isinstance(value, list):
            if not set(value) <= set(superset[key]):
                return False
        elif isinstance(value, set):
            if not value <= superset[key]:
                return False

        else:
            if not value == superset[key]:
                return False

    return True


class DeepChainMap(ChainMap):
    def __getitem__(self, key):
        values = (mapping[key] for mapping in self.maps if key in mapping)
        try:
            first = next(values)
        except StopIteration:
            return self.__missing__(key)
        if isinstance(first, dict):
            return self.__class__(first, *values)
        return first

    def __repr__(self):
        return repr(dict(self))


def resolve_best_command(preferred_command: list[str], app_type: str) -> list[str]:
    """Dynamically resolve installed app command if preferred isn't available"""
    cmd0 = preferred_command[0] if preferred_command else ""
    if shutil.which(cmd0) or (cmd0.startswith("flatpak") and shutil.which("flatpak")):
        return preferred_command

    if app_type == "music":
        if shutil.which("spotify"):
            return ["spotify"]
        if shutil.which("flatpak") and subprocess.run(["flatpak", "info", "com.spotify.Client"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return ["flatpak", "run", "com.spotify.Client"]
        for alt in ["feishin", "plexamp", "cider"]:
            if shutil.which(alt):
                return [alt]

    elif app_type == "communication":
        for alt in ["discord", "vesktop", "legcord", "equibop", "webcord", "whatsapp"]:
            if shutil.which(alt):
                return [alt]
        if shutil.which("flatpak"):
            for fp in ["com.discordapp.Discord", "dev.vencord.Vesktop"]:
                if subprocess.run(["flatpak", "info", fp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                    return ["flatpak", "run", fp]

    elif app_type == "todo":
        if shutil.which("todoist"):
            return ["todoist"]
        if shutil.which("flatpak") and subprocess.run(["flatpak", "info", "com.todoist.Todoist"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return ["flatpak", "run", "com.todoist.Todoist"]

    return preferred_command


class Command:
    args: Namespace
    cfg: dict[str, dict[str, dict[str, Any]]] | DeepChainMap
    clients: list[dict[str, Any]] | None = None

    def __init__(self, args: Namespace) -> None:
        self.args = args

        self.cfg = {
            "communication": {
                "discord": {
                    "enable": True,
                    "match": [
                        {"class": "discord"},
                        {"class": "Discord"},
                        {"class": "vesktop"},
                        {"class": "equibop"},
                        {"class": "legcord"},
                        {"class": "WebCord"},
                        {"initialTitle": "Discord"},
                        {"class": "com.discordapp.Discord"},
                        {"class": "dev.vencord.Vesktop"},
                    ],
                    "command": ["discord"],
                    "move": True,
                    "type": "communication",
                },
                "whatsapp": {
                    "enable": True,
                    "match": [{"class": "whatsapp"}, {"class": "WhatsApp"}, {"class": "whatsapp-for-linux"}],
                    "command": ["whatsapp"],
                    "move": True,
                    "type": "communication",
                },
            },
            "music": {
                "spotify": {
                    "enable": True,
                    "match": [
                        {"class": "Spotify"},
                        {"class": "spotify"},
                        {"initialTitle": "Spotify"},
                        {"initialTitle": "Spotify Free"},
                        {"initialClass": "Spotify"},
                        {"class": "com.spotify.Client"},
                    ],
                    "command": ["spotify"],
                    "move": True,
                    "type": "music",
                },
                "feishin": {
                    "enable": True,
                    "match": [{"class": "feishin"}],
                    "move": True,
                    "type": "music",
                },
            },
            "sysmon": {
                "btop": {
                    "enable": True,
                    "match": [{"class": "btop", "title": "btop", "workspace": {"name": "special:sysmon"}}],
                    "command": ["foot", "-a", "btop", "-T", "btop", "fish", "-C", "exec btop"],
                    "type": "sysmon",
                },
            },
            "todo": {
                "todoist": {
                    "enable": True,
                    "match": [{"class": "Todoist"}, {"class": "todoist"}, {"class": "com.todoist.Todoist"}],
                    "command": ["todoist"],
                    "move": True,
                    "type": "todo",
                },
            },
        }
        try:
            self.cfg = DeepChainMap(get_config().get("toggles", {}), self.cfg)
        except Exception:
            pass

    def run(self) -> None:
        if self.args.workspace == "specialws":
            self.specialws()
            return

        spawned = False
        if self.args.workspace in self.cfg:
            for client in self.cfg[self.args.workspace].values():
                if "enable" in client and client.get("enable") and self.handle_client_config(client):
                    spawned = True

        monitors = cast(list[dict[str, Any]], hypr.message("monitors"))
        focused = next((m for m in monitors if m.get("focused")), None)
        active_special = focused.get("specialWorkspace", {}).get("name", "") if focused else ""

        # If app was just spawned and special workspace isn't open, open it immediately
        if spawned:
            if active_special != f"special:{self.args.workspace}":
                hypr.dispatch("togglespecialworkspace", self.args.workspace)
        else:
            hypr.dispatch("togglespecialworkspace", self.args.workspace)

    def get_clients(self) -> list[dict[str, Any]]:
        if self.clients is None:
            self.clients = cast(list[dict[str, Any]], hypr.message("clients"))
        return self.clients

    def move_client(self, selector: Callable, workspace: str) -> None:
        for client in self.get_clients():
            if selector(client) and client.get("workspace", {}).get("name") != f"special:{workspace}":
                hypr.dispatch("movetoworkspacesilent", f"special:{workspace},address:{client['address']}")

    def spawn_client(self, selector: Callable, spawn: list[str], app_type: str = "") -> bool:
        resolved_spawn = resolve_best_command(spawn, app_type)
        if not any(selector(client) for client in self.get_clients()):
            hypr.dispatch("exec", f"[workspace special:{self.args.workspace}] {shlex.join(resolved_spawn)}")
            return True
        return False

    def handle_client_config(self, client: dict[str, Any]) -> bool:
        def selector(c: dict[str, Any]) -> bool:
            for match in client.get("match", []):
                if is_subset(c, match):
                    return True
            return False

        spawned = False
        if "command" in client and client["command"]:
            spawned = self.spawn_client(selector, client["command"], client.get("type", self.args.workspace))
        if "move" in client and client.get("move"):
            self.move_client(selector, self.args.workspace)

        return spawned

    def specialws(self) -> None:
        monitors = cast(list[dict[str, Any]], hypr.message("monitors"))
        target = next((m for m in monitors if m.get("focused")), None)
        if target:
            special = target.get("specialWorkspace", {}).get("name", "")[8:] or "special"
            hypr.dispatch("togglespecialworkspace", special)
