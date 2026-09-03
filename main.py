from utils import banner
from utils.dependencies import ensure_dependencies


MENU_OPTIONS = [
    ("1", "WiFi Deauth", "target a wireless access point"),
    ("2", "Bluetooth Deauth", "target a bluetooth device"),
    ("3", "Exit", "quit AirFlood"),
]


def launch_wifi():
    from modules.wifi_deauth import run
    run()


def launch_bluetooth():
    from modules.bluetooth_deauth import scan_attack
    scan_attack()


def main():
    while True:
        banner.banner()
        banner.section("main menu")
        choice = banner.menu(MENU_OPTIONS)

        try:
            if choice == "1":
                launch_wifi()
            elif choice == "2":
                launch_bluetooth()
            elif choice == "3":
                banner.info("bye.")
                return
            else:
                banner.warn("invalid selection, try again")
                input("press enter to continue...")
                continue
        except banner.BackToMenu:
            pass

        input(f"\n{banner.C.MUTED}press enter to return to the main menu...{banner.C.RESET}")


if __name__ == "__main__":
    try:
        ensure_dependencies()
        input(f"\n{banner.C.MUTED}press enter to continue to AirFlood...{banner.C.RESET}")
        main()
    except KeyboardInterrupt:
        print()
        banner.warn("aborted")
