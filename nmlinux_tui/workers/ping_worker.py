from __future__ import annotations

import re
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field


def _parse_ping_rtt(ping_output: str) -> float | None:
    m = re.search(r'time=(\d+\.?\d*)', ping_output)
    return float(m.group(1)) if m else None


@dataclass
class PingStats:
    sent: int = 0
    received: int = 0
    rtts: list[float] = field(default_factory=list)

    @property
    def avg(self) -> float | None:
        return sum(self.rtts) / len(self.rtts) if self.rtts else None

    @property
    def loss_pct(self) -> int:
        if self.sent == 0:
            return 0
        return round((self.sent - self.received) / self.sent * 100)

    @property
    def last_rtt(self) -> float | None:
        return self.rtts[-1] if self.rtts else None


ResultCallback = Callable[['PingWorker', bool, float | None, PingStats], None]


class PingWorker(threading.Thread):
    def __init__(self, host: str, interval: float, on_result: ResultCallback) -> None:
        super().__init__(daemon=True)
        self.host = host
        self._interval = interval
        self._on_result = on_result
        self._running = True
        self.stats = PingStats()

    def run(self) -> None:
        while self._running:
            t0 = time.monotonic()
            self.stats.sent += 1
            try:
                proc = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', self.host],
                    capture_output=True, text=True, timeout=5,
                )
                if proc.returncode == 0:
                    rtt = _parse_ping_rtt(proc.stdout)
                    if rtt is not None:
                        self.stats.rtts = self.stats.rtts[-49:] + [rtt]
                    self.stats.received += 1
                    self._on_result(self, True, rtt, self.stats)
                else:
                    self._on_result(self, False, None, self.stats)
            except Exception:
                self._on_result(self, False, None, self.stats)

            elapsed = time.monotonic() - t0
            deadline = time.monotonic() + max(0.0, self._interval - elapsed)
            while self._running and time.monotonic() < deadline:
                time.sleep(0.05)

    def stop(self) -> None:
        self._running = False
