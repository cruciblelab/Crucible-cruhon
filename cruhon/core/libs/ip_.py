"""
IP address & network utilities for Cruhon — @ip.*

Wraps Python's `ipaddress` module: parse and classify IPv4/IPv6 addresses
and networks, enumerate hosts, and test membership. No `@import` needed.

━━━ PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ip.address[s]             → IPv4Address / IPv6Address object
  @ip.network[s]             → IPv4Network / IPv6Network (strict=False)
  @ip.interface[s]           → IPv4Interface / IPv6Interface

━━━ CLASSIFY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ip.version[s]             → 4 or 6
  @ip.is_private[s]          → True for private ranges (10/8, 192.168/16, …)
  @ip.is_global[s]           → True for globally-routable addresses
  @ip.is_loopback[s]         → True for 127.0.0.1 / ::1
  @ip.is_multicast[s]        → True for multicast addresses

━━━ NETWORK ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ip.hosts[cidr]            → list of usable host addresses in a network
  @ip.num_addresses[cidr]    → total address count of the network
  @ip.netmask[cidr]          → network mask address
  @ip.broadcast[cidr]        → broadcast address
  @ip.network_address[cidr]  → network (base) address
  @ip.contains[cidr; addr]   → True if the network contains the address
  @ip.supernet[cidr]         → the immediate parent network

━━━ CONVERT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ip.to_int[s]              → integer value of the address
  @ip.from_int[n]            → address from an integer
"""
from ..registry import register_lib, register_lib_call

_IP = "__import__('ipaddress')"


def register():
    register_lib("ip", "ipaddress")

    # ── PARSE ─────────────────────────────────────────────────
    register_lib_call("ip", "address",
        lambda a: f"{_IP}.ip_address({a[0]})" if a else "None")

    register_lib_call("ip", "network",
        lambda a: f"{_IP}.ip_network({a[0]}, strict=False)" if a else "None")

    register_lib_call("ip", "interface",
        lambda a: f"{_IP}.ip_interface({a[0]})" if a else "None")

    # ── CLASSIFY ──────────────────────────────────────────────
    register_lib_call("ip", "version",
        lambda a: f"{_IP}.ip_address({a[0]}).version" if a else "0")

    register_lib_call("ip", "is_private",
        lambda a: f"{_IP}.ip_address({a[0]}).is_private" if a else "False")

    register_lib_call("ip", "is_global",
        lambda a: f"{_IP}.ip_address({a[0]}).is_global" if a else "False")

    register_lib_call("ip", "is_loopback",
        lambda a: f"{_IP}.ip_address({a[0]}).is_loopback" if a else "False")

    register_lib_call("ip", "is_multicast",
        lambda a: f"{_IP}.ip_address({a[0]}).is_multicast" if a else "False")

    # ── NETWORK ───────────────────────────────────────────────
    register_lib_call("ip", "hosts",
        lambda a: f"list({_IP}.ip_network({a[0]}, strict=False).hosts())" if a else "[]")

    register_lib_call("ip", "num_addresses",
        lambda a: f"{_IP}.ip_network({a[0]}, strict=False).num_addresses" if a else "0")

    register_lib_call("ip", "netmask",
        lambda a: f"{_IP}.ip_network({a[0]}, strict=False).netmask" if a else "None")

    register_lib_call("ip", "broadcast",
        lambda a: f"{_IP}.ip_network({a[0]}, strict=False).broadcast_address" if a else "None")

    register_lib_call("ip", "network_address",
        lambda a: f"{_IP}.ip_network({a[0]}, strict=False).network_address" if a else "None")

    register_lib_call("ip", "contains",
        lambda a: (
            f"({_IP}.ip_address({a[1]}) in {_IP}.ip_network({a[0]}, strict=False))"
            if len(a) > 1 else "False"
        ))

    register_lib_call("ip", "supernet",
        lambda a: f"{_IP}.ip_network({a[0]}, strict=False).supernet()" if a else "None")

    # ── CONVERT ───────────────────────────────────────────────
    register_lib_call("ip", "to_int",
        lambda a: f"int({_IP}.ip_address({a[0]}))" if a else "0")

    register_lib_call("ip", "from_int",
        lambda a: f"{_IP}.ip_address(int({a[0]}))" if a else "None")
