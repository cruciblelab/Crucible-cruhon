"""
Mail stdlib wrappers for Cruhon — @mail.*

Covers smtplib / email so a non-coder can send emails, build messages
and manage attachments with one-liners, without knowing SMTP, MIMEText
or MIMEMultipart.

━━━ SEND ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mail.send[to; subject; body]
      — send plain-text email via SMTP (uses env vars for config)
  @mail.send[to; subject; body; from_=; host=; port=; user=; pass_=; tls=]
  @mail.send_html[to; subject; html]
      — send HTML email
  @mail.send_with_attachment[to; subject; body; file]
      — send email with one file attachment

━━━ BUILD ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mail.message[subject; body]      → MIMEText object
  @mail.html_message[subject; html] → MIMEText (HTML) object
  @mail.attach[msg; file]           — attach a file to a message object

━━━ SMTP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mail.connect[host; port]         → SMTP connection
  @mail.connect_tls[host; port]     → SMTP_SSL connection
  @mail.login[smtp; user; pass_]    — authenticate
  @mail.deliver[smtp; from_; to; msg] — send a pre-built message
  @mail.close[smtp]                 — quit SMTP connection

━━━ PARSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @mail.parse[raw]                  → email.message_from_string result
  @mail.subject[msg]                → subject string
  @mail.sender[msg]                 → From header string
  @mail.body[msg]                   → decoded plain-text body
"""
from ..registry import register_lib, register_lib_call

_MOD = "cruhon.core.libs.mail_"


# ── Runtime helpers ───────────────────────────────────────────────────────────

def _send(to, subject, body,
          from_=None, host=None, port=None,
          user=None, pass_=None, tls=True):
    import os, smtplib
    from email.mime.text import MIMEText
    host  = str(host  or os.environ.get("MAIL_HOST",  "localhost"))
    port  = int(port  or os.environ.get("MAIL_PORT",  "587"))
    user  = str(user  or os.environ.get("MAIL_USER",  "") or "")
    pass_ = str(pass_ or os.environ.get("MAIL_PASS",  "") or "")
    from_ = str(from_ or os.environ.get("MAIL_FROM",  user) or user)
    tls   = bool(tls)

    msg = MIMEText(str(body), "plain", "utf-8")
    msg["Subject"] = str(subject)
    msg["From"]    = from_
    msg["To"]      = str(to) if not isinstance(to, (list, tuple)) else ", ".join(to)

    _smtp_send(host, port, user, pass_, tls, from_, to, msg)


def _send_html(to, subject, html,
               from_=None, host=None, port=None,
               user=None, pass_=None, tls=True):
    import os, smtplib
    from email.mime.text import MIMEText
    host  = str(host  or os.environ.get("MAIL_HOST",  "localhost"))
    port  = int(port  or os.environ.get("MAIL_PORT",  "587"))
    user  = str(user  or os.environ.get("MAIL_USER",  "") or "")
    pass_ = str(pass_ or os.environ.get("MAIL_PASS",  "") or "")
    from_ = str(from_ or os.environ.get("MAIL_FROM",  user) or user)
    tls   = bool(tls)

    msg = MIMEText(str(html), "html", "utf-8")
    msg["Subject"] = str(subject)
    msg["From"]    = from_
    msg["To"]      = str(to) if not isinstance(to, (list, tuple)) else ", ".join(to)

    _smtp_send(host, port, user, pass_, tls, from_, to, msg)


def _send_with_attachment(to, subject, body, file_path,
                          from_=None, host=None, port=None,
                          user=None, pass_=None, tls=True):
    import os, smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    host  = str(host  or os.environ.get("MAIL_HOST",  "localhost"))
    port  = int(port  or os.environ.get("MAIL_PORT",  "587"))
    user  = str(user  or os.environ.get("MAIL_USER",  "") or "")
    pass_ = str(pass_ or os.environ.get("MAIL_PASS",  "") or "")
    from_ = str(from_ or os.environ.get("MAIL_FROM",  user) or user)
    tls   = bool(tls)

    msg = MIMEMultipart()
    msg["Subject"] = str(subject)
    msg["From"]    = from_
    msg["To"]      = str(to) if not isinstance(to, (list, tuple)) else ", ".join(to)
    msg.attach(MIMEText(str(body), "plain", "utf-8"))

    file_path = str(file_path)
    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
    msg.attach(part)

    _smtp_send(host, port, user, pass_, tls, from_, to, msg)


