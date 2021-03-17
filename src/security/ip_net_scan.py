import ipaddress
import re
import socket

port_range_pattern = re.compile("([0-9]+)-([0-9]+)")

port_min = 0
port_max = 65535


def ip_port_scan(ip_addr: str, port_range: str) -> list:
    try:
        ip_address_obj = ipaddress.ip_address(ip_addr)  # noqa: F841
    except Exception:
        raise ValueError("Invalid IP!")

    port_range_valid = port_range_pattern.search(port_range.replace(" ", ""))
    if port_range_valid:
        port_min = int(port_range_valid.group(1))
        port_max = int(port_range_valid.group(2))
    else:
        raise ValueError("Invalid Port range!")

    open_ports = []

    for port in range(port_min, port_max + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                sock.connect((ip_addr, port))
                open_ports.append(port)
        except Exception:
            pass

    return open_ports
