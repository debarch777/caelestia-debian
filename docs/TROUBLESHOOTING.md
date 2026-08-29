# 🔧 Troubleshooting Guide

Common issues, diagnostics, and solutions for the Caelestia Hyprland environment.

---

## 1. Special Workspaces (`Super + M`, `Super + D`) Open Empty / Dim Screen
* **Cause:** The target application (Spotify or Discord) is not installed in your PATH or Flatpak runtime.
* **Solution:**
  1. Verify the binary wrapper exists in `~/.local/bin/`:
     ```bash
     which spotify discord todoist whatsapp
     ```
  2. Verify Flatpak is installed:
     ```bash
     flatpak list | grep -iE "spotify|discord|todoist"
     ```
  3. Install any missing application:
     ```bash
     flatpak install flathub com.spotify.Client com.discordapp.Discord com.todoist.Todoist
     ```

---

## 2. Lock Screen Authentication Fails
* **Cause:** Missing PAM authentication rule for `quickshell` in `/etc/pam.d/`.
* **Solution:**
  Ensure `/etc/pam.d/quickshell` and `/etc/pam.d/caelestia` exist:
  ```bash
  sudo cp pam/quickshell /etc/pam.d/quickshell
  sudo cp pam/caelestia /etc/pam.d/caelestia
  ```

---

## 3. Screen Recording (`Ctrl + Alt + R`) Doesn't Record
* **Cause:** Missing video recording backend.
* **Solution:**
  Install `wf-recorder` (universal Wayland screen recorder):
  ```bash
  sudo apt install -y wf-recorder
  ```
  `caelestia record` automatically falls back from `gpu-screen-recorder` to `wf-recorder`.

---

## 4. Nvidia GPU Flickering or Black Windows on Wayland
* **Cause:** Missing Wayland environment flags for Nvidia proprietary drivers.
* **Solution:**
  In `~/.config/hypr/hyprland/env.lua`, verify these flags are set:
  ```lua
  hl.set_env("LIBVA_DRIVER_NAME", "nvidia")
  hl.set_env("XDG_SESSION_TYPE", "wayland")
  hl.set_env("GBM_BACKEND", "nvidia-drm")
  hl.set_env("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
  hl.set_env("NVD_BACKEND", "direct")
  hl.set_env("ELECTRON_OZONE_PLATFORM_HINT", "auto")
  ```

---

## 5. Quickshell Logs & Diagnostics
To inspect the live status of all desktop shell drawers and widgets:
```bash
# Print all shell IPC commands
caelestia shell -s

# View live shell log stream
caelestia shell -l

# Restart the shell daemon
caelestia shell -k && caelestia shell -d
```