def _smtp_send(host, port, user, pass_, tls, from_, to, msg):
    import smtplib
    to_list = [str(to)] if not isinstance(to, (list, tuple)) else [str(t) for t in to]
    if tls and port != 465:
        with smtplib.SMTP(host, port) as s:
            s.ehlo()
            s.starttls()
            if user:
                s.login(user, pass_)
            s.sendmail(from_, to_list, msg.as_string())
    else:
        with smtplib.SMTP_SSL(host, port) as s:
            if user:
                s.login(user, pass_)
            s.sendmail(from_, to_list, msg.as_string())


def _message(subject: str, body: str):
    from email.mime.text import MIMEText
    msg = MIMEText(str(body), "plain", "utf-8")
    msg["Subject"] = str(subject)
    return msg


def _html_message(subject: str, html: str):
    from email.mime.text import MIMEText
    msg = MIMEText(str(html), "html", "utf-8")
    msg["Subject"] = str(subject)
    return msg


def _attach(msg, file_path: str):
    import os
    from email.mime.base import MIMEBase
    from email import encoders
    file_path = str(file_path)
    with open(file_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(file_path)}")
    msg.attach(part)


def _body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return str(msg.get_payload())


def _ref(fn: str) -> str:
    return f"__import__({_MOD!r}, fromlist=[{fn!r}]).{fn}"


def register():
    register_lib("mail", None)

    # ── SEND ────────────────────────────────────────────────────
    register_lib_call("mail", "send",
        lambda a: f"{_ref('_send')}({', '.join(a)})")

    register_lib_call("mail", "send_html",
        lambda a: f"{_ref('_send_html')}({', '.join(a)})")

    register_lib_call("mail", "send_with_attachment",
        lambda a: f"{_ref('_send_with_attachment')}({', '.join(a)})")

    # ── BUILD ────────────────────────────────────────────────────
    register_lib_call("mail", "message",
        lambda a: f"{_ref('_message')}({a[0]}, {a[1]})")

    register_lib_call("mail", "html_message",
        lambda a: f"{_ref('_html_message')}({a[0]}, {a[1]})")

    register_lib_call("mail", "attach",
        lambda a: f"{_ref('_attach')}({a[0]}, {a[1]})")

    # ── SMTP ─────────────────────────────────────────────────────
    register_lib_call("mail", "connect",
        lambda a: (
            f"__import__('smtplib').SMTP({a[0]}, {a[1] if len(a)>1 else 25})"
        ))

    register_lib_call("mail", "connect_tls",
        lambda a: (
            f"__import__('smtplib').SMTP_SSL({a[0]}, {a[1] if len(a)>1 else 465})"
        ))

    register_lib_call("mail", "login",
        lambda a: f"{a[0]}.login({a[1]}, {a[2]})")

    register_lib_call("mail", "deliver",
        lambda a: f"{a[0]}.sendmail({a[1]}, {a[2]}, {a[3]}.as_string())")

    register_lib_call("mail", "close",
        lambda a: f"{a[0]}.quit()")

    # ── PARSE ────────────────────────────────────────────────────
    register_lib_call("mail", "parse",
        lambda a: f"__import__('email').message_from_string(str({a[0]}))")

    register_lib_call("mail", "subject",
        lambda a: f"str({a[0]}.get('Subject', ''))")

    register_lib_call("mail", "sender",
        lambda a: f"str({a[0]}.get('From', ''))")

    register_lib_call("mail", "body",
        lambda a: f"{_ref('_body')}({a[0]})")
