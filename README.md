# AirFlood

A terminal-based WiFi & Bluetooth deauthentication toolkit with a themed menu system.

## ⚠️ Legal & Ethical Use

AirFlood is intended **only** for authorized security testing — your own network/devices, or an engagement you have explicit written permission for (e.g. a pentest scope, a CTF, a lab environment). Deauthenticating wireless clients or Bluetooth devices you don't own or don't have permission to test is illegal in most jurisdictions and against the Terms of Service of virtually every network. You are solely responsible for how you use this tool.

## Status: trial-and-error testing, not a finished tool

AirFlood is being actively built and debugged right now, one real run at a time — this is **not** a stable release. Expect things to break. So far it's only been exercised on a single Kali Linux machine, catching issues as they show up (crashes, commands with wrong arguments, terminal-rendering glitches, UX rough edges) and fixing them one at a time as they're hit. There will be more.

What that means in practice:

- Behavior can change between commits as bugs get found and fixed.
- Not every code path has actually been run against real hardware yet — some are still theoretical until tested.
- If something breaks, that's expected at this stage, not a sign you did something wrong. Note what happened (a screenshot of the terminal is ideal) and report it.
- Nothing here should be relied on for a real engagement yet — treat it as a work in progress you're helping shake out, not a finished tool.

## Compatibility

| Platform | Status |
|---|---|
| Kali Linux | 🟡 Actively being tested — the only platform run so far, still finding and fixing issues |
| Parrot OS | ⚪ Not yet tried |
| Other Debian-based (Ubuntu, Debian) | ⚪ Not yet tried — dependencies are available via `apt`, but the tool hasn't been run there |
| Non-Debian Linux (Fedora, Arch, ...) | ⚪ Core scripts should run once dependencies are installed manually, but the built-in auto-installer only supports `apt` |
| Windows / macOS | ❌ Not supported (monitor mode / raw Bluetooth sockets aren't available the same way) |

## Requirements

- Linux (see Compatibility above)
- Root — AirFlood refuses to start without it (see [Environment check](#environment-check))
- Python 3
- A wireless network adapter that supports **both** monitor mode **and** packet injection (for the WiFi module) — many built-in laptop wifi chips support monitor mode but not injection, which the deauth attack needs. Check a given adapter/driver with `aireplay-ng --test <interface>` before relying on it. A well-known-compatible external USB adapter (e.g. one using an Atheros or Ralink chipset supported by `aircrack-ng`) is the safest bet.
- A Bluetooth adapter (for the Bluetooth module)
- [`aircrack-ng`](https://www.aircrack-ng.org/) suite — provides `airmon-ng`, `airodump-ng`, `aireplay-ng`
- `bluez` — provides `hciconfig`, `hcitool`, `l2ping`

You don't need to install the tool dependencies by hand — AirFlood checks for them on startup and offers to install anything missing via `apt`.

## Getting Started

```bash
git clone https://github.com/CodinWaffle/AirFlood.git
cd AirFlood
sudo python3 main.py
```

It has to be run with `sudo` — `airmon-ng`, `airodump-ng`, `aireplay-ng`, `hciconfig`, and `l2ping` all need raw device access, and AirFlood checks for root before showing the menu rather than failing partway through later.

On first run, AirFlood also checks your platform and dependencies before showing the main menu. If required tools are missing, it will ask before installing anything — nothing is installed silently.

## Usage

Run `main.py` and pick a module from the main menu:

- **WiFi Deauth** — select a wireless interface → enable monitor mode → 30-second animated scan for nearby access points → pick a target → launch the deauth attack.
- **Bluetooth Deauth** — select a Bluetooth interface (brought up automatically if it's down) → animated scan for nearby devices → pick a target → set packet size / thread count → launch the flood.

Selecting "Back" / "Exit" anywhere returns you to the AirFlood main menu rather than closing the program. `Ctrl+C` aborts the current step early.

Each module can also be run standalone for testing:

```bash
sudo python3 modules/wifi_deauth.py
sudo python3 modules/bluetooth_deauth.py
```

## Environment Check

Before the main menu loads, AirFlood:

1. Confirms it's running on Linux.
2. Reads `/etc/os-release` and notes whether you're on Kali/Parrot (a soft warning is shown on anything else — it won't block you, just flags that it's unverified there).
3. Confirms it's running as root, and refuses to continue otherwise.
4. Checks for `airmon-ng`, `airodump-ng`, `aireplay-ng`, `hciconfig`, `hcitool`, and `l2ping` on your `PATH`.
5. If any are missing and `apt-get` is available, it asks for confirmation and then runs `apt-get install` for the missing packages. On non-`apt` systems it tells you what to install manually instead of guessing.

## Project Structure

```
AirFlood/
├── main.py                     # entry point — dependency check + main menu
├── modules/
│   ├── wifi_deauth.py          # WiFi interface select → scan → deauth
│   └── bluetooth_deauth.py     # Bluetooth interface select → scan → flood
└── utils/
    ├── banner.py                # theme: colors, banners, menu rendering, animations
    └── dependencies.py          # platform, root, and dependency checks
```

## Reporting Issues

Since this is still in trial-and-error testing, the most useful thing you can do is report exactly what broke: which module, which step, what you expected vs. what happened, and a screenshot of the terminal if you can grab one. That's how the compatibility table above moves from "not yet tried" to actually verified.
