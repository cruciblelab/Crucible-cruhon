"""
cruhon/core/libs/ftp_.py
========================
FTP client for Cruhon — @ftp.*

Connect to FTP servers, browse directories and transfer files.

━━━ CONNECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ftp.new[]                      → unconnected FTP object
  @ftp.connect[host]              → connect (anonymous)
  @ftp.connect[host; user; pass]  → connect and log in
  @ftp.connect_tls[host; user; pass] → FTP over TLS
  @ftp.quit[ftp]                  → close the connection politely

━━━ BROWSE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ftp.list[ftp]                  → names in the current directory
  @ftp.details[ftp]               → detailed (LIST) directory lines
  @ftp.pwd[ftp]                   → current working directory
  @ftp.cwd[ftp; path]             → change directory
  @ftp.size[ftp; name]            → file size in bytes

━━━ TRANSFER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @ftp.download[ftp; remote; local] → fetch a file to a local path
  @ftp.upload[ftp; local; remote]   → store a local file remotely
  @ftp.delete[ftp; name]            → delete a remote file
"""
from ..registry import register_lib, register_lib_call

_FT = "__import__('ftplib')"


def register():
    register_lib("ftp", None)

    # ── Connect ───────────────────────────────────────────────
    register_lib_call("ftp", "new",
        lambda a: f"{_FT}.FTP()")
    register_lib_call("ftp", "connect",
        lambda a: (
            f"{_FT}.FTP({a[0]}, {a[1]}, {a[2]})" if len(a) > 2 else
            f"{_FT}.FTP({a[0]})"
        ))
    register_lib_call("ftp", "connect_tls",
        lambda a: (
            f"(lambda _h, _u, _p: (lambda _f: (_f.login(_u, _p), _f.prot_p(), _f)[2])"
            f"({_FT}.FTP_TLS(_h)))({a[0]}, {a[1]}, {a[2]})"
        ))
    register_lib_call("ftp", "quit",
        lambda a: f"{a[0]}.quit()")

    # ── Browse ────────────────────────────────────────────────
    register_lib_call("ftp", "list",
        lambda a: f"{a[0]}.nlst()")
    register_lib_call("ftp", "details",
        lambda a: f"(lambda _f: (lambda _o: (_f.retrlines('LIST', _o.append), _o)[1])([]))({a[0]})")
    register_lib_call("ftp", "pwd",
        lambda a: f"{a[0]}.pwd()")
    register_lib_call("ftp", "cwd",
        lambda a: f"{a[0]}.cwd({a[1]})")
    register_lib_call("ftp", "size",
        lambda a: f"{a[0]}.size({a[1]})")

    # ── Transfer ──────────────────────────────────────────────
    register_lib_call("ftp", "download",
        lambda a: (
            f"(lambda _f, _r, _l: (lambda _o: (_f.retrbinary('RETR ' + _r, _o.write), _o.close())[1])"
            f"(open(_l, 'wb')))({a[0]}, {a[1]}, {a[2]})"
        ))
    register_lib_call("ftp", "upload",
        lambda a: (
            f"(lambda _f, _l, _r: (lambda _o: (_f.storbinary('STOR ' + _r, _o), _o.close())[1])"
            f"(open(_l, 'rb')))({a[0]}, {a[1]}, {a[2]})"
        ))
    register_lib_call("ftp", "delete",
        lambda a: f"{a[0]}.delete({a[1]})")
