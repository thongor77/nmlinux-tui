from __future__ import annotations

import json
import re
import socket
import subprocess
import urllib.request


def _parse_gateway(route_output: str) -> tuple[str, str]:
    m_gw = re.search(r'via (\S+)', route_output)
    m_if = re.search(r'dev (\S+)', route_output)
    return (
        m_gw.group(1) if m_gw else '—',
        m_if.group(1) if m_if else '',
    )


def _parse_ipv4(addr_output: str) -> str:
    m = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', addr_output)
    return m.group(1) if m else '—'


def _parse_ipv6(addr_output: str) -> str:
    m = re.search(r'inet6 (\S+)/', addr_output)
    return m.group(1) if m else '—'


def collect_local() -> dict:
    out: dict = {}

    try:
        out['hostname'] = socket.gethostname()
    except Exception:
        out['hostname'] = '—'

    try:
        route = subprocess.run(
            ['ip', 'route', 'show', 'default'],
            capture_output=True, text=True, timeout=3,
        ).stdout
        out['gateway'], out['iface'] = _parse_gateway(route)
    except Exception:
        out['gateway'] = '—'
        out['iface'] = ''

    iface = out.get('iface', '')

    try:
        cmd = ['ip', '-4', 'addr', 'show'] + ([iface] if iface else [])
        raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
        out['local_ipv4'] = _parse_ipv4(raw)
    except Exception:
        out['local_ipv4'] = '—'

    try:
        cmd = ['ip', '-6', 'addr', 'show', 'scope', 'global'] + \
              (['dev', iface] if iface else [])
        raw = subprocess.run(cmd, capture_output=True, text=True, timeout=3).stdout
        out['local_ipv6'] = _parse_ipv6(raw)
    except Exception:
        out['local_ipv6'] = '—'

    try:
        req = urllib.request.Request(
            'http://ip-api.com/json/?fields=query',
            headers={'User-Agent': 'nmlinux-tui/0.1'},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            out['public_ip'] = data.get('query', '—')
    except Exception:
        out['public_ip'] = '—'

    return out
