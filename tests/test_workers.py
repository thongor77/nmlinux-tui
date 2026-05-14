from nmlinux_tui.workers.net_info import _parse_gateway, _parse_ipv4, _parse_ipv6


def test_parse_gateway_normal():
    output = "default via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.5 metric 100"
    gw, iface = _parse_gateway(output)
    assert gw == "192.168.1.1"
    assert iface == "eth0"


def test_parse_gateway_empty():
    gw, iface = _parse_gateway("")
    assert gw == "—"
    assert iface == ""


def test_parse_ipv4_normal():
    output = "2: eth0    inet 192.168.1.5/24 brd 192.168.1.255 scope global eth0"
    assert _parse_ipv4(output) == "192.168.1.5"


def test_parse_ipv4_empty():
    assert _parse_ipv4("") == "—"


def test_parse_ipv6_normal():
    output = "    inet6 2001:db8::1/64 scope global dynamic"
    assert _parse_ipv6(output) == "2001:db8::1"


def test_parse_ipv6_empty():
    assert _parse_ipv6("") == "—"


from nmlinux_tui.workers.wifi_scan import _parse_terse, signal_bars, pct_to_dbm


def test_parse_terse_simple():
    assert _parse_terse("a:b:c") == ["a", "b", "c"]


def test_parse_terse_escaped_colon():
    line = r"*:MyNetwork:AA\:BB\:CC\:DD\:EE\:FF:6:2437 MHz:72:WPA2"
    parts = _parse_terse(line)
    assert parts[0] == "*"
    assert parts[1] == "MyNetwork"
    assert parts[2] == "AA:BB:CC:DD:EE:FF"
    assert parts[5] == "72"


def test_signal_bars_full():
    assert signal_bars(100) == "████████"


def test_signal_bars_empty():
    assert signal_bars(0) == "▒▒▒▒▒▒▒▒"


def test_signal_bars_half():
    result = signal_bars(50)
    assert len(result) == 8
    assert result.count('█') == 4


def test_pct_to_dbm_max():
    assert pct_to_dbm(100) == -50


def test_pct_to_dbm_min():
    assert pct_to_dbm(0) == -100


def test_pct_to_dbm_mid():
    assert pct_to_dbm(70) == -65


from nmlinux_tui.workers.ping_worker import _parse_ping_rtt, PingStats


def test_parse_ping_rtt_found():
    output = "64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=12.3 ms"
    assert _parse_ping_rtt(output) == 12.3


def test_parse_ping_rtt_integer():
    output = "64 bytes from 8.8.8.8: icmp_seq=1 ttl=57 time=18 ms"
    assert _parse_ping_rtt(output) == 18.0


def test_parse_ping_rtt_not_found():
    assert _parse_ping_rtt("Request timeout for icmp_seq 1") is None


def test_ping_stats_avg():
    stats = PingStats(sent=3, received=3, rtts=[10.0, 20.0, 30.0])
    assert stats.avg == 20.0


def test_ping_stats_avg_empty():
    assert PingStats().avg is None


def test_ping_stats_loss_25pct():
    stats = PingStats(sent=4, received=3, rtts=[])
    assert stats.loss_pct == 25


def test_ping_stats_loss_zero():
    assert PingStats().loss_pct == 0


from nmlinux_tui.workers.ip_scan import parse_cidr, _ping_host


def test_parse_cidr_slash30():
    hosts = parse_cidr("192.168.1.0/30")
    assert isinstance(hosts, list)
    assert "192.168.1.1" in hosts
    assert "192.168.1.2" in hosts
    assert len(hosts) == 2


def test_parse_cidr_slash32():
    hosts = parse_cidr("10.0.0.1/32")
    assert isinstance(hosts, list)
    assert hosts == ["10.0.0.1"]


def test_parse_cidr_invalid():
    result = parse_cidr("not-valid")
    assert isinstance(result, str)
    assert "Invalid" in result


def test_parse_cidr_too_large():
    result = parse_cidr("0.0.0.0/0")
    assert isinstance(result, str)
    assert "too large" in result.lower()


def test_ping_host_localhost():
    alive, hostname = _ping_host("127.0.0.1", timeout=1)
    assert alive is True
