import re
import typing as t

import scapy.all as scapy

# IPv4 Regex
ipv4_regex = re.compile("^(?:[0-9]{1,3}.){3}[0-9]{1,3}/[0-9]*$")


def get_connected_lan_devices(ip_range: str) -> t.Any:
    if ipv4_regex.search(ip_range):
        arp_result = scapy.arping(ip_range)
        return arp_result
    else:
        return None
