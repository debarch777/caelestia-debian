#!/usr/bin/env bash
# ==============================================================================
#  🌌 Caelestia Hyprland Uninstaller / Backup Restorer
# ==============================================================================

set -eo pipefail

BACKUP_ROOT="${HOME}/.config/caelestia_backups"

echo "=== Caelestia Hyprland Restore & Uninstall ==="

if [ ! -d "${BACKUP_ROOT}" ]; then
    echo "No backups found in ${BACKUP_ROOT}."
    exit 1
fi

LATEST_BACKUP="$(ls -td "${BACKUP_ROOT}"/backup-* 2>/dev/null | head -n 1 || true)"

if [ -z "${LATEST_BACKUP}" ] || [ ! -d "${LATEST_BACKUP}" ]; then
    echo "No timestamped backup directories found in ${BACKUP_ROOT}."
    exit 1
fi

echo "Found latest backup: ${LATEST_BACKUP}"
read -rp "Do you want to restore this backup to ~/.config/? [y/N]: " confirm

if [[ "${confirm}" =~ ^[Yy]$ ]]; then
    for item in "${LATEST_BACKUP}"/*; do
        if [ -e "${item}" ]; then
            target_name="$(basename "${item}")"
            dest="${HOME}/.config/${target_name}"
            rm -rf "${dest}"
            cp -r "${item}" "${dest}"
            echo "Restored: ${target_name} -> ${dest}"
        fi
    done
    echo "Backup restored successfully."
else
    echo "Restore cancelled."
fi
