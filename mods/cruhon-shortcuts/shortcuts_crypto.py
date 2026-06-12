"""
cruhon-shortcuts — crypto group
=================================
Shortcuts for @crypto.* and @base64.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@uuid[]                 → @crypto.uuid[]
@uuid4[]                → @crypto.uuid[]
@uuid1[]                → @crypto.uuid1[]
@token[n]               → @crypto.token[n]
@token_url[n]           → @crypto.token_url[n]
@token_bytes[n]         → @crypto.token_bytes[n]
@sha256[data]           → @crypto.sha256[data]
@sha512[data]           → @crypto.sha512[data]
@sha1[data]             → @crypto.sha1[data]
@md5[data]              → @crypto.md5[data]
@blake2b[data]          → @crypto.blake2b[data]
@hmac_sign[k; d; alg]   → @crypto.hmac[k; d; alg]
@hex_encode[data]       → @crypto.hex_encode[data]
@hex_decode[data]       → @crypto.hex_decode[data]
@b64enc[data]           → @base64.encode[data]
@b64dec[data]           → @base64.decode[data]
@b64url_enc[data]       → @base64.urlsafe_encode[data]
@b64url_dec[data]       → @base64.urlsafe_decode[data]
@b32enc[data]           → @base64.b32encode[data]
@b32dec[data]           → @base64.b32decode[data]
@b16enc[data]           → @base64.b16encode[data]
@b16dec[data]           → @base64.b16decode[data]

Namespace method aliases
─────────────────────────
@crypto.id[]            → @crypto.uuid[]
@crypto.new_uuid[]      → @crypto.uuid[]
@base64.enc[data]       → @base64.encode[data]
@base64.dec[data]       → @base64.decode[data]
@base64.enc_url[data]   → @base64.urlsafe_encode[data]
@base64.dec_url[data]   → @base64.urlsafe_decode[data]

New methods (via api.lib_call)
───────────────────────────────
@crypto.hash_all[alg; d]    → hash with named algorithm (sha256, md5, etc.)
@crypto.fingerprint[data]   → SHA-256 fingerprint (first 16 chars)
@crypto.short_id[]          → 8-char URL-safe random ID
@crypto.nano_id[n]          → URL-safe random ID of length n (default 21)
@crypto.cuid[]              → collision-resistant ID (timestamp + random hex)
@crypto.checksum[data]      → CRC32 hex checksum
@crypto.xor[data; key]      → XOR-cipher bytes (returns hex)
@crypto.is_hash[s; alg]     → check if string looks like hash of given algo
@crypto.compare_hashes[a;b] → constant-time comparison (timing-safe)
@base64.encode_str[s]       → encode UTF-8 string to base64 string
@base64.decode_str[s]       → decode base64 string to UTF-8 string
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@uuid[":         "@crypto.uuid[",
    "@uuid4[":        "@crypto.uuid[",
    "@uuid1[":        "@crypto.uuid1[",
    "@token[":        "@crypto.token[",
    "@token_url[":    "@crypto.token_url[",
    "@token_bytes[":  "@crypto.token_bytes[",
    "@sha256[":       "@crypto.sha256[",
    "@sha512[":       "@crypto.sha512[",
    "@sha1[":         "@crypto.sha1[",
    "@md5[":          "@crypto.md5[",
    "@blake2b[":      "@crypto.blake2b[",
    "@hmac_sign[":    "@crypto.hmac[",
    "@hex_encode[":   "@crypto.hex_encode[",
    "@hex_decode[":   "@crypto.hex_decode[",
    "@b64enc[":       "@base64.encode[",
    "@b64dec[":       "@base64.decode[",
    "@b64url_enc[":   "@base64.urlsafe_encode[",
    "@b64url_dec[":   "@base64.urlsafe_decode[",
    "@b32enc[":       "@base64.b32encode[",
    "@b32dec[":       "@base64.b32decode[",
    "@b16enc[":       "@base64.b16encode[",
    "@b16dec[":       "@base64.b16decode[",
}

METHOD_ALIASES: dict[str, str] = {
    "@crypto.id[":       "@crypto.uuid[",
    "@crypto.new_uuid[": "@crypto.uuid[",
    "@base64.enc[":      "@base64.encode[",
    "@base64.dec[":      "@base64.decode[",
    "@base64.enc_url[":  "@base64.urlsafe_encode[",
    "@base64.dec_url[":  "@base64.urlsafe_decode[",
}

_HL  = "__import__('hashlib')"
_SC  = "__import__('secrets')"
_B64 = "__import__('base64')"
_ST  = "__import__('struct')"
_ZL  = "__import__('zlib')"
_HM  = "__import__('hmac')"
_TM  = "__import__('time')"


def _new_lib_calls(api) -> None:

    api.lib_call("crypto", "hash_all", lambda a: (
        f"{_HL}.new({a[0]}, {a[1]}.encode() if isinstance({a[1]}, str) else {a[1]}).hexdigest()"
        if len(a) > 1 else
        f"''"
    ))

    api.lib_call("crypto", "fingerprint", lambda a: (
        f"{_HL}.sha256({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}).hexdigest()[:16]"
        if a else
        f"''"
    ))

    api.lib_call("crypto", "short_id", lambda a: (
        f"{_SC}.token_urlsafe(6)"
    ))

    api.lib_call("crypto", "nano_id", lambda a: (
        f"{_SC}.token_urlsafe({a[0]})"
        if a else
        f"{_SC}.token_urlsafe(21)"
    ))

    api.lib_call("crypto", "cuid", lambda a: (
        f"(lambda _t, _r: f'c{{_t:x}}{{_r}}')"
        f"(int({_TM}.time() * 1000), {_SC}.token_hex(8))"
    ))

    api.lib_call("crypto", "checksum", lambda a: (
        f"format({_ZL}.crc32({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}) & 0xFFFFFFFF, '08x')"
        if a else
        f"'00000000'"
    ))

    api.lib_call("crypto", "xor", lambda a: (
        f"bytes(b ^ k for b, k in zip("
        f"({a[0]}.encode() if isinstance({a[0]}, str) else {a[0]}), "
        f"({a[1]} * 9999)[:len({a[0]})])).hex()"
        if len(a) > 1 else
        f"''"
    ))

    api.lib_call("crypto", "is_hash", lambda a: (
        f"(len({a[0]}) == {{'md5': 32, 'sha1': 40, 'sha256': 64, 'sha512': 128}}.get({a[1]}, -1) "
        f"and all(c in '0123456789abcdef' for c in str({a[0]}).lower()))"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("crypto", "compare_hashes", lambda a: (
        f"{_HM}.compare_digest(str({a[0]}), str({a[1]}))"
        if len(a) > 1 else
        f"False"
    ))

    api.lib_call("base64", "encode_str", lambda a: (
        f"{_B64}.b64encode({a[0]}.encode('utf-8')).decode('ascii')"
        if a else
        f"''"
    ))

    api.lib_call("base64", "decode_str", lambda a: (
        f"{_B64}.b64decode({a[0]}).decode('utf-8')"
        if a else
        f"''"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
