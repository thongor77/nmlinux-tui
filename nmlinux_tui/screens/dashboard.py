from __future__ import annotations

import asyncio
import json
import re
import subprocess

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Static

from nmlinux_tui.workers import net_info as net_info_mod
from nmlinux_tui.workers import wifi_scan as wifi_mod
from nmlinux_tui.workers.ping_worker import PingWorker, PingStats


class DashboardScreen(Screen):
    DEFAULT_CSS = """
    DashboardScreen {
        layout: grid;
        grid-size: 2;
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
        yield Static("PING GATEWAY\n  loading...", id="ping-gw", classes="panel")
        yield Static("WI-FI\n  loading...", id="wifi", classes="panel")
        yield Footer()

    def on_mount(self) -> None:
        self._ping_results: list[str] = []
        self._ping_stats: PingStats | None = None
        self._ping_worker: PingWorker | None = None
        self._ping_gw = '8.8.8.8'

        self.set_interval(3.0, self._refresh_net)
        self.set_interval(3.0, self._refresh_ifaces)
        self.set_interval(10.0, self._refresh_wifi)
        self._start_ping_worker()

    def on_unmount(self) -> None:
        if self._ping_worker:
            self._ping_worker.stop()

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
            for iface in ifaces[:6]:
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

    # ── ping panel ────────────────────────────────────────────────────────────

    def _start_ping_worker(self) -> None:
        try:
            route = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=3,
            ).stdout
            m = re.search(r'via (\S+)', route)
            if m:
                self._ping_gw = m.group(1)
        except Exception:
            pass

        self._ping_worker = PingWorker(
            self._ping_gw, interval=1.0, on_result=self._on_ping_result
        )
        self._ping_worker.start()

    def _on_ping_result(self, worker: PingWorker, ok: bool, rtt: float | None, stats: PingStats) -> None:
        dot = '[green]●[/green]' if ok else '[red]●[/red]'
        rtt_str = f'{rtt:.0f}ms' if rtt is not None else 'N/A'
        self._ping_results = (self._ping_results + [f'{dot} {rtt_str}'])[-3:]
        self._ping_stats = stats
        self.app.call_from_thread(self._update_ping_panel)

    def _update_ping_panel(self) -> None:
        results_str = '  '.join(self._ping_results) if self._ping_results else '...'
        stats = self._ping_stats
        avg_str = f'{stats.avg:.0f}ms' if stats and stats.avg is not None else '—'
        loss_str = f'{stats.loss_pct}%' if stats else '—'
        text = (
            f"[b]PING {self._ping_gw}[/b]\n"
            f"  {results_str}\n"
            f"  avg {avg_str}  loss {loss_str}"
        )
        self.query_one("#ping-gw", Static).update(text)

    # ── wifi panel ────────────────────────────────────────────────────────────

    async def _refresh_wifi(self) -> None:
        data = await asyncio.to_thread(wifi_mod.wifi_scan)
        lines = ["[b]WI-FI[/b]"]
        ssids = data.get('ssids', [])
        if not ssids:
            lines.append("  nmcli non disponible")
        for entry in ssids[:4]:
            star = '★' if entry['connected'] else ' '
            ssid = entry['ssid'][:16]
            lines.append(
                f"  {star} {ssid:<16} {entry['bar']} {entry['signal_dbm']}dBm"
            )
        self.query_one("#wifi", Static).update("\n".join(lines))
