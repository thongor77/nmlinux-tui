# nmlinux-tui

Terminal network monitor for Linux — btop-style, no GUI required. Works over SSH on any terminal.

Built with [Textual](https://github.com/Textualize/textual) (Python), single external dependency.

## Screenshot

![Dashboard](Screenshots/current.png)

## Features

| Screen | Description |
|--------|-------------|
| **Dashboard** | Left: local network info, interfaces, Wi-Fi · Right: live ping monitor + IP scanner |
| **Interfaces** | Live DataTable (`ip -j addr`) — name, state, IPv4/IPv6, MAC, refresh every 5s |
| **Wi-Fi** | nmcli scan with signal bars `████▒▒▒▒` and dBm, rescan with `r` |
| **Ping Monitor** | Multi-host live ping — gateway + 8.8.8.8 preloaded, add/remove hosts |
| **IP Scanner** | CIDR input, streaming results, auto-detects local subnet |

## Requirements

- Python 3.11+
- Linux with `ip`, `ping`, `nmcli` available
- No root required

## Install

```bash
git clone https://github.com/thongor77/nmlinux-tui.git
cd nmlinux-tui
python -m venv venv
venv/bin/pip install -e .
```

## Run

```bash
venv/bin/python -m nmlinux_tui
# or after install:
nmlinux-tui
```

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `d` | Dashboard |
| `1` | Interfaces |
| `2` | Wi-Fi |
| `3` | Ping Monitor |
| `4` | IP Scanner |
| `Esc` | Back to dashboard |
| `q` | Quit |

**Ping Monitor extras:** `a` add host · `Del` remove host  
**Wi-Fi extras:** `r` rescan

## Project structure

```
nmlinux_tui/
  app.py              — main app, routing
  workers/
    net_info.py       — local network info (IP, gateway, public IP)
    wifi_scan.py      — nmcli wrapper, signal bars
    ping_worker.py    — continuous ping thread per host
    ip_scan.py        — parallel CIDR scanner
  screens/
    dashboard.py      — main dashboard (all-in-one view)
    interfaces.py     — network interfaces screen
    wifi.py           — Wi-Fi scan screen
    ping.py           — ping monitor screen
    ip_scanner.py     — IP scanner screen
tests/
  test_workers.py     — 27 unit tests on workers
```

## Tests

```bash
venv/bin/pytest
```
