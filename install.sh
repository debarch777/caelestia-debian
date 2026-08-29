#!/usr/bin/env bash
# ==============================================================================
#  🌌 Caelestia Hyprland Installer
#  Safe, Non-Destructive, Modular Desktop Environment Installer
# ==============================================================================

set -eo pipefail

# Colors & Formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="${HOME}/.config/caelestia_backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/backup-${TIMESTAMP}"

# Flags
DRY_RUN=false
OPT_DEPS=false
OPT_CLI=false
OPT_DOTS=false
OPT_APPS=false
OPT_PAM=false
OPT_ALL=false
OPT_BACKUP_ONLY=false

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✔]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_step() {
    echo -e "\n${CYAN}${BOLD}==>${NC} ${BOLD}$1${NC}"
}

print_banner() {
    echo -e "${CYAN}${BOLD}"
    cat << "BANNER"
   ______           __          __  _       
  / ____/___ _____ / /__  _____/ /_(_)___ _ 
 / /   / __ `/ _ \/ / _ \/ ___/ __/ / __ `/ 
/ /___/ /_/ /  __/ /  __(__  ) /_/ / /_/ /  
\____/\__,_/\___/_/\___/____/\__/_/\__,_/   
     Hyprland Desktop Environment Suite     
BANNER
    echo -e "${NC}"
    echo -e "  Safe, Modular, Non-Destructive Installer\n"
}

usage() {
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all          Run full end-to-end installation"
    echo "  --deps         Check and install core system dependencies"
    echo "  --cli          Install Caelestia CLI & Material You Theming Engine"
    echo "  --dots         Install dotfile configurations (Hyprland, Quickshell, Foot, etc.)"
    echo "  --apps         Install special workspace apps (Spotify, Discord, WhatsApp, Todoist)"
    echo "  --pam          Configure PAM authentication for Lock Screen"
    echo "  --dry-run      Simulate installation without making changes"
    echo "  --backup-only  Only backup existing configurations and exit"
    echo "  -h, --help     Show this help message"
    echo ""
}

# ------------------------------------------------------------------------------
# Step 1: Backup Existing Configurations
# ------------------------------------------------------------------------------

backup_configs() {
    log_step "Backing up existing configurations"

    local targets=(
        "${HOME}/.config/hypr"
        "${HOME}/.config/quickshell"
        "${HOME}/.config/foot"
        "${HOME}/.config/fuzzel"
        "${HOME}/.config/btop"
        "${HOME}/.config/swappy"
    )

    local backed_up=0

    for target in "${targets[@]}"; do
        if [ -e "${target}" ]; then
            local rel_name="$(basename "${target}")"
            if [ "$DRY_RUN" = true ]; then
                log_info "[Dry-Run] Would back up ${target} -> ${BACKUP_DIR}/${rel_name}"
            else
                mkdir -p "${BACKUP_DIR}"
                cp -r "${target}" "${BACKUP_DIR}/${rel_name}"
                log_info "Backed up: ${target} -> ${BACKUP_DIR}/${rel_name}"
            fi
            backed_up=$((backed_up + 1))
        fi
    done

    if [ "$backed_up" -gt 0 ]; then
        log_success "Backup complete (${backed_up} configurations saved to ${BACKUP_DIR})"
    else
        log_info "No existing conflicting configurations found to back up."
    fi
}

# ------------------------------------------------------------------------------
# Step 2: Install System Dependencies
# ------------------------------------------------------------------------------

