"""
Crypto / security stdlib wrappers for Cruhon — @crypto.*

Covers hashlib / hmac / secrets / base64 / uuid so a non-coder can hash
passwords, generate tokens, encode data and create UUIDs without knowing
any of those module names.

━━━ HASH ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @crypto.md5[s]               → hex digest
  @crypto.sha1[s]              → hex digest
  @crypto.sha256[s]            → hex digest
  @crypto.sha512[s]            → hex digest
  @crypto.hash[algo; s]        → hex digest with any hashlib algo name
  @crypto.hash_bytes[algo; b]  → hash raw bytes input

━━━ HMAC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @crypto.hmac[key; msg]           → HMAC-SHA256 hex digest
  @crypto.hmac[key; msg; algo]     → HMAC with custom algo ("sha1", "sha512" …)
  @crypto.compare[a; b]            → constant-time equality (safe for secrets)

━━━ TOKENS / RANDOM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @crypto.token[n]             → n-byte random hex string (default 32)
  @crypto.token_url[n]         → URL-safe random token (default 32)
  @crypto.token_bytes[n]       → raw random bytes (default 32)
  @crypto.random_int[n]        → cryptographically secure int in [0, n)
  @crypto.random_bytes[n]      → os.urandom(n)

━━━ UUID ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @crypto.uuid[]               → UUID4 string
  @crypto.uuid1[]              → UUID1 string (host + time)
  @crypto.uuid3[ns; name]      → UUID3 (MD5 namespace hash)
  @crypto.uuid5[ns; name]      → UUID5 (SHA1 namespace hash)

━━━ BASE64 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @crypto.b64_encode[s]        → standard base64 string
  @crypto.b64_decode[s]        → decoded string
  @crypto.b64url_encode[s]     → URL-safe base64 string
  @crypto.b64url_decode[s]     → decoded string
  @crypto.hex_encode[b]        → bytes → hex string
  @crypto.hex_decode[s]        → hex string → bytes
"""
from ..registry import register_lib, register_lib_call

_HL  = "__import__('hashlib')"
_HM  = "__import__('hmac')"
_SC  = "__import__('secrets')"
_B64 = "__import__('base64')"
_UUID = "__import__('uuid')"
_OS  = "__import__('os')"


def _to_bytes(expr: str) -> str:
    return f"(({expr}).encode() if isinstance({expr}, str) else {expr})"


def register():
    register_lib("crypto", None)

    # ── HASH ─────────────────────────────────────────────────
    for algo in ("md5", "sha1", "sha256", "sha512"):
        register_lib_call("crypto", algo,
            (lambda a: lambda args: f"{_HL}.{a}({_to_bytes(args[0])}).hexdigest()")(algo))

    register_lib_call("crypto", "hash",
        lambda a: f"{_HL}.new({a[0]}, {_to_bytes(a[1])}).hexdigest()")

    _empty = 'b""'
    register_lib_call("crypto", "hash_bytes",
        lambda a: f"{_HL}.new({a[0]}, {a[1] if len(a)>1 else _empty}).hexdigest()")

    # ── HMAC ─────────────────────────────────────────────────
    register_lib_call("crypto", "hmac",
        lambda a: (
            f"{_HM}.new({_to_bytes(a[0])}, {_to_bytes(a[1])}, getattr({_HL}, {a[2]})).hexdigest()"
            if len(a) > 2 else
            f"{_HM}.new({_to_bytes(a[0])}, {_to_bytes(a[1])}, {_HL}.sha256).hexdigest()"
        ))

    register_lib_call("crypto", "compare",
        lambda a: f"{_HM}.compare_digest({_to_bytes(a[0])}, {_to_bytes(a[1])})")

    # ── TOKENS / RANDOM ──────────────────────────────────────
    register_lib_call("crypto", "token",
        lambda a: f"{_SC}.token_hex({a[0] if a else 32})")

    register_lib_call("crypto", "token_url",
        lambda a: f"{_SC}.token_urlsafe({a[0] if a else 32})")

    register_lib_call("crypto", "token_bytes",
        lambda a: f"{_SC}.token_bytes({a[0] if a else 32})")

    register_lib_call("crypto", "random_int",
        lambda a: f"{_SC}.randbelow({a[0] if a else 100})")

    register_lib_call("crypto", "random_bytes",
        lambda a: f"{_OS}.urandom({a[0] if a else 16})")

    # ── UUID ─────────────────────────────────────────────────
    register_lib_call("crypto", "uuid",
        lambda a: f"str({_UUID}.uuid4())")

    register_lib_call("crypto", "uuid1",
        lambda a: f"str({_UUID}.uuid1())")

    register_lib_call("crypto", "uuid3",
        lambda a: f"str({_UUID}.uuid3({_UUID}.NAMESPACE_DNS, {a[1]}))" if len(a) > 1
                  else f"str({_UUID}.uuid3({_UUID}.NAMESPACE_DNS, ''))")

    register_lib_call("crypto", "uuid5",
        lambda a: f"str({_UUID}.uuid5({_UUID}.NAMESPACE_DNS, {a[1]}))" if len(a) > 1
                  else f"str({_UUID}.uuid5({_UUID}.NAMESPACE_DNS, ''))")

    # ── BASE64 ───────────────────────────────────────────────
    register_lib_call("crypto", "b64_encode",
        lambda a: f"{_B64}.b64encode({_to_bytes(a[0])}).decode()")

    register_lib_call("crypto", "b64_decode",
        lambda a: f"{_B64}.b64decode({a[0]}).decode('utf-8', errors='replace')")

    register_lib_call("crypto", "b64url_encode",
        lambda a: f"{_B64}.urlsafe_b64encode({_to_bytes(a[0])}).decode()")

    register_lib_call("crypto", "b64url_decode",
        lambda a: f"{_B64}.urlsafe_b64decode({a[0]}).decode('utf-8', errors='replace')")

    register_lib_call("crypto", "hex_encode",
        lambda a: f"{a[0]}.hex() if isinstance({a[0]}, bytes) else {_to_bytes(a[0])}.hex()")

    register_lib_call("crypto", "hex_decode",
        lambda a: f"bytes.fromhex({a[0]})")
