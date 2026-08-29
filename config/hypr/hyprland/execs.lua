local vars = require("variables")
local fn   = require("utils.functions")

-- Launch Caelestia Shell and desktop services once Hyprland socket is ready
local function start_desktop()
    -- 1. Update D-Bus & Systemd User Environment (prevents 20s app launch freezes)
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP HYPRLAND_INSTANCE_SIGNATURE && systemctl --user restart xdg-desktop-portal-hyprland xdg-desktop-portal 2>/dev/null || true")

    -- 2. Instant Wallpaper Pre-Render (0ms screen fill)
    hl.exec_cmd("swaybg -i " .. os.getenv("HOME") .. "/.local/state/caelestia/wallpaper/current -m fill")

    -- 3. Start Caelestia Shell daemon
    hl.exec_cmd("caelestia shell -d")

    -- 4. Pre-warm file manager daemon
    hl.exec_cmd("thunar --daemon")

    -- 5. Clean up legacy bars
    hl.exec_cmd("pkill -9 waybar swaync dunst mako ags eww 2>/dev/null || true")

    -- 6. Keyring daemon
    hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")

    -- 7. Clipboard history
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")

    -- 8. Cursors
    hl.exec_cmd("hyprctl setcursor " .. vars.cursorTheme .. " " .. vars.cursorSize)
    hl.exec_cmd("gsettings set org.gnome.desktop.interface cursor-theme " .. vars.cursorTheme)
    hl.exec_cmd("gsettings set org.gnome.desktop.interface cursor-size " .. vars.cursorSize)

    -- 9. Bluetooth MPRIS Proxy
    hl.exec_cmd("mpris-proxy")

    -- 10. Handy Speech-to-Text daemon
    hl.exec_cmd("handy --start-hidden")

    -- 11. Polkit GUI Authentication Agent
    hl.exec_cmd("/usr/lib/x86_64-linux-gnu/libexec/polkit-kde-authentication-agent-1 || /usr/lib/polkit-kde-authentication-agent-1 || /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1")
end

hl.on("hyprland.ready", start_desktop)
hl.on("hyprland.start", start_desktop)

-- Resizer listeners
local function apply_resizer_rules(win)
    local float_center = {
        hl.dsp.window.float({ action = "on", window = win }),
        hl.dsp.window.center({ window = win }),
    }
    local pip_actions = fn.move_actions(win) or {}

    if win.class == "Bitwarden" then
        hl.batch(float_center)
    end
end

hl.on("window.title", apply_resizer_rules)
hl.on("window.open", apply_resizer_rules)
