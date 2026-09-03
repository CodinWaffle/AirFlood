"""Terminal theming for AirFlood: colors, banner, and menu rendering."""

import os
import sys


class BackToMenu(Exception):
    """Raised by a module to unwind back to the AirFlood main menu instead of exiting."""


class C:
    """ANSI color codes — electric blue / cyan storm theme."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # gradient shades used for the logo, dark -> bright
    NAVY = "\033[38;5;25m"
    BLUE = "\033[38;5;33m"
    SKY = "\033[38;5;39m"
    CYAN = "\033[38;5;45m"
    ICE = "\033[38;5;51m"
    WHITE = "\033[38;5;231m"

    ACCENT = "\033[38;5;51m"   # bright ice-cyan accents / borders
    MUTED = "\033[38;5;67m"    # muted steel-blue for secondary text
    WARN = "\033[38;5;208m"
    DANGER = "\033[38;5;196m"
    OK = "\033[38;5;48m"


LOGO_LINES = [
    r" █████╗ ██╗██████╗ ███████╗██╗      ██████╗  ██████╗ ██████╗ ",
    r"██╔══██╗██║██╔══██╗██╔════╝██║     ██╔═══██╗██╔═══██╗██╔══██╗",
    r"███████║██║██████╔╝█████╗  ██║     ██║   ██║██║   ██║██║  ██║",
    r"██╔══██║██║██╔══██╗██╔══╝  ██║     ██║   ██║██║   ██║██║  ██║",
    r"██║  ██║██║██║  ██║██║     ███████╗╚██████╔╝╚██████╔╝██████╔╝",
    r"╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ",
]

# one gradient shade per logo line, dark navy fading into bright ice-cyan
LOGO_GRADIENT = [C.NAVY, C.BLUE, C.SKY, C.CYAN, C.ICE, C.ICE]

TAGLINE = "wireless deauthentication toolkit"
COMPAT_NOTE = "linux only · built & tested on kali linux and parrot os"

# per-module sub-banners: same storm palette, distinct glyph + accent so the
# screen is instantly recognizable as "not the main menu anymore"
MODULE_THEMES = {
    "wifi": {
        "accent": C.CYAN,
        "glyph_line": "▂▄▆█   W I F I   D E A U T H   █▆▄▂",
        "subtitle": "access point discovery & deauthentication",
    },
    "bluetooth": {
        "accent": "\033[38;5;69m",  # steel indigo — distinct from wifi's cyan, same family
        "glyph_line": "ᛒ─   B L U E T O O T H   D E A U T H   ─ᛒ",
        "subtitle": "device discovery & l2ping flood",
    },
}


def width(default=72):
    # os.get_terminal_size() queries the real pty directly, bypassing any stale
    # COLUMNS/LINES env vars that shutil.get_terminal_size() would otherwise
    # trust blindly (common after sudo, tmux, or a resized window/pane) — a
    # stale wider value here makes every centered line wrap unpredictably.
    try:
        return max(60, min(os.get_terminal_size(sys.__stdout__.fileno()).columns, 100))
    except OSError:
        return default


def clear():
    # \033[2J clears the visible screen, \033[3J clears scrollback, \033[H homes the cursor
    print("\033[2J\033[3J\033[H", end="", flush=True)


def hr(char="─", color=C.MUTED):
    print(f"{color}{char * width()}{C.RESET}")


def banner():
    clear()
    w = width()
    for line, shade in zip(LOGO_LINES, LOGO_GRADIENT):
        print(f"{shade}{C.BOLD}{line.center(w)}{C.RESET}")
    print(f"{C.MUTED}{TAGLINE.center(w)}{C.RESET}")
    print(f"{C.DIM}{C.MUTED}{COMPAT_NOTE.center(w)}{C.RESET}")
    print()
    hr()


def module_banner(module):
    """Clear the screen and show the sub-banner for a specific module (wifi/bluetooth)."""
    theme = MODULE_THEMES[module]
    accent = theme["accent"]
    clear()
    w = width()
    print(f"{C.MUTED}{'AIRFLOOD'.center(w)}{C.RESET}")
    print(f"{accent}{C.BOLD}{theme['glyph_line'].center(w)}{C.RESET}")
    print(f"{C.MUTED}{theme['subtitle'].center(w)}{C.RESET}")
    print()
    hr(color=accent)


def section(title, accent=None):
    print(f"\n{accent or C.ACCENT}{C.BOLD}▸ {title}{C.RESET}")


def prompt(label="select an option", accent=None):
    accent = accent or C.ACCENT
    return input(f"{C.CYAN}{C.BOLD}airflood{C.RESET}{C.MUTED} ❯ {C.RESET}{label} {accent}» {C.RESET}").strip()


def menu(options, label="select an option", accent=None):
    """
    Render a numbered menu.
    options: list of (key, label, description) tuples
    """
    print()
    for key, opt_label, desc in options:
        key_tag = f"{accent or C.ACCENT}{C.BOLD}[{key}]{C.RESET}"
        label_txt = f"{C.WHITE}{opt_label}{C.RESET}"
        desc_txt = f"{C.MUTED}  · {desc}{C.RESET}" if desc else ""
        print(f"  {key_tag} {label_txt}{desc_txt}")
    print()
    return prompt(label, accent=accent)


def info(msg):
    print(f"{C.SKY}[i]{C.RESET} {msg}")


def ok(msg):
    print(f"{C.OK}[✓]{C.RESET} {msg}")


def warn(msg):
    print(f"{C.WARN}[!]{C.RESET} {msg}")


def error(msg):
    print(f"{C.DANGER}[✗]{C.RESET} {msg}")


def countdown(seconds, label="starting"):
    import time
    for i in range(seconds, 0, -1):
        print(f"\r{C.WARN}[*] {label} in {i}...{C.RESET}   ", end="", flush=True)
        time.sleep(1)
    print(f"\r{C.OK}[*] go.{C.RESET}                        ")


SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def spinner_frame(tick, accent=None):
    accent = accent or C.ACCENT
    return f"{accent}{C.BOLD}{SPINNER_FRAMES[tick % len(SPINNER_FRAMES)]}{C.RESET}"


def progress_bar(elapsed, total, bar_width=32, accent=None):
    """Render a filled/empty block progress bar with a percentage, e.g. '████░░░░  42%'."""
    accent = accent or C.ACCENT
    ratio = min(1.0, max(0.0, elapsed / total)) if total > 0 else 1.0
    filled = int(bar_width * ratio)
    bar = "█" * filled + "░" * (bar_width - filled)
    pct = int(ratio * 100)
    return f"{accent}{bar}{C.RESET} {C.MUTED}{pct:3d}%{C.RESET}"


if __name__ == "__main__":
    banner()
    section("main menu")
    choice = menu(
        [
            ("1", "WiFi Deauth", "target a wireless access point"),
            ("2", "Bluetooth Deauth", "target a bluetooth device"),
            ("3", "Exit", "quit AirFlood"),
        ]
    )
    print(f"\nyou picked: {choice}")
