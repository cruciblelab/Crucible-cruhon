"""
cruhon-shortcuts — io group
=============================
Shortcuts for @io.*, @archive.*, and @mail.* operations.

Global aliases (source rewrites)
─────────────────────────────────
@sio[s]                 → @io.StringIO[s]
@bio[b]                 → @io.BytesIO[b]
@open_text[path]        → @io.open[path]
@open_bytes[path]       → @io.open_bytes[path]
@open_write[path]       → @io.open_write[path]
@open_append[path]      → @io.open_append[path]
@zip_create[path; ...]  → @archive.zip[path; ...]
@zip_extract[path; dst] → @archive.unzip[path; dst]
@tar_create[path; ...]  → @archive.tar[path; ...]
@tar_extract[path; dst] → @archive.untar[path; dst]
@gzip_file[path]        → @archive.gzip[path]
@gunzip_file[path]      → @archive.gunzip[path]
@send_mail[...]         → @mail.send[...]
@send_html_mail[...]    → @mail.send_html[...]

Namespace method aliases
─────────────────────────
@io.str_buf[s]          → @io.StringIO[s]
@io.bytes_buf[b]        → @io.BytesIO[b]
@archive.create_zip[p]  → @archive.zip[p]
@archive.extract_zip[p] → @archive.unzip[p]

New methods (via api.lib_call)
───────────────────────────────
@io.read_all[stream]        → read all content from stream
@io.read_lines[stream]      → readlines from stream
@io.seek_start[stream]      → seek to position 0
@io.to_bytes[stream]        → getvalue() as bytes (for BytesIO)
@io.to_str[stream]          → getvalue() as string (for StringIO)
@io.copy_stream[src; dst]   → copy all content from src to dst stream
@archive.list_zip[path]     → list files inside a zip archive
@archive.list_tar[path]     → list files inside a tar archive
@archive.zip_size[path]     → total uncompressed size of zip contents
@archive.add_to_zip[z; f]   → add file to existing zip archive
@mail.build_message[subj; body; to] → create email.message.Message object
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@sio[":            "@io.StringIO[",
    "@bio[":            "@io.BytesIO[",
    "@open_text[":      "@io.open[",
    "@open_bytes[":     "@io.open_bytes[",
    "@open_write[":     "@io.open_write[",
    "@open_append[":    "@io.open_append[",
    "@zip_create[":     "@archive.zip[",
    "@zip_extract[":    "@archive.unzip[",
    "@tar_create[":     "@archive.tar[",
    "@tar_extract[":    "@archive.untar[",
    "@gzip_file[":      "@archive.gzip[",
    "@gunzip_file[":    "@archive.gunzip[",
    "@send_mail[":      "@mail.send[",
    "@send_html_mail[": "@mail.send_html[",
}

METHOD_ALIASES: dict[str, str] = {
    "@io.str_buf[":       "@io.StringIO[",
    "@io.bytes_buf[":     "@io.BytesIO[",
    "@archive.create_zip[": "@archive.zip[",
    "@archive.extract_zip[": "@archive.unzip[",
}

_IO  = "__import__('io')"
_ZF  = "__import__('zipfile')"
_TF  = "__import__('tarfile')"
_SHU = "__import__('shutil')"


def _new_lib_calls(api) -> None:

    api.lib_call("io", "read_all", lambda a: (
        f"{a[0]}.read()"
        if a else
        f"''"
    ))

    api.lib_call("io", "read_lines", lambda a: (
        f"{a[0]}.readlines()"
        if a else
        f"[]"
    ))

    api.lib_call("io", "seek_start", lambda a: (
        f"(lambda _s: (_s.seek(0), _s)[1])({a[0]})"
        if a else
        f"None"
    ))

    api.lib_call("io", "to_bytes", lambda a: (
        f"{a[0]}.getvalue()"
        if a else
        f"b''"
    ))

    api.lib_call("io", "to_str", lambda a: (
        f"{a[0]}.getvalue()"
        if a else
        f"''"
    ))

    api.lib_call("io", "copy_stream", lambda a: (
        f"{_SHU}.copyfileobj({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("archive", "list_zip", lambda a: (
        f"{_ZF}.ZipFile({a[0]}).namelist()"
        if a else
        f"[]"
    ))

    api.lib_call("archive", "list_tar", lambda a: (
        f"{_TF}.open({a[0]}).getnames()"
        if a else
        f"[]"
    ))

    api.lib_call("archive", "zip_size", lambda a: (
        f"sum(_i.file_size for _i in {_ZF}.ZipFile({a[0]}).infolist())"
        if a else
        f"0"
    ))

    api.lib_call("archive", "add_to_zip", lambda a: (
        f"(lambda _z, _f: {_ZF}.ZipFile(_z, 'a').write(_f))({a[0]}, {a[1]})"
        if len(a) > 1 else
        f"None"
    ))

    api.lib_call("mail", "build_message", lambda a: (
        f"(lambda _subj, _body, _to: "
        f"(lambda _msg: "
        f"(_msg.__setitem__('Subject', _subj), "
        f"_msg.__setitem__('To', _to), "
        f"_msg.set_payload(_body), _msg)[3])"
        f"(__import__('email.message', fromlist=['Message']).Message()))"
        f"({a[0]}, {a[1]}, {a[2]})"
        if len(a) > 2 else
        f"__import__('email.message', fromlist=['Message']).Message()"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
