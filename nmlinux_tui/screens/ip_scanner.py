from __future__ import annotations

import re
import subprocess
import threading

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Input, Label, ProgressBar

from nmlinux_tui.workers.ip_scan import scan_cidr, parse_cidr


class IpScannerScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.switch_screen('dashboard')", "Retour"),
    ]

    DEFAULT_CSS = """
    IpScannerScreen {
        padding: 1 2;
    }
    #title {
        text-style: bold;
        margin-bottom: 1;
    }
    #controls {
        height: 3;
        margin-bottom: 1;
    }
    #cidr-input {
        width: 24;
    }
    #scan-btn {
        width: 12;
        margin-left: 2;
    }
    #progress {
        margin-bottom: 1;
        height: 2;
    }
    #status {
        height: 1;
        margin-bottom: 1;
    }
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("IP SCANNER", id="title")
        with Horizontal(id="controls"):
            yield Input(placeholder="192.168.1.0/24", id="cidr-input")
            yield Button("Lancer", id="scan-btn", variant="primary")
        yield Label("", id="status")
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield DataTable(id="scan-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("IP", "Hostname")
        table.cursor_type = "row"
        self._scanning = False
        self.query_one(ProgressBar).update(progress=0)
        self._prefill_cidr()

    def _prefill_cidr(self) -> None:
        try:
            route = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m = re.search(r'src (\d+\.\d+\.\d+\.\d+)', route)
            if m:
                parts = m.group(1).rsplit('.', 1)
                cidr = parts[0] + '.0/24'
                self.query_one("#cidr-input", Input).value = cidr
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan-btn" and not self._scanning:
            cidr = self.query_one("#cidr-input", Input).value.strip()
            self._start_scan(cidr)

    def _start_scan(self, cidr: str) -> None:
        hosts = parse_cidr(cidr)
        if isinstance(hosts, str):
            self.query_one("#status", Label).update(f"[red]{hosts}[/red]")
            return

        self._scanning = True
        table = self.query_one(DataTable)
        table.clear()
        bar = self.query_one(ProgressBar)
        bar.update(total=len(hosts), progress=0)
        self.query_one("#status", Label).update(f"Scanning {len(hosts)} hosts...")

        def on_result(ip: str, hostname: str) -> None:
            self.app.call_from_thread(table.add_row, ip, hostname or '—')

        def on_progress(done: int, total: int) -> None:
            self.app.call_from_thread(bar.update, progress=done)

        def on_done() -> None:
            self._scanning = False
            self.app.call_from_thread(
                self.query_one("#status", Label).update,
                f"[green]Done — {table.row_count} hosts found[/green]"
            )

        threading.Thread(
            target=scan_cidr,
            args=(cidr, on_result, on_progress, on_done),
            daemon=True,
        ).start()
