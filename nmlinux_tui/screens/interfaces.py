from __future__ import annotations

import asyncio
import json
import subprocess

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label


class InterfacesScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.switch_screen('dashboard')", "Retour"),
    ]

    DEFAULT_CSS = """
    InterfacesScreen {
        padding: 1 2;
    }
    #title {
        text-style: bold;
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("INTERFACES", id="title")
        yield DataTable(id="iface-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Interface", "Type", "État", "IPv4", "IPv6", "MAC")
        table.cursor_type = "row"
        self.set_interval(5.0, self._refresh)

    async def _refresh(self) -> None:
        try:
            raw = await asyncio.to_thread(
                lambda: subprocess.run(
                    ['ip', '-j', 'addr'], capture_output=True, text=True, timeout=5
                ).stdout
            )
            ifaces = json.loads(raw)
        except Exception:
            return

        table = self.query_one(DataTable)
        table.clear()
        for iface in ifaces:
            name = iface.get('ifname', '?')
            link_type = iface.get('link_type', '?').upper()
            state = iface.get('operstate', '?')
            mac = iface.get('address', '—') or '—'
            ipv4 = '—'
            ipv6 = '—'
            for addr in iface.get('addr_info', []):
                if addr.get('family') == 'inet' and ipv4 == '—':
                    ipv4 = f"{addr['local']}/{addr['prefixlen']}"
                elif addr.get('family') == 'inet6' and ipv6 == '—':
                    scope = addr.get('scope', '')
                    if scope == 'global':
                        ipv6 = f"{addr['local']}/{addr['prefixlen']}"
            state_str = '● UP' if state == 'UP' else '○ DOWN'
            table.add_row(name, link_type, state_str, ipv4, ipv6, mac)