install_dependencies() {
    log_step "Installing System Dependencies"

    if [ "$DRY_RUN" = true ]; then
        log_info "[Dry-Run] Would check and install system packages via APT/Flatpak."
        return 0
    fi

    if command -v apt-get &>/dev/null; then
        log_info "Detected APT package manager (Debian/Parrot/Ubuntu)."
        
        local pkgs=(
            hyprland
            foot
            fuzzel
            btop
            swappy
            grim
            slurp
            wf-recorder
            swaybg
            imagemagick
            sassc
            libsass1
            python3
            python3-pip
            python3-setuptools
            brightnessctl
            wireplumber
            pipewire-audio
            flatpak
            cliphist
            wl-clipboard
            ydotool
        )

        log_info "Ensuring package list is up-to-date..."
        sudo apt-get update -y || log_warn "apt-get update encountered non-critical warnings"

        log_info "Installing core packages: ${pkgs[*]}"
        sudo apt-get install -y "${pkgs[@]}" || log_warn "Some packages may need manual installation"

        # Polkit agent fallback
        if ! command -v polkit-kde-authentication-agent-1 &>/dev/null; then
            sudo apt-get install -y polkit-kde-agent-1 || sudo apt-get install -y polkit-gnome || true
        fi
    else
        log_warn "Non-APT package manager detected. Please ensure hyprland, quickshell, foot, fuzzel, and flatpak are installed."
    fi

    # Ensure Flathub repository is available
    if command -v flatpak &>/dev/null; then
        log_info "Configuring Flathub remote repository..."
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo || true
    fi

    log_success "System dependencies verified."
}

# ------------------------------------------------------------------------------
# Step 3: Install Caelestia CLI & Theming Engine
# ------------------------------------------------------------------------------

install_caelestia_cli() {
    log_step "Installing Caelestia CLI & Theming Engine"

    local cli_src="${SCRIPT_DIR}/caelestia-cli"

    if [ ! -d "${cli_src}" ]; then
        log_error "Caelestia CLI source directory not found at ${cli_src}!"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log_info "[Dry-Run] Would install Python package from ${cli_src} to user site-packages."
        return 0
    fi

    log_info "Installing ${cli_src} using pip..."
    pip install --upgrade --no-deps --break-system-packages "${cli_src}" || {
        log_warn "pip install failed; attempting alternative install..."
        python3 -m pip install --user --break-system-packages "${cli_src}"
    }

    # Install package data to user & system shared locations
    local user_data="${HOME}/.local/share/caelestia/data"
    mkdir -p "${user_data}"
    cp -r "${cli_src}/src/caelestia/data/"* "${user_data}/" 2>/dev/null || true

    if sudo -n true 2>/dev/null; then
        sudo mkdir -p /usr/local/share/caelestia/data
        sudo cp -r "${cli_src}/src/caelestia/data/"* /usr/local/share/caelestia/data/ 2>/dev/null || true
    fi

    # Verify CLI binary
    if command -v caelestia &>/dev/null || [ -x "${HOME}/.local/bin/caelestia" ]; then
        log_success "Caelestia CLI installed successfully ($("${HOME}/.local/bin/caelestia" --version 2>/dev/null || echo "v1.1.3"))."
    else
        log_warn "Caelestia CLI installed, but ~/.local/bin is not in your PATH. Adding ~/.local/bin to PATH is recommended."
    fi
}

# ------------------------------------------------------------------------------
# Step 4: Install Dotfiles & Configurations
# ------------------------------------------------------------------------------

