# AirFlood

A terminal-based WiFi & Bluetooth deauthentication toolkit with a themed menu system.

## ⚠️ Legal & Ethical Use

AirFlood is intended **only** for authorized security testing — your own network/devices, or an engagement you have explicit written permission for (e.g. a pentest scope, a CTF, a lab environment). Deauthenticating wireless clients or Bluetooth devices you don't own or don't have permission to test is illegal in most jurisdictions and against the Terms of Service of virtually every network. You are solely responsible for how you use this tool.

## Status

This is an early-stage project, currently **tested only on Kali Linux**. It is expected to work on Parrot OS as well (same toolset, same Debian base) but that hasn't been verified yet. Behavior on other Debian-based distros (Ubuntu, Debian itself, etc.) is untested and unconfirmed — the tools it depends on are packaged there too, but nothing beyond Kali has actually been run and checked.

## Compatibility

| Platform | Status |
|---|---|
| Kali Linux | ✅ Tested |
| Parrot OS | 🟡 Expected to work, not yet verified |
| Other Debian-based (Ubuntu, Debian) | 🟡 Untested — dependencies are available via `apt`, but the tool hasn't been run there |
| Non-Debian Linux (Fedora, Arch, ...) | 🟡 Core scripts should run once dependencies are installed manually, but the built-in auto-installer only supports `apt` |
| Windows / macOS | ❌ Not supported (monitor mode / raw Bluetooth sockets aren't available the same way) |

## Requirements

- Linux (see Compatibility above)
- Python 3
- A wireless network adapter that supports monitor mode (for the WiFi module)
- A Bluetooth adapter (for the Bluetooth module)
- [`aircrack-ng`](https://www.aircrack-ng.org/) suite — provides `airmon-ng`, `airodump-ng`, `aireplay-ng`
- `bluez` — provides `hciconfig`, `hcitool`, `l2ping`

You don't need to install these by hand — AirFlood checks for them on startup and offers to install anything missing via `apt` (see [Environment check](#environment-check)).

## Getting Started

```bash
git clone <this-repo-url>
cd AirFlood
python3 main.py
```

On first run, AirFlood checks your platform and dependencies before showing the main menu. If required tools are missing, it will ask before installing anything — nothing is installed silently.

Since monitor mode and interface control require elevated privileges, some steps will prompt for `sudo`.

## Usage

Run `main.py` and pick a module from the main menu:

- **WiFi Deauth** — select a wireless interface → enable monitor mode → scan for nearby access points → pick a target → launch the deauth attack.
- **Bluetooth Deauth** — select a Bluetooth interface → scan for nearby devices → pick a target → set packet size / thread count → launch the flood.

Selecting "Back" / "Exit" anywhere returns you to the AirFlood main menu rather than closing the program. `Ctrl+C` aborts the current step.

Each module can also be run standalone for testing:

```bash
python3 modules/wifi_deauth.py
python3 modules/bluetooth_deauth.py
```

## Environment Check

Before the main menu loads, AirFlood:

1. Confirms it's running on Linux.
2. Reads `/etc/os-release` and notes whether you're on Kali/Parrot (a soft warning is shown on anything else — it won't block you, just flags that it's unverified there).
3. Checks for `airmon-ng`, `airodump-ng`, `aireplay-ng`, `hciconfig`, `hcitool`, and `l2ping` on your `PATH`.
4. If any are missing and `apt-get` is available, it asks for confirmation and then runs `sudo apt-get install` for the missing packages. On non-`apt` systems it tells you what to install manually instead of guessing.

## Project Structure

```
AirFlood/
├── main.py                     # entry point — dependency check + main menu
├── modules/
│   ├── wifi_deauth.py          # WiFi interface select → scan → deauth
│   └── bluetooth_deauth.py     # Bluetooth interface select → scan → flood
└── utils/
    ├── banner.py                # theme: colors, banners, menu rendering
    └── dependencies.py          # platform + dependency checks
```

## Contributing

If you run this on Parrot OS, another Debian-based distro, or hit a compatibility issue, opening an issue with your distro/version is genuinely useful — the compatibility table above will get updated as it's actually verified rather than assumed.
