"""
Tests for HTML & Web namespaces: @html, @webbrowser, @mimetypes
"""
import pytest

from cruhon.core.transpiler import Transpiler
from cruhon.core.parser import Parser


def transpile(src):
    return Transpiler().transpile(Parser().parse(src))


def run(src, globs=None):
    g = globs or {}
    exec(compile(transpile(src), "<test>", "exec"), g)
    return g


# ─────────────────────────────────────────────────────────────
# @html
# ─────────────────────────────────────────────────────────────

class TestHtml:
    def test_escape(self):
        g = run('@var[s; @html.escape["<a> & \'b\'"]]')
        assert g["s"] == "&lt;a&gt; &amp; &#x27;b&#x27;"

    def test_unescape(self):
        g = run('@var[s; @html.unescape["&lt;x&gt; &amp; &#x27;y&#x27;"]]')
        assert g["s"] == "<x> & 'y'"

    def test_strip_tags(self):
        g = run('@var[s; @html.strip_tags["<p>Hi <b>there</b></p>"]]')
        assert g["s"] == "Hi there"

    def test_text(self):
        g = run('@var[s; @html.text["<h1>Hello</h1>  <p>World &amp; co</p>"]]')
        assert g["s"] == "Hello World & co"

    def test_links(self):
        h = '<a href="https://a.com">x</a> <a href="/b">y</a>'
        g = run('@var[l; @html.links[h]]', {"h": h})
        assert g["l"] == ["https://a.com", "/b"]

    def test_images(self):
        h = '<img src="a.png"><img src="b.jpg">'
        g = run('@var[i; @html.images[h]]', {"h": h})
        assert g["i"] == ["a.png", "b.jpg"]

    def test_tags(self):
        g = run('@var[t; @html.tags["<div><p></p><span></span></div>"]]')
        assert g["t"] == ["div", "p", "span"]


# ─────────────────────────────────────────────────────────────
# @webbrowser
# ─────────────────────────────────────────────────────────────

class TestWebbrowser:
    def test_open_monkeypatched(self, monkeypatch):
        import webbrowser
        opened = []
        monkeypatch.setattr(webbrowser, "open", lambda url, *a, **k: opened.append(url) or True)
        run('@webbrowser.open["https://example.com"]')
        assert opened == ["https://example.com"]

    def test_open_tab_monkeypatched(self, monkeypatch):
        import webbrowser
        opened = []
        monkeypatch.setattr(webbrowser, "open_new_tab", lambda url: opened.append(url) or True)
        run('@webbrowser.open_tab["https://t.com"]')
        assert opened == ["https://t.com"]


# ─────────────────────────────────────────────────────────────
# @mimetypes
# ─────────────────────────────────────────────────────────────

class TestMimetypes:
    def test_guess_html(self):
        g = run('@var[m; @mimetypes.guess["page.html"]]')
        assert g["m"] == "text/html"

    def test_guess_png(self):
        g = run('@var[m; @mimetypes.guess["pic.png"]]')
        assert g["m"] == "image/png"

    def test_full(self):
        g = run('@var[t; @mimetypes.full["a.txt"]]')
        assert g["t"][0] == "text/plain"

    def test_is_text(self):
        g = run('@var[b; @mimetypes.is_text["notes.txt"]]')
        assert g["b"] is True

    def test_is_image(self):
        g = run('@var[b; @mimetypes.is_image["pic.jpg"]]')
        assert g["b"] is True

    def test_is_text_false(self):
        g = run('@var[b; @mimetypes.is_text["pic.png"]]')
        assert g["b"] is False

    def test_extension(self):
        g = run('@var[e; @mimetypes.extension["text/html"]]')
        assert g["e"] in (".html", ".htm")

    def test_add(self):
        run('@mimetypes.add["application/x-cruhon"; ".cru"]')
        g = run('@var[m; @mimetypes.guess["file.cru"]]')
        assert g["m"] == "application/x-cruhon"
