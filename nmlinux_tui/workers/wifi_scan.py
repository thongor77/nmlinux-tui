from __future__ import annotations

import subprocess


def _parse_terse(line: str) -> list[str]:
    parts: list[str] = []
    current = ''
    it = iter(line)
    for ch in it:
        if ch == '\\':
            nxt = next(it, '')
            current += nxt
        elif ch == ':':
            parts.append(current)
            current = ''
        else:
            current += ch
    parts.append(current)
    return parts


def signal_bars(signal_pct: int) -> str:
    filled = max(0, min(8, round(signal_pct / 100 * 8)))
    return '█' * filled + '▒' * (8 - filled)


def pct_to_dbm(pct: int) -> int:
    return (pct // 2) - 100


def wifi_scan() -> dict:
    result: dict = {'iface': '—', 'connected_ssid': '', 'ssids': []}

    wifi_iface = '—'
    try:
        raw = subprocess.run(
            ['nmcli', '-t', '-f', 'DEVICE,TYPE', 'dev'],
            capture_output=True, text=True, timeout=4,
        ).stdout
        for line in raw.splitlines():
            parts = _parse_terse(line)
            if len(parts) >= 2 and parts[1] == 'wifi':
                wifi_iface = parts[0]
                break
    except Exception:
        pass

    result['iface'] = wifi_iface
    if wifi_iface == '—':
        return result

    try:
        subprocess.run(
            ['nmcli', 'dev', 'wifi', 'rescan', 'ifname', wifi_iface],
            capture_output=True, timeout=6,
        )
    except Exception:
        pass

    try:
        raw = subprocess.run(
            ['nmcli', '-t', '-f', 'IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY',
             'dev', 'wifi', 'list', 'ifname', wifi_iface],
            capture_output=True, text=True, timeout=8,
        ).stdout
        seen: set[str] = set()
        ssids: list[dict] = []
        for line in raw.splitlines():
            parts = _parse_terse(line)
            if len(parts) < 7:
                continue
            in_use, ssid, bssid, chan, freq, signal, security = parts[:7]
            if not ssid:
                ssid = '(hidden)'
            if bssid in seen:
                continue
            seen.add(bssid)
            try:
                pct = int(signal)
            except ValueError:
                pct = 0
            ssids.append({
                'connected': in_use == '*',
                'ssid': ssid,
                'bssid': bssid,
                'chan': chan,
                'freq': freq,
                'signal_pct': pct,
                'signal_dbm': pct_to_dbm(pct),
                'bar': signal_bars(pct),
                'security': security or 'Open',
            })
            if in_use == '*':
                result['connected_ssid'] = ssid
        ssids.sort(key=lambda x: (not x['connected'], -x['signal_pct']))
        result['ssids'] = ssids
    except Exception:
        pass

    return result
