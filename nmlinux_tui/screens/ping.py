from __future__ import annotations

import re
import subprocess

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Input, Label

from nmlinux_tui.workers.ping_worker import PingWorker, PingStats


class PingScreen(Screen):
    BINDINGS = [
        Binding("escape", "app.switch_screen('dashboard')", "Retour"),
        Binding("a", "add_host", "Ajouter"),
        Binding("delete", "remove_host", "Retirer"),
    ]

    DEFAULT_CSS = """
    PingScreen {
        padding: 1 2;
    }
    #title {
        text-style: bold;
        margin-bottom: 1;
    }
    #input-row {
        height: 3;
        display: none;
    }
    #host-input {
        width: 32;
    }
    DataTable {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("PING MONITOR", id="title")
        with Horizontal(id="input-row"):
            yield Input(placeholder="hostname ou IP", id="host-input")
        yield DataTable(id="ping-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("Hôte", key="host")
        table.add_column("État", key="state")
        table.add_column("RTT", key="rtt")
        table.add_column("Avg", key="avg")
        table.add_column("Min", key="min")
        table.add_column("Max", key="max")
        table.add_column("Perte", key="loss")
        table.cursor_type = "row"
        self._workers: dict[str, PingWorker] = {}
        self._row_keys: dict[str, object] = {}

        gateway = self._detect_gateway()
        if gateway:
            self._start_worker(gateway)
        self._start_worker("8.8.8.8")

    def on_unmount(self) -> None:
        for w in self._workers.values():
            w.stop()

    def _detect_gateway(self) -> str:
        try:
            route = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m = re.search(r'via (\S+)', route)
            return m.group(1) if m else ''
        except Exception:
            return ''

    def _start_worker(self, host: str) -> None:
        if host in self._workers:
            return
        table = self.query_one(DataTable)
        rk = table.add_row(host, '...', '—', '—', '—', '—', '—', key=host)
        self._row_keys[host] = rk
        worker = PingWorker(host, interval=1.0, on_result=self._on_ping_result)
        self._workers[host] = worker
        worker.start()

    def _on_ping_result(self, worker: PingWorker, ok: bool, rtt: float | None, stats: PingStats) -> None:
        self.app.call_from_thread(self._update_row, worker.host, ok, rtt, stats)

    def _update_row(self, host: str, ok: bool, rtt: float | None, stats: PingStats) -> None:
        if host not in self._row_keys:
            return
        table = self.query_one(DataTable)
        state = '[green]● OK[/green]' if ok else '[red]● KO[/red]'
        rtt_str = f'{rtt:.1f}ms' if rtt is not None else '—'
        avg_str = f'{stats.avg:.1f}ms' if stats.avg is not None else '—'
        rtts = stats.rtts
        min_str = f'{min(rtts):.1f}ms' if rtts else '—'
        max_str = f'{max(rtts):.1f}ms' if rtts else '—'
        loss_str = f'{stats.loss_pct}%'
        rk = self._row_keys[host]
        table.update_cell(rk, "state", state)
        table.update_cell(rk, "rtt", rtt_str)
        table.update_cell(rk, "avg", avg_str)
        table.update_cell(rk, "min", min_str)
        table.update_cell(rk, "max", max_str)
        table.update_cell(rk, "loss", loss_str)

    def action_add_host(self) -> None:
        self.query_one("#input-row").display = True
        self.query_one("#host-input").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        host = event.value.strip()
        if host:
            self._start_worker(host)
        self.query_one("#input-row").display = False
        self.query_one("#host-input").clear()

    def action_remove_host(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row < 0:
            return
        try:
            row_data = table.get_row_at(table.cursor_row)
            host = str(row_data[0])
        except Exception:
            return
        if host in self._workers:
            self._workers[host].stop()
            del self._workers[host]
        if host in self._row_keys:
            table.remove_row(self._row_keys[host])
            del self._row_keys[host]
