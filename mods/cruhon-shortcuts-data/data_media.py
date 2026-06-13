"""
cruhon-shortcuts-data — media group
=======================================
Shortcuts for @yaml.*, @image.*, and @pdf.*.

Global aliases (source rewrites)
─────────────────────────────────
@yaml_load[text]         → @yaml.loads[text]
@yaml_file[path]         → @yaml.load_file[path]
@yaml_dump[data]         → @yaml.dumps[data]
@yaml_get[data; key]     → @yaml.get[data; key]
@img_open[path]          → @image.open[path]
@img_save[img; path]     → @image.save[img; path]
@img_resize[img; w; h]   → @image.resize[img; w; h]
@img_thumb[img; w; h]    → @image.thumbnail[img; w; h]
@img_gray[img]           → @image.grayscale[img]
@pdf_open[path]          → @pdf.open[path]
@pdf_text[doc]           → @pdf.text[doc]
@pdf_pages[doc]          → @pdf.page_count[doc]
@pdf_page[doc; n]        → @pdf.text_of[doc; n]

Namespace method aliases
─────────────────────────
@yaml.load[text]         → @yaml.loads[text]
@yaml.dump[data]         → @yaml.dumps[data]
@yaml.file[path]         → @yaml.load_file[path]
@image.gray[img]         → @image.grayscale[img]
@image.thumb[img; w; h]  → @image.thumbnail[img; w; h]
@pdf.count[doc]          → @pdf.page_count[doc]
@pdf.page[doc; n]        → @pdf.text_of[doc; n]

New methods (via api.lib_call)
───────────────────────────────
@yaml.get_all[data; *keys]  → nested key access (data["k1"]["k2"]...)
@image.wh[img]              → (width, height) tuple
@pdf.has_tables[doc]        → True if any page has tables
"""
from __future__ import annotations

GLOBAL_REWRITES: dict[str, str] = {
    "@yaml_load[":   "@yaml.loads[",
    "@yaml_file[":   "@yaml.load_file[",
    "@yaml_dump[":   "@yaml.dumps[",
    "@yaml_get[":    "@yaml.get[",
    "@img_open[":    "@image.open[",
    "@img_save[":    "@image.save[",
    "@img_resize[":  "@image.resize[",
    "@img_thumb[":   "@image.thumbnail[",
    "@img_gray[":    "@image.grayscale[",
    "@pdf_open[":    "@pdf.open[",
    "@pdf_text[":    "@pdf.text[",
    "@pdf_pages[":   "@pdf.page_count[",
    "@pdf_page[":    "@pdf.text_of[",
}

METHOD_ALIASES: dict[str, str] = {
    "@yaml.load[":    "@yaml.loads[",
    "@yaml.dump[":    "@yaml.dumps[",
    "@yaml.file[":    "@yaml.load_file[",
    "@image.gray[":   "@image.grayscale[",
    "@image.thumb[":  "@image.thumbnail[",
    "@pdf.count[":    "@pdf.page_count[",
    "@pdf.page[":     "@pdf.text_of[",
}


def _new_lib_calls(api) -> None:

    api.lib_call("yaml", "get_all", lambda a: (
        f"__import__('functools').reduce(lambda _d, _k: _d[_k], [{', '.join(a[1:])}], {a[0]})"
        if len(a) > 1 else a[0] if a else "None"
    ))

    api.lib_call("image", "wh", lambda a: (
        f"{a[0]}.size"
        if a else "None"
    ))

    api.lib_call("pdf", "has_tables", lambda a: (
        f"any(_p.extract_tables() for _p in {a[0]}.pages)"
        if a else "False"
    ))


def register_group(api, cfg) -> dict[str, str]:
    rewrites: dict[str, str] = {}
    rewrites.update(cfg.filter_rewrites(GLOBAL_REWRITES))
    rewrites.update(cfg.filter_method_aliases(METHOD_ALIASES))
    if cfg.method_aliases:
        _new_lib_calls(api)
    return rewrites
