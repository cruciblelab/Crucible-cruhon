"""
Tests for cruhon-shortcuts-data v2.5 additions:
  - data_media.py  (@yaml.*, @image.*, @pdf.*)
  - data_regex.py  (@re.*)

Each rewrite test verifies that the shortcut alias compiles to the same
Python as the canonical namespace call — i.e. the before_parse hook fired
and routed correctly.  We never assert on raw `@ns.method[` strings because
the transpiler converts those to Python before we see them.

The @re lib_call tests do execute real Python (stdlib re is always present).
yaml / image / pdf lib_call methods require optional packages, so only
source-level checks are done for those.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core.mod_loader import load_all_mods
from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile


@pytest.fixture(scope="module", autouse=True)
def _mods():
    load_all_mods(Path(__file__).parent.parent.parent)


def _src(source: str) -> str:
    """Return the transpiled Python source without executing it."""
    return transpile(parse(source))


def _run(src: str) -> dict:
    code = transpile(parse(src))
    ns = {}
    exec(compile(code, "<t>", "exec"), ns)
    return ns


# ── YAML rewrites ────────────────────────────────────────────────────────────

class TestYamlRewrites:
    def test_yaml_load_global_rewrite(self):
        assert _src('@var[r; @yaml_load["a: 1"]]') == _src('@var[r; @yaml.loads["a: 1"]]')

    def test_yaml_file_global_rewrite(self):
        assert _src('@var[r; @yaml_file["data.yaml"]]') == _src('@var[r; @yaml.load_file["data.yaml"]]')

    def test_yaml_dump_global_rewrite(self):
        assert _src('@var[r; @yaml_dump[d]]') == _src('@var[r; @yaml.dumps[d]]')

    def test_yaml_get_global_rewrite(self):
        assert _src('@var[r; @yaml_get[d; "key"]]') == _src('@var[r; @yaml.get[d; "key"]]')

    def test_yaml_load_method_alias(self):
        assert _src('@var[r; @yaml.load["a: 1"]]') == _src('@var[r; @yaml.loads["a: 1"]]')

    def test_yaml_dump_method_alias(self):
        assert _src('@var[r; @yaml.dump[d]]') == _src('@var[r; @yaml.dumps[d]]')

    def test_yaml_file_method_alias(self):
        assert _src('@var[r; @yaml.file["path.yaml"]]') == _src('@var[r; @yaml.load_file["path.yaml"]]')


# ── Image rewrites ───────────────────────────────────────────────────────────

class TestImageRewrites:
    def test_img_open_global_rewrite(self):
        assert _src('@var[r; @img_open["photo.png"]]') == _src('@var[r; @image.open["photo.png"]]')

    def test_img_save_global_rewrite(self):
        assert _src('@img_save[img; "out.png"]') == _src('@image.save[img; "out.png"]')

    def test_img_resize_global_rewrite(self):
        assert _src('@var[r; @img_resize[img; 100; 200]]') == _src('@var[r; @image.resize[img; 100; 200]]')

    def test_img_thumb_global_rewrite(self):
        assert _src('@img_thumb[img; 64; 64]') == _src('@image.thumbnail[img; 64; 64]')

    def test_img_gray_global_rewrite(self):
        assert _src('@var[r; @img_gray[img]]') == _src('@var[r; @image.grayscale[img]]')

    def test_image_gray_method_alias(self):
        assert _src('@var[r; @image.gray[img]]') == _src('@var[r; @image.grayscale[img]]')

    def test_image_thumb_method_alias(self):
        assert _src('@var[r; @image.thumb[img; 64; 64]]') == _src('@var[r; @image.thumbnail[img; 64; 64]]')


# ── PDF rewrites ─────────────────────────────────────────────────────────────

class TestPdfRewrites:
    def test_pdf_open_global_rewrite(self):
        assert _src('@var[r; @pdf_open["doc.pdf"]]') == _src('@var[r; @pdf.open["doc.pdf"]]')

    def test_pdf_text_global_rewrite(self):
        assert _src('@var[r; @pdf_text[doc]]') == _src('@var[r; @pdf.text[doc]]')

    def test_pdf_pages_global_rewrite(self):
        assert _src('@var[r; @pdf_pages[doc]]') == _src('@var[r; @pdf.page_count[doc]]')

    def test_pdf_page_global_rewrite(self):
        assert _src('@var[r; @pdf_page[doc; 0]]') == _src('@var[r; @pdf.text_of[doc; 0]]')

    def test_pdf_count_method_alias(self):
        assert _src('@var[r; @pdf.count[doc]]') == _src('@var[r; @pdf.page_count[doc]]')

    def test_pdf_page_method_alias(self):
        assert _src('@var[r; @pdf.page[doc; 1]]') == _src('@var[r; @pdf.text_of[doc; 1]]')


# ── Regex rewrites ───────────────────────────────────────────────────────────
# Note: @re_find and @re.find are intentionally absent — cruhon-shortcuts-pro
# owns those names (mapping to @re.findall).  Only non-conflicting aliases are
# tested here so both plugins can be loaded simultaneously.

class TestRegexRewrites:
    def test_re_match_global_rewrite(self):
        assert _src('@var[r; @re_match["\\d+"; "abc123"]]') == _src('@var[r; @re.match["\\d+"; "abc123"]]')

    def test_re_findall_global_rewrite(self):
        assert _src('@var[r; @re_findall["\\d+"; "a1b2c3"]]') == _src('@var[r; @re.findall["\\d+"; "a1b2c3"]]')

    def test_re_sub_global_rewrite(self):
        assert _src('@var[r; @re_sub["\\d+"; "X"; "a1b2"]]') == _src('@var[r; @re.sub["\\d+"; "X"; "a1b2"]]')

    def test_re_split_global_rewrite(self):
        assert _src('@var[r; @re_split["\\s+"; "a b c"]]') == _src('@var[r; @re.split["\\s+"; "a b c"]]')

    def test_is_match_global_rewrite(self):
        assert _src('@var[r; @is_match["\\d+"; "123"]]') == _src('@var[r; @re.is_match["\\d+"; "123"]]')

    def test_first_match_global_rewrite(self):
        assert _src('@var[r; @first_match["\\d+"; "abc123"]]') == _src('@var[r; @re.group1["\\d+"; "abc123"]]')

    def test_re_test_method_alias(self):
        assert _src('@var[r; @re.test["\\d+"; "123"]]') == _src('@var[r; @re.is_match["\\d+"; "123"]]')

    def test_re_replace_method_alias(self):
        assert _src('@var[r; @re.replace["\\d+"; "X"; "a1b2"]]') == _src('@var[r; @re.sub["\\d+"; "X"; "a1b2"]]')

    def test_re_first_method_alias(self):
        assert _src('@var[r; @re.first["(\\d+)"; "abc123"]]') == _src('@var[r; @re.group1["(\\d+)"; "abc123"]]')


# ── re.extract new lib_call (stdlib — can execute) ───────────────────────────

class TestRegexLibCalls:
    def test_re_extract_single_group(self):
        ns = _run('@var[r; @re.extract["(\\d+)"; "a1 b2 c3"]]')
        assert ns["r"] == ["1", "2", "3"]

    def test_re_replace_all(self):
        ns = _run(
            '@var[pairs; @list[@list["a"; "X"]; @list["b"; "Y"]]]\n'
            '@var[r; @re.replace_all[pairs; "abc"]]'
        )
        assert ns["r"] == "XYc"
