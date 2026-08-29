# 📦 Installation Guide

This guide covers installing and setting up the Caelestia Hyprland desktop environment on Debian, Parrot OS, Ubuntu, and general Linux distributions.

---

## ⚡ Quick Start (Automated Installer)

Clone the repository and run the safe, non-destructive installer:

```bash
git clone https://github.com/your-username/caelestia-dots.git
cd caelestia-dots
./install.sh
```

The installer will:
1. Automatically create a timestamped backup of any existing configs in `~/.config/caelestia_backups/`.
2. Check and install system packages (`apt` / `flatpak`).
3. Install the in-tree `caelestia-cli` Python package locally to `~/.local/bin/caelestia`.
4. Safely install dotfiles (`hypr/`, `quickshell/`, `foot/`, `fuzzel/`, `btop/`).
5. Configure PAM lockscreen authentication and Polkit authentication agents.
6. Install special workspace applications (Spotify, Discord, WhatsApp, Todoist).

---

## 🛠️ Modular Installation Options

You can run individual parts of the installer or preview actions:

```bash
# Preview what would be changed without modifying anything
./install.sh --dry-run

# Run full setup non-interactively
./install.sh --all

# Only install core system dependencies
./install.sh --deps

# Only install Caelestia CLI & Material You Theming engine
./install.sh --cli

# Only install dotfiles & configurations
./install.sh --dots

# Only install special workspace apps
./install.sh --apps

# Only install PAM lockscreen files
./install.sh --pam

# Rollback / restore previous backup
./uninstall.sh
```

---

## 📖 Manual Installation

If you prefer to install manually without the script:

### Step 1: System Packages
Install required Wayland, audio, and graphics tools:
```bash
sudo apt update
sudo apt install -y \
  hyprland quickshell foot fuzzel btop swappy grim slurp wf-recorder \
  swaybg imagemagick sassc libsass1 python3 python3-pip python3-setuptools \
  brightnessctl wireplumber pipewire-audio flatpak cliphist wl-clipboard \
  polkit-kde-agent-1 ydotool
```

### Step 2: Caelestia CLI
Install the bundled CLI locally:
```bash
pip install --user --break-system-packages ./caelestia-cli
# Or via pipx:
# pipx install ./caelestia-cli
```

### Step 3: Copy Dotfiles
```bash
mkdir -p ~/.config ~/.local/bin ~/.local/share/applications ~/Pictures/Wallpapers

cp -r config/hypr ~/.config/
cp -r config/quickshell ~/.config/
cp -r config/foot ~/.config/
cp -r config/fuzzel ~/.config/
cp -r config/btop ~/.config/
cp -r config/swappy ~/.config/
cp -r config/gtk-3.0 ~/.config/
cp -r config/qt6ct ~/.config/
cp bin/* ~/.local/bin/
cp wallpapers/* ~/Pictures/Wallpapers/
```

### Step 4: Setup PAM Authentication
```bash
sudo cp pam/quickshell /etc/pam.d/quickshell
sudo cp pam/caelestia /etc/pam.d/caelestia
```

### Step 5: Special Apps (Flatpak)
```bash
flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub com.spotify.Client com.discordapp.Discord com.todoist.Todoist
```

### Step 6: Initialize Theme & Wallpaper
```bash
caelestia wallpaper -r ~/Pictures/Wallpapers/
caelestia scheme set -n dynamic
hyprctl reload
```
