"""
Email message building & parsing for Cruhon — @email.*

Wraps Python's `email` package: construct, parse, and inspect MIME
messages. This is the *message* layer — for actually sending mail use
the `@mail.*` namespace (smtplib / imaplib). No `@import` needed.

━━━ BUILD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @email.message[]                    → empty EmailMessage
  @email.make[subject; from; to; body]→ ready-to-send EmailMessage
  @email.set_content[msg; body]       — set the plain-text body
  @email.add_html[msg; html]          — add an HTML alternative part
  @email.set_header[msg; name; value] — set/replace a header
  @email.attach_file[msg; path]       — attach a file from disk

━━━ PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @email.parse[raw_text]              → EmailMessage from a raw string
  @email.parse_bytes[raw_bytes]       → EmailMessage from raw bytes

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @email.subject[msg]                 → Subject header
  @email.sender[msg]                  → From header
  @email.recipients[msg]              → To header
  @email.header[msg; name]            → arbitrary header value
  @email.headers[msg]                 → dict of all headers
  @email.body[msg]                    → plain-text body content
  @email.is_multipart[msg]            → bool
  @email.parts[msg]                   → list of payload parts
  @email.as_string[msg]               → serialize the whole message to text

━━━ ADDRESS UTILITIES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @email.parse_address[s]             → (display_name, email_addr)
  @email.format_address[name; addr]   → "Name <addr>" string
  @email.valid_address[s]             → bool — looks like a valid address
"""
from ..registry import register_lib, register_lib_call

_EM  = "__import__('email.message', fromlist=['EmailMessage'])"
_EU  = "__import__('email.utils', fromlist=['parseaddr', 'formataddr'])"
_EP  = "__import__('email', fromlist=['message_from_string', 'message_from_bytes'])"


def register():
    register_lib("email", "email")

    # ── BUILD ─────────────────────────────────────────────────
    register_lib_call("email", "message",
        lambda a: f"{_EM}.EmailMessage()")

    register_lib_call("email", "make",
        lambda a: (
            f"(lambda _m: ("
            f"_m.__setitem__('Subject', {a[0]}), "
            f"_m.__setitem__('From', {a[1]}), "
            f"_m.__setitem__('To', {a[2]}), "
            f"_m.set_content({a[3]}), _m)[-1])({_EM}.EmailMessage())"
            if len(a) > 3 else
            f"{_EM}.EmailMessage()"
        ))

    register_lib_call("email", "set_content",
        lambda a: f"{a[0]}.set_content({a[1]})" if len(a) > 1 else f"{a[0]}.set_content('')")

    register_lib_call("email", "add_html",
        lambda a: (
            f"{a[0]}.add_alternative({a[1]}, subtype='html')"
            if len(a) > 1 else
            f"{a[0]}.add_alternative('', subtype='html')"
        ))

    register_lib_call("email", "set_header",
        lambda a: (
            f"(lambda _m: (_m.__delitem__({a[1]}), _m.__setitem__({a[1]}, {a[2]}))[-1] "
            f"if {a[1]} in _m else _m.__setitem__({a[1]}, {a[2]}))({a[0]})"
            if len(a) > 2 else
            f"None"
        ))

    register_lib_call("email", "attach_file",
        lambda a: (
            f"(lambda _m, _p: _m.add_attachment("
            f"open(_p, 'rb').read(), maintype='application', subtype='octet-stream', "
            f"filename=__import__('os').path.basename(_p)))({a[0]}, {a[1]})"
            if len(a) > 1 else
            f"None"
        ))

    # ── PARSE ─────────────────────────────────────────────────
    register_lib_call("email", "parse",
        lambda a: f"{_EP}.message_from_string({a[0]})")

    register_lib_call("email", "parse_bytes",
        lambda a: f"{_EP}.message_from_bytes({a[0]})")

    # ── INSPECT ───────────────────────────────────────────────
    register_lib_call("email", "subject",
        lambda a: f"{a[0]}.get('Subject', '')")

    register_lib_call("email", "sender",
        lambda a: f"{a[0]}.get('From', '')")

    register_lib_call("email", "recipients",
        lambda a: f"{a[0]}.get('To', '')")

    register_lib_call("email", "header",
        lambda a: f"{a[0]}.get({a[1]}, '')" if len(a) > 1 else f"''")

    register_lib_call("email", "headers",
        lambda a: f"dict({a[0]}.items())")

    register_lib_call("email", "body",
        lambda a: (
            f"(lambda _m: _m.get_body(preferencelist=('plain',)).get_content() "
            f"if hasattr(_m, 'get_body') and _m.get_body(preferencelist=('plain',)) is not None "
            f"else (_m.get_payload(decode=True).decode('utf-8', 'replace') "
            f"if not _m.is_multipart() else ''))({a[0]})"
        ))

    register_lib_call("email", "is_multipart",
        lambda a: f"{a[0]}.is_multipart()")

    register_lib_call("email", "parts",
        lambda a: f"list({a[0]}.walk())")

    register_lib_call("email", "as_string",
        lambda a: f"{a[0]}.as_string()")

    # ── ADDRESS UTILITIES ─────────────────────────────────────
    register_lib_call("email", "parse_address",
        lambda a: f"{_EU}.parseaddr({a[0]})")

    register_lib_call("email", "format_address",
        lambda a: f"{_EU}.formataddr(({a[0]}, {a[1]}))" if len(a) > 1 else f"{_EU}.formataddr(('', {a[0]}))")

    register_lib_call("email", "valid_address",
        lambda a: (
            f"(lambda _r: '@' in _r[1] and '.' in _r[1].split('@')[-1])"
            f"({_EU}.parseaddr({a[0]}))"
            if a else
            f"False"
        ))
