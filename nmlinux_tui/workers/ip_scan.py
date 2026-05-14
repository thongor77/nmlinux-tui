from __future__ import annotations

import ipaddress
import socket
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed


def _ping_host(ip: str, timeout: int = 1) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            ['ping', '-c', '1', '-W', str(timeout), ip],
            capture_output=True, text=True, timeout=timeout + 2,
        )
        if proc.returncode == 0:
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except Exception:
                hostname = ''
            return True, hostname
    except Exception:
        pass
    return False, ''


def parse_cidr(cidr: str) -> list[str] | str:
    cidr = cidr.strip()
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        # Check size before enumerating hosts
        num_hosts = net.num_addresses
        if net.num_addresses > 2:
            num_hosts -= 2  # Exclude network and broadcast addresses
        if num_hosts > 65536:
            return f"Network too large ({num_hosts} hosts, max 65536)"
        hosts = list(net.hosts()) or [net.network_address]
        return [str(h) for h in hosts]
    except ValueError:
        return f"Invalid CIDR: {cidr!r}"


def scan_cidr(
    cidr: str,
    on_result: Callable[[str, str], None],
    on_progress: Callable[[int, int], None],
    on_done: Callable[[], None],
    n_threads: int = 50,
    timeout: int = 1,
) -> None:
    hosts = parse_cidr(cidr)
    if isinstance(hosts, str):
        on_done()
        return

    total = len(hosts)
    done = 0

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futures = {pool.submit(_ping_host, ip, timeout): ip for ip in hosts}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                alive, hostname = future.result()
            except Exception:
                alive, hostname = False, ''
            done += 1
            on_progress(done, total)
            if alive:
                on_result(ip, hostname)

    on_done()
