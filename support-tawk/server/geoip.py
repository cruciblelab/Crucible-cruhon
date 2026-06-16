from __future__ import annotations
"""Basit, bağımlılıksız IP coğrafi konum çözümleyici.

ip-api.com ücretsiz uç noktasını kullanır. Ağ erişimi yoksa veya özel/
yerel IP ise sessizce boş döner. Sonuçlar bellek içinde önbelleğe alınır.
"""
import json
import urllib.request
from typing import Dict

_cache: Dict[str, dict] = {}

_PRIVATE_PREFIXES = ("10.", "192.168.", "127.", "0.", "172.16.", "172.17.",
                     "172.18.", "172.19.", "172.20.", "172.21.", "172.22.",
                     "172.23.", "172.24.", "172.25.", "172.26.", "172.27.",
                     "172.28.", "172.29.", "172.30.", "172.31.", "::1", "fc",
                     "fd", "fe80")


def _is_private(ip: str) -> bool:
    if not ip or ip == "unknown":
        return True
    return ip.startswith(_PRIVATE_PREFIXES)


def lookup(ip: str) -> dict:
    """{'country': str, 'city': str} döner. Hata/özel IP'de boş alanlar."""
    if _is_private(ip):
        return {"country": "", "city": ""}
    if ip in _cache:
        return _cache[ip]
    result = {"country": "", "city": ""}
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,city"
        req = urllib.request.Request(url, headers={"User-Agent": "support-tawk"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if data.get("status") == "success":
            result = {
                "country": data.get("country", "") or "",
                "city": data.get("city", "") or "",
            }
    except Exception:
        pass
    _cache[ip] = result
    return result
