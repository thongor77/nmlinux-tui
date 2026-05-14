from __future__ import annotations

from textual.app import App
from textual.binding import Binding

from nmlinux_tui.screens.dashboard import DashboardScreen
from nmlinux_tui.screens.interfaces import InterfacesScreen
from nmlinux_tui.screens.wifi import WifiScreen
from nmlinux_tui.screens.ping import PingScreen
from nmlinux_tui.screens.ip_scanner import IpScannerScreen


class TuiApp(App):
    TITLE = "nmlinux-tui"

    SCREENS = {
        "dashboard": DashboardScreen,
        "interfaces": InterfacesScreen,
        "wifi": WifiScreen,
        "ping": PingScreen,
        "ip_scanner": IpScannerScreen,
    }

    BINDINGS = [
        Binding("d", "switch_screen('dashboard')", "Dashboard"),
        Binding("1", "switch_screen('interfaces')", "Interfaces"),
        Binding("2", "switch_screen('wifi')", "Wi-Fi"),
        Binding("3", "switch_screen('ping')", "Ping"),
        Binding("4", "switch_screen('ip_scanner')", "IP Scanner"),
        Binding("q", "quit", "Quitter", priority=True),
    ]

    def on_mount(self) -> None:
        self.push_screen("dashboard")


def main() -> None:
    TuiApp().run()


if __name__ == "__main__":
    main()