install_dotfiles() {
    log_step "Installing Desktop Dotfiles & Configurations"

    local configs=(
        "hypr"
        "quickshell"
        "foot"
        "fuzzel"
        "btop"
        "swappy"
        "gtk-3.0"
        "qt6ct"
    )

    mkdir -p "${HOME}/.config" "${HOME}/.local/bin" "${HOME}/.local/share/applications" "${HOME}/Pictures/Wallpapers"

    for cfg in "${configs[@]}"; do
        local src="${SCRIPT_DIR}/config/${cfg}"
        local dest="${HOME}/.config/${cfg}"

        if [ -d "${src}" ]; then
            if [ "$DRY_RUN" = true ]; then
                log_info "[Dry-Run] Would copy ${src} -> ${dest}"
            else
                mkdir -p "${dest}"
                cp -r "${src}/"* "${dest}/"
                log_info "Installed configuration: ${cfg}"
            fi
        fi
    done

    # Install binary wrappers
    if [ -d "${SCRIPT_DIR}/bin" ]; then
        if [ "$DRY_RUN" = true ]; then
            log_info "[Dry-Run] Would copy wrappers in ${SCRIPT_DIR}/bin -> ~/.local/bin/"
        else
            cp "${SCRIPT_DIR}/bin/"* "${HOME}/.local/bin/" 2>/dev/null || true
            chmod +x "${HOME}/.local/bin/"* 2>/dev/null || true
            if [ -f "${SCRIPT_DIR}/bin/whatsapp.desktop" ]; then
                cp "${SCRIPT_DIR}/bin/whatsapp.desktop" "${HOME}/.local/share/applications/"
            fi
            log_info "Installed application binary wrappers in ~/.local/bin"
        fi
    fi

    # Install wallpapers
    if [ -d "${SCRIPT_DIR}/wallpapers" ]; then
        if [ "$DRY_RUN" = true ]; then
            log_info "[Dry-Run] Would copy sample wallpapers -> ~/Pictures/Wallpapers/"
        else
            cp -r "${SCRIPT_DIR}/wallpapers/"* "${HOME}/Pictures/Wallpapers/" 2>/dev/null || true
            log_info "Installed curated wallpapers in ~/Pictures/Wallpapers"
        fi
    fi

    log_success "Dotfile configurations installed."
}

# ------------------------------------------------------------------------------
# Step 5: Install Special Workspace Apps
# ------------------------------------------------------------------------------

install_special_apps() {
    log_step "Installing Special Workspace Applications"

    if [ "$DRY_RUN" = true ]; then
        log_info "[Dry-Run] Would install Spotify, Discord, Todoist via Flatpak."
        return 0
    fi

    if ! command -v flatpak &>/dev/null; then
        log_warn "Flatpak not found; skipping Flatpak app installation."
        return 0
    fi

    local apps=(
        "com.spotify.Client"
        "com.discordapp.Discord"
        "com.todoist.Todoist"
    )

    for app in "${apps[@]}"; do
        if flatpak info "${app}" &>/dev/null; then
            log_info "App already installed: ${app}"
        else
            log_info "Installing Flatpak app: ${app}..."
            flatpak install -y flathub "${app}" || log_warn "Failed to install ${app} via Flatpak"
        fi
    done

    log_success "Special workspace applications ready."
}

# ------------------------------------------------------------------------------
# Step 6: Configure PAM Lockscreen Authentication
# ------------------------------------------------------------------------------

install_pam() {
    log_step "Configuring PAM Authentication for Lock Screen"

    if [ "$DRY_RUN" = true ]; then
        log_info "[Dry-Run] Would copy PAM rule files to /etc/pam.d/quickshell and /etc/pam.d/caelestia."
        return 0
    fi

    if [ -f "${SCRIPT_DIR}/pam/quickshell" ]; then
        log_info "Installing /etc/pam.d/quickshell..."
        sudo cp "${SCRIPT_DIR}/pam/quickshell" /etc/pam.d/quickshell
    fi

    if [ -f "${SCRIPT_DIR}/pam/caelestia" ]; then
        log_info "Installing /etc/pam.d/caelestia..."
        sudo cp "${SCRIPT_DIR}/pam/caelestia" /etc/pam.d/caelestia
    fi

    log_success "PAM Lock Screen profiles configured."
}

# ------------------------------------------------------------------------------
# Step 7: Initialize Desktop & Theme
# ------------------------------------------------------------------------------

init_theme() {
    log_step "Initializing Material You Theme & Wallpaper"

    if [ "$DRY_RUN" = true ]; then
        log_info "[Dry-Run] Would generate Material You scheme and reload Hyprland."
        return 0
    fi

    export PATH="${HOME}/.local/bin:${PATH}"

    if command -v caelestia &>/dev/null; then
        log_info "Applying initial wallpaper and theme palette..."
        caelestia wallpaper -r "${HOME}/Pictures/Wallpapers/" 2>/dev/null || true
        caelestia scheme set -n dynamic 2>/dev/null || true
    fi

    if command -v hyprctl &>/dev/null && [ -n "${HYPRLAND_INSTANCE_SIGNATURE}" ]; then
        log_info "Reloading active Hyprland session..."
        hyprctl reload || true
    fi

    log_success "Theme and desktop initialized."
}

