"""
cruhon-shortcuts-data — system group
======================================
Shortcuts for @ip.*, @platform.*, @unicode.*, @binascii.*, and @shlex.*.

Global aliases (source rewrites)
─────────────────────────────────
@ip_addr[s]             → @ip.address[s]
@ip_net[s]              → @ip.network[s]
@is_private_ip[s]       → @ip.is_private[s]
@ip_version[s]          → @ip.version[s]
@ip_hosts[cidr]         → @ip.hosts[cidr]
@ip_in[cidr; addr]      → @ip.contains[cidr; addr]
@os_name[]              → @platform.system[]
@py_version[]           → @platform.python_version[]
@machine[]              → @platform.machine[]
@hostname[]             → @platform.node[]
@char_name[c]           → @unicode.name[c]
@char_lookup[name]      → @unicode.lookup[name]
@strip_accents[s]       → @unicode.strip_accents[s]
@hexlify[data]          → @binascii.hexlify[data]
@unhexlify[hex]         → @binascii.unhexlify[hex]
@sh_split[cmd]          → @shlex.split[cmd]
@sh_quote[s]            → @shlex.quote[s]
@sh_join[tokens]        → @shlex.join[tokens]

Namespace method aliases
─────────────────────────
@ip.addr[s]             → @ip.address[s]
@ip.net[s]              → @ip.network[s]
@ip.private[s]          → @ip.is_private[s]
@ip.count[cidr]         → @ip.num_addresses[cidr]
@platform.os[]          → @platform.system[]
@platform.py[]          → @platform.python_version[]
@unicode.no_accents[s]  → @unicode.strip_accents[s]
@binascii.hex[data]     → @binascii.hexlify[data]
@binascii.from_hex[h]   → @binascii.unhexlify[h]
@shlex.parse[cmd]       → @shlex.split[cmd]

New methods (via api.lib_call)
───────────────────────────────
@ip.is_ipv4[s]          → True if the address is IPv4
@ip.is_ipv6[s]          → True if the address is IPv6
@ip.first_host[cidr]    → first usable host address in a network
@platform.summary[]     → "{system} {release} / Python {py_version}"
@binascii.hex_spaced[d] → space-separated hex pairs ("41 42")
"""
from __future__ import annotations

_IP = "__import__('ipaddress')"
_PF = "__import__('platform')"
_BA = "__import__('binascii')"


GLOBAL_REWRITES: dict[str, str] = {
    "@ip_addr[":        "@ip.address[",
    "@ip_net[":         "@ip.network[",
    "@is_private_ip[":  "@ip.is_private[",
    "@ip_version[":     "@ip.version[",
    "@ip_hosts[":       "@ip.hosts[",
    "@ip_in[":          "@ip.contains[",
    "@os_name[":        "@platform.system[",
    "@py_version[":     "@platform.python_version[",
    "@machine[":        "@platform.machine[",
    "@hostname[":       "@platform.node[",
    "@char_name[":      "@unicode.name[",
    "@char_lookup[":    "@unicode.lookup[",
    "@strip_accents[":  "@unicode.strip_accents[",
    "@hexlify[":        "@binascii.hexlify[",
    "@unhexlify[":      "@binascii.unhexlify[",
    "@sh_split[":       "@shlex.split[",
    "@sh_quote[":       "@shlex.quote[",
    "@sh_join[":        "@shlex.join[",
}

METHOD_ALIASES: dict[str, str] = {
    "@ip.addr[":           "@ip.address[",
    "@ip.net[":            "@ip.network[",
    "@ip.private[":        "@ip.is_private[",
    "@ip.count[":          "@ip.num_addresses[",
    "@platform.os[":       "@platform.system[",
    "@platform.py[":       "@platform.python_version[",
    "@unicode.no_accents[":"@unicode.strip_accents[",
    "@binascii.hex[":      "@binascii.hexlify[",
    "@binascii.from_hex[": "@binascii.unhexlify[",
    "@shlex.parse[":       "@shlex.split[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("ip", "is_ipv4", lambda a: (
        f"({_IP}.ip_address({a[0]}).version == 4)" if a else "False"
    ))

    api.lib_call("ip", "is_ipv6", lambda a: (
        f"({_IP}.ip_address({a[0]}).version == 6)" if a else "False"
    ))

    api.lib_call("ip", "first_host", lambda a: (
        f"next(iter({_IP}.ip_network({a[0]}, strict=False).hosts()), None)"
        if a else "None"
    ))

    api.lib_call("platform", "summary", lambda a: (
        f"({_PF}.system() + ' ' + {_PF}.release() + ' / Python ' + {_PF}.python_version())"
    ))

    api.lib_call("binascii", "hex_spaced", lambda a: (
        f"(lambda _h: ' '.join(_h[_i:_i+2] for _i in range(0, len(_h), 2)))("
        f"{_BA}.hexlify({a[0]}.encode('utf-8') if isinstance({a[0]}, str) else {a[0]}).decode('ascii'))"
        if a else "''"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
