from __future__ import annotations

import asyncio
import json
import subprocess

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Static

from nmlinux_tui.workers import net_info as net_info_mod
from nmlinux_tui.workers import wifi_scan as wifi_mod


class DashboardScreen(Screen):
    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 3;
        grid-gutter: 1 2;
    }
    .panel {
        border: solid $primary;
        padding: 0 1;
        height: 1fr;
        overflow: hidden;
    }
    Footer {
        dock: bottom;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("RÉSEAU LOCAL\n  loading...", id="net-info", classes="panel")
        yield Static("INTERFACES\n  loading...", id="ifaces", classes="panel")
        yield Static("WI-FI\n  loading...", id="wifi", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(3.0, self._refresh_net)
        self.set_interval(3.0, self._refresh_ifaces)
        self.set_interval(10.0, self._refresh_wifi)

    # ── net info panel ────────────────────────────────────────────────────────

    async def _refresh_net(self) -> None:
        data = await asyncio.to_thread(net_info_mod.collect_local)
        text = (
            "[b]RÉSEAU LOCAL[/b]\n"
            f"  Hostname : {data.get('hostname', '—')}\n"
            f"  IPv4     : {data.get('local_ipv4', '—')}\n"
            f"  IPv6     : {data.get('local_ipv6', '—')}\n"
            f"  Gateway  : {data.get('gateway', '—')}\n"
            f"  IP pub   : {data.get('public_ip', '—')}"
        )
        self.query_one("#net-info", Static).update(text)

    # ── interfaces panel ──────────────────────────────────────────────────────

    async def _refresh_ifaces(self) -> None:
        lines = ["[b]INTERFACES[/b]"]
        try:
            raw = await asyncio.to_thread(
                lambda: subprocess.run(
                    ['ip', '-j', 'addr'], capture_output=True, text=True, timeout=3
                ).stdout
            )
            ifaces = json.loads(raw)
            for iface in ifaces[:8]:
                name = iface.get('ifname', '?')
                state = iface.get('operstate', '?')
                ipv4 = '—'
                for addr in iface.get('addr_info', []):
                    if addr.get('family') == 'inet':
                        ipv4 = addr['local']
                        break
                dot = '[green]●[/green]' if state == 'UP' else '[red]●[/red]'
                lines.append(f"  {dot} {name:<10} {ipv4}")
        except Exception:
            lines.append("  —")
        self.query_one("#ifaces", Static).update("\n".join(lines))

    # ── wifi panel ────────────────────────────────────────────────────────────

    async def _refresh_wifi(self) -> None:
        data = await asyncio.to_thread(wifi_mod.wifi_scan)
        lines = ["[b]WI-FI[/b]"]
        ssids = data.get('ssids', [])
        if not ssids:
            lines.append("  nmcli non disponible")
        for entry in ssids[:6]:
            star = '★' if entry['connected'] else ' '
            ssid = entry['ssid'][:18]
            lines.append(
                f"  {star} {ssid:<18} {entry['bar']} {entry['signal_dbm']}dBm"
            )
        self.query_one("#wifi", Static).update("\n".join(lines))