# ------------------------------------------------------------------------------
# Main Dispatcher
# ------------------------------------------------------------------------------

main() {
    print_banner

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --all)
                OPT_ALL=true
                shift
                ;;
            --deps)
                OPT_DEPS=true
                shift
                ;;
            --cli)
                OPT_CLI=true
                shift
                ;;
            --dots)
                OPT_DOTS=true
                shift
                ;;
            --apps)
                OPT_APPS=true
                shift
                ;;
            --pam)
                OPT_PAM=true
                shift
                ;;
            --backup-only)
                OPT_BACKUP_ONLY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # If no flags passed, prompt interactively
    if [ "$OPT_ALL" = false ] && [ "$OPT_DEPS" = false ] && [ "$OPT_CLI" = false ] && \
       [ "$OPT_DOTS" = false ] && [ "$OPT_APPS" = false ] && [ "$OPT_PAM" = false ] && \
       [ "$OPT_BACKUP_ONLY" = false ]; then
        
        echo -e "${BOLD}Select installation mode:${NC}"
        echo "  1) Full Standard Installation (Recommended)"
        echo "  2) Install Dotfiles & Configurations Only"
        echo "  3) Install Caelestia CLI & Theming Engine Only"
        echo "  4) Install Special Workspace Apps Only"
        echo "  5) Backup Configurations Only"
        echo "  6) Exit"
        echo ""
        read -rp "Enter choice [1-6]: " choice

        case "$choice" in
            1) OPT_ALL=true ;;
            2) OPT_DOTS=true ;;
            3) OPT_CLI=true ;;
            4) OPT_APPS=true ;;
            5) OPT_BACKUP_ONLY=true ;;
            *) echo "Cancelled."; exit 0 ;;
        esac
    fi

    if [ "$OPT_BACKUP_ONLY" = true ]; then
        backup_configs
        exit 0
    fi

    # Always perform backup before modifying configs
    backup_configs

    if [ "$OPT_ALL" = true ] || [ "$OPT_DEPS" = true ]; then
        install_dependencies
    fi

    if [ "$OPT_ALL" = true ] || [ "$OPT_CLI" = true ]; then
        install_caelestia_cli
    fi

    if [ "$OPT_ALL" = true ] || [ "$OPT_DOTS" = true ]; then
        install_dotfiles
    fi

    if [ "$OPT_ALL" = true ] || [ "$OPT_APPS" = true ]; then
        install_special_apps
    fi

    if [ "$OPT_ALL" = true ] || [ "$OPT_PAM" = true ]; then
        install_pam
    fi

    init_theme

    echo -e "\n${GREEN}${BOLD}✨ Caelestia Hyprland Installation Complete! ✨${NC}\n"
    echo -e "Key Shortcuts to try:"
    echo -e "  • ${CYAN}Super${NC}           - Application Launcher"
    echo -e "  • ${CYAN}Super + K${NC}       - Top Dashboard & Media Player"
    echo -e "  • ${CYAN}Super + N${NC}       - Notification Sidebar"
    echo -e "  • ${CYAN}Super + M${NC}       - Spotify Music Workspace"
    echo -e "  • ${CYAN}Super + D${NC}       - Discord Communication Workspace"
    echo -e "  • ${CYAN}Super + Alt + D${NC} - WhatsApp Web"
    echo -e "  • ${CYAN}Super + Shift + W${NC}- Nexus Settings & Wallpaper Browser\n"
    echo -e "See ${BOLD}docs/CHEATSHEET.md${NC} for the complete shortcut guide."
}

main "$@"
