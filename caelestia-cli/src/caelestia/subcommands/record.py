import os
import re
import shutil
import subprocess
import time
from argparse import Namespace
from datetime import datetime
from pathlib import Path

from caelestia.utils import hypr
from caelestia.utils.notify import close_notification, notify
from caelestia.utils.paths import get_config, recording_notif_path, recording_path, recordings_dir

SUPPORTED_RECORDERS = ["gpu-screen-recorder", "wf-recorder", "wl-screenrec"]


def get_available_recorder() -> str:
    """Detect available Wayland screen recording tool"""
    for rec in SUPPORTED_RECORDERS:
        if shutil.which(rec):
            return rec
    return "wf-recorder"


class Command:
    args: Namespace

    def __init__(self, args: Namespace) -> None:
        self.args = args

    def get_active_recorder(self) -> str | None:
        for rec in SUPPORTED_RECORDERS:
            p = subprocess.run(["pgrep", "-f", rec], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if p.returncode == 0:
                return rec
        return None

    def proc_running(self) -> bool:
        return self.get_active_recorder() is not None

    def run(self) -> None:
        if self.args.pause:
            rec = self.get_active_recorder() or get_available_recorder()
            if rec == "gpu-screen-recorder":
                subprocess.run(["pkill", "-USR2", "-f", "gpu-screen-recorder"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-STOP", "-f", rec], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif self.proc_running():
            self.stop()
        else:
            self.start()

    def intersects(self, a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
        return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]

    def start(self) -> None:
        recorder = get_available_recorder()
        if not shutil.which(recorder):
            notify("-u", "critical", "Recording failed", "No Wayland screen recorder found. Please install wf-recorder or gpu-screen-recorder.")
            return

        monitors = hypr.message("monitors")
        cmd = [recorder]

        if recorder == "gpu-screen-recorder":
            args = ["-w"]
            if self.args.region:
                if self.args.region == "slurp":
                    region = subprocess.check_output(["slurp", "-f", "%wx%h+%x+%y"], text=True).strip()
                else:
                    region = self.args.region.strip()
                args += ["region", "-region", region]

                m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", region)
                if not m:
                    raise ValueError(f"Invalid region: {region}")

                w, h, x, y = map(int, m.groups())
                r = x, y, w, h
                max_rr = 0
                for monitor in monitors:
                    if self.intersects((monitor["x"], monitor["y"], monitor["width"], monitor["height"]), r):
                        rr = round(monitor["refreshRate"])
                        max_rr = max(max_rr, rr)
                args += ["-f", str(max(30, max_rr))]
            else:
                focused_monitor = next((m for m in monitors if m.get("focused")), monitors[0] if monitors else None)
                if focused_monitor:
                    args += [focused_monitor["name"], "-f", str(round(focused_monitor.get("refreshRate", 60)))]

            if self.args.sound:
                args += ["-a", "default_output"]

            args += ["-o", str(recording_path)]
            cmd += args

        elif recorder == "wf-recorder":
            args = ["-f", str(recording_path)]
            if self.args.region:
                if self.args.region == "slurp":
                    region = subprocess.check_output(["slurp", "-f", "%x,%y %wx%h"], text=True).strip()
                else:
                    region = self.args.region.strip()
                args += ["-g", region]
            else:
                focused_monitor = next((m for m in monitors if m.get("focused")), monitors[0] if monitors else None)
                if focused_monitor:
                    args += ["-o", focused_monitor["name"]]

            if self.args.sound:
                args += ["-a"]

            cmd += args

        elif recorder == "wl-screenrec":
            args = ["-f", str(recording_path)]
            if self.args.region:
                if self.args.region == "slurp":
                    region = subprocess.check_output(["slurp", "-f", "%x,%y %wx%h"], text=True).strip()
                else:
                    region = self.args.region.strip()
                args += ["-g", region]
            else:
                focused_monitor = next((m for m in monitors if m.get("focused")), monitors[0] if monitors else None)
                if focused_monitor:
                    args += ["-o", focused_monitor["name"]]

            if self.args.sound:
                args += ["--audio"]

            cmd += args

        config = get_config()
        try:
            if "record" in config and "extraArgs" in config["record"]:
                cmd += config["record"]["extraArgs"]
        except TypeError as e:
            raise ValueError(f"Config option 'record.extraArgs' should be an array: {e}")

        recording_path.parent.mkdir(parents=True, exist_ok=True)
        # Remove old recording if exists
        if recording_path.exists():
            recording_path.unlink()

        proc = subprocess.Popen(cmd, start_new_session=True)

        notif = notify("-p", "Recording started", f"Recording using {recorder}...")
        recording_notif_path.write_text(notif)

        try:
            if proc.wait(0.8) != 0:
                close_notification(notif)
                notify(
                    "Recording failed",
                    "An error occurred attempting to start recorder. "
                    f"Command `{' '.join(proc.args)}` failed with exit code {proc.returncode}",
                )
        except subprocess.TimeoutExpired:
            pass

    def stop(self) -> None:
        rec = self.get_active_recorder() or get_available_recorder()

        # Send SIGINT so video encoders cleanly finalize mp4 index
        subprocess.run(["pkill", "-INT", "-f", rec], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Wait for process to cleanly write container headers
        for _ in range(30):
            if not self.proc_running():
                break
            time.sleep(0.1)

        if self.proc_running():
            subprocess.run(["pkill", "-9", "-f", rec], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Close start notification
        try:
            close_notification(recording_notif_path.read_text())
        except IOError:
            pass

        time.sleep(0.2)
        if not recording_path.exists() or recording_path.stat().st_size == 0:
            notify("Recording cancelled", "No recording was saved.")
            return

        # Move to recordings folder
        new_path = recordings_dir / f"recording_{datetime.now().strftime('%Y%m%d_%H-%M-%S')}.mp4"
        recordings_dir.mkdir(exist_ok=True, parents=True)
        shutil.move(recording_path, new_path)

        if self.args.clipboard:
            file_uri = Path(new_path).resolve().as_uri() + "\n"
            subprocess.run(["wl-copy", "--type", "text/uri-list"], input=file_uri.encode())

        action = notify(
            "--action=watch=Watch",
            "--action=open=Open",
            "--action=delete=Delete",
            "Recording stopped",
            f"Recording saved in {new_path}",
        )

        if action == "watch":
            subprocess.Popen(["xdg-open", str(new_path)], start_new_session=True)
        elif action == "open":
            p = subprocess.run(
                [
                    "dbus-send",
                    "--session",
                    "--dest=org.freedesktop.FileManager1",
                    "--type=method_call",
                    "/org/freedesktop/FileManager1",
                    "org.freedesktop.FileManager1.ShowItems",
                    f"array:string:file://{new_path}",
                    "string:",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if p.returncode != 0:
                subprocess.Popen(["xdg-open", str(new_path.parent)], start_new_session=True)
        elif action == "delete":
            new_path.unlink()
