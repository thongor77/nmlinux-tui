from __future__ import annotations

import asyncio

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Label

from nmlinux_tui.workers.wifi_scan import wifi_scan


class WifiScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.switch_screen('dashboard')", "Retour"),
        Binding("r", "rescan", "Rescanner"),
    ]

    DEFAULT_CSS = """
    WifiScreen {
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
        yield Label("WI-FI", id="title")
        yield DataTable(id="wifi-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(" ", "SSID", "Ch", "Fréq", "Signal", "dBm", "Sécurité")
        table.cursor_type = "row"
        self.set_interval(10.0, self._refresh)

    async def _refresh(self) -> None:
        data = await asyncio.to_thread(wifi_scan)
        table = self.query_one(DataTable)
        table.clear()
        ssids = data.get('ssids', [])
        if not ssids:
            table.add_row('', 'nmcli non disponible', '', '', '', '', '')
            return
        for entry in ssids:
            star = '★' if entry['connected'] else ' '
            table.add_row(
                star,
                entry['ssid'],
                entry['chan'],
                entry['freq'],
                entry['bar'],
                str(entry['signal_dbm']),
                entry['security'],
            )

    async def action_rescan(self) -> None:
        await self._refresh()
