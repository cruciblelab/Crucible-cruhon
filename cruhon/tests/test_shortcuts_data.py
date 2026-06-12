"""
Integration tests for the cruhon-shortcuts-data plugin.

Loads all bundled mods (which installs the data plugin's before_parse
rewrite hook and its new lib_calls), then exercises a representative set
of global aliases, method aliases, and convenience methods end-to-end
through the parse → transpile → exec pipeline.
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


def _run(src):
    code = transpile(parse(src))
    ns = {}
    exec(compile(code, "<t>", "exec"), ns)
    return ns


class TestDataShortcutsFormat:
    def test_xml_parse_and_text_aliases(self):
        ns = _run('@var[r; @xml_parse["<a><b>hi</b></a>"]]\n@var[t; @xml_text[r; "b"]]')
        assert ns["t"] == "hi"

    def test_toml_load_alias(self):
        ns = _run('@var[d; @toml_load["port = 8080"]]')
        assert ns["d"] == {"port": 8080}

    def test_similar_alias(self):
        ns = _run('@var[r; @similar["hello world"; "hello werld"]]')
        assert ns["r"] is True

    def test_closest_alias(self):
        ns = _run('@var[r; @closest["colour"; ["color", "flavor"]]]')
        assert ns["r"] == "color"

    def test_xml_text_all_new_method(self):
        ns = _run(
            '@var[r; @xml_parse["<root><i>a</i><i>b</i></root>"]]\n'
            '@var[t; @xml.text_all[r; "i"]]'
        )
        assert ns["t"] == ["a", "b"]

    def test_diff_changed_new_method(self):
        ns = _run('@var[r; @diff.changed["abc"; "abc"]]')
        assert ns["r"] is False


class TestDataShortcutsNumbers:
    def test_dec_add_alias(self):
        ns = _run('@var[r; @dec_add["0.1"; "0.2"]]')
        assert str(ns["r"]) == "0.3"

    def test_frac_aliases(self):
        ns = _run('@var[f; @frac[1; 3]]\n@var[s; @frac_str[f]]')
        assert ns["s"] == "1/3"

    def test_money_alias(self):
        ns = _run('@var[r; @money["3.14159"]]')
        assert str(ns["r"]) == "3.14"

    def test_decimal_percent_new_method(self):
        ns = _run('@var[r; @decimal.percent["1"; "4"]]')
        assert str(ns["r"]) == "25.00"

    def test_decimal_average_new_method(self):
        ns = _run('@var[r; @decimal.average[["0.1", "0.2", "0.3"]]]')
        assert str(ns["r"]) == "0.2"

    def test_fraction_reciprocal_new_method(self):
        ns = _run('@var[r; @fraction.reciprocal[@frac[2; 3]]]\n@var[s; @fraction.to_str[r]]')
        assert ns["s"] == "3/2"


class TestDataShortcutsSystem:
    def test_is_private_ip_alias(self):
        ns = _run('@var[r; @is_private_ip["10.0.0.1"]]')
        assert ns["r"] is True

    def test_os_name_alias(self):
        import platform
        ns = _run('@var[r; @os_name[]]')
        assert ns["r"] == platform.system()

    def test_char_name_alias(self):
        ns = _run('@var[r; @char_name["A"]]')
        assert ns["r"] == "LATIN CAPITAL LETTER A"

    def test_strip_accents_alias(self):
        ns = _run('@var[r; @strip_accents["café"]]')
        assert ns["r"] == "cafe"

    def test_hexlify_alias(self):
        ns = _run('@var[r; @hexlify[b"AB"]]')
        assert ns["r"] == "4142"

    def test_sh_split_alias(self):
        ns = _run('@var[r; @sh_split["echo hello world"]]')
        assert ns["r"] == ["echo", "hello", "world"]

    def test_ip_is_ipv4_new_method(self):
        ns = _run('@var[r; @ip.is_ipv4["192.168.1.1"]]')
        assert ns["r"] is True

    def test_platform_summary_new_method(self):
        ns = _run('@var[r; @platform.summary[]]')
        assert "Python" in ns["r"]

    def test_binascii_hex_spaced_new_method(self):
        ns = _run('@var[r; @binascii.hex_spaced[b"AB"]]')
        assert ns["r"] == "41 42"
