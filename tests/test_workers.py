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
