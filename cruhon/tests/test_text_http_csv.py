"""
Tests for Group 2: @text, @http (expanded), @csv
"""
import os
import csv
import json
import pytest

from cruhon.core.parser import parse
from cruhon.core.transpiler import transpile
from cruhon.core.runner import run_source, RunError


def _eval(expr_source: str):
    code = transpile(parse(f"@var[__r__; {expr_source}]"))
    ns: dict = {}
    exec(compile(code, "<test>", "exec"), ns)
    return ns["__r__"]


def _run(source: str):
    return run_source(source)


@pytest.fixture
def in_tmp(tmp_path):
    old = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old)


# ════════════════════════════════════════════════════════════
#  @text — case
# ════════════════════════════════════════════════════════════

class TestTextCase:
    def test_upper(self):      assert _eval('@text.upper["hello"]') == "HELLO"
    def test_lower(self):      assert _eval('@text.lower["HELLO"]') == "hello"
    def test_title(self):      assert _eval('@text.title["hello world"]') == "Hello World"
    def test_capitalize(self): assert _eval('@text.capitalize["hello world"]') == "Hello world"
    def test_swapcase(self):   assert _eval('@text.swapcase["Hello"]') == "hELLO"


# ════════════════════════════════════════════════════════════
#  @text — whitespace
# ════════════════════════════════════════════════════════════

class TestTextStrip:
    def test_strip(self):   assert _eval('@text.strip["  hi  "]') == "hi"
    def test_lstrip(self):  assert _eval('@text.lstrip["  hi  "]') == "hi  "
    def test_rstrip(self):  assert _eval('@text.rstrip["  hi  "]') == "  hi"
    def test_strip_chars(self): assert _eval('@text.strip["xxhixx"; "x"]') == "hi"


# ════════════════════════════════════════════════════════════
#  @text — search / test
# ════════════════════════════════════════════════════════════

class TestTextSearch:
    def test_contains_true(self):   assert _eval('@text.contains["hello world"; "world"]') is True
    def test_contains_false(self):  assert _eval('@text.contains["hello"; "xyz"]') is False
    def test_startswith(self):      assert _eval('@text.startswith["hello"; "hel"]') is True
    def test_endswith(self):        assert _eval('@text.endswith["hello"; "llo"]') is True
    def test_count(self):           assert _eval('@text.count["abcabc"; "a"]') == 2
    def test_index_found(self):     assert _eval('@text.index["hello"; "ll"]') == 2
    def test_index_not_found(self): assert _eval('@text.index["hello"; "xyz"]') == -1
    def test_is_digit_true(self):   assert _eval('@text.is_digit["123"]') is True
    def test_is_digit_false(self):  assert _eval('@text.is_digit["12a"]') is False
    def test_is_alpha(self):        assert _eval('@text.is_alpha["abc"]') is True
    def test_is_alnum(self):        assert _eval('@text.is_alnum["abc123"]') is True
    def test_is_space(self):        assert _eval('@text.is_space["   "]') is True
    def test_is_upper(self):        assert _eval('@text.is_upper["ABC"]') is True
    def test_is_lower(self):        assert _eval('@text.is_lower["abc"]') is True


# ════════════════════════════════════════════════════════════
#  @text — split / join
# ════════════════════════════════════════════════════════════

class TestTextSplitJoin:
    def test_split_default(self):  assert _eval('@text.split["a b c"]') == ["a", "b", "c"]
    def test_split_sep(self):      assert _eval('@text.split["a,b,c"; ","]') == ["a", "b", "c"]
    def test_split_max(self):      assert _eval('@text.split["a,b,c"; ","; 1]') == ["a", "b,c"]
    def test_join(self):           assert _eval('@text.join["-"; ["a", "b", "c"]]') == "a-b-c"
    def test_lines(self):
        import textwrap as _tw
        code = transpile(parse('@var[s; "a\\nb\\nc"]\n@var[__r__; @text.lines[s]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == ["a", "b", "c"]
    def test_words(self):          assert _eval('@text.words["  a  b  c  "]') == ["a", "b", "c"]


# ════════════════════════════════════════════════════════════
#  @text — replace / format
# ════════════════════════════════════════════════════════════

class TestTextReplace:
    def test_replace(self):     assert _eval('@text.replace["hello"; "l"; "r"]') == "herro"
    def test_replace_n(self):   assert _eval('@text.replace["aaa"; "a"; "b"; 2]') == "bba"
    def test_repeat(self):      assert _eval('@text.repeat["ab"; 3]') == "ababab"
    def test_reverse(self):     assert _eval('@text.reverse["hello"]') == "olleh"
    def test_template(self):
        assert _eval('@text.template["hi {name}"; {"name": "Ali"}]') == "hi Ali"


# ════════════════════════════════════════════════════════════
#  @text — slice / size
# ════════════════════════════════════════════════════════════

class TestTextSlice:
    def test_len(self):              assert _eval('@text.len["hello"]') == 5
    def test_slice_start(self):      assert _eval('@text.slice["hello"; 2]') == "llo"
    def test_slice_range(self):      assert _eval('@text.slice["hello"; 1; 3]') == "el"
    def test_truncate_short(self):   assert _eval('@text.truncate["hi"; 10]') == "hi"
    def test_truncate_long(self):    assert _eval('@text.truncate["hello world"; 5]') == "hello…"
    def test_truncate_custom_suf(self):
        assert _eval('@text.truncate["hello world"; 5; "..."]') == "hello..."


# ════════════════════════════════════════════════════════════
#  @text — pad / align
# ════════════════════════════════════════════════════════════

class TestTextPad:
    def test_pad_left(self):   assert _eval('@text.pad_left["5"; 3]') == "  5"
    def test_pad_right(self):  assert _eval('@text.pad_right["5"; 3]') == "5  "
    def test_center(self):     assert _eval('@text.center["a"; 5]') == "  a  "
    def test_pad_char(self):   assert _eval('@text.pad_left["5"; 3; "0"]') == "005"
    def test_zfill(self):      assert _eval('@text.zfill["42"; 5]') == "00042"


# ════════════════════════════════════════════════════════════
#  @text — wrap / indent
# ════════════════════════════════════════════════════════════

class TestTextWrap:
    def test_wrap(self):
        result = _eval('@text.wrap["hello world foo bar"; 10]')
        assert isinstance(result, list)
        assert all(len(line) <= 10 for line in result)

    def test_fill(self):
        result = _eval('@text.fill["hello world foo bar"; 10]')
        assert isinstance(result, str)
        assert "\n" in result

    def test_indent(self):
        code = transpile(parse('@var[s; "a\\nb"]\n@var[__r__; @text.indent[s; "  "]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == "  a\n  b"

    def test_dedent(self):
        code = transpile(parse('@var[s; "  a\\n  b"]\n@var[__r__; @text.dedent[s]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == "a\nb"


# ════════════════════════════════════════════════════════════
#  @text — regex
# ════════════════════════════════════════════════════════════

class TestTextRegex:
    def test_match_true(self):    assert _eval('@text.match["^he"; "hello"]') is True
    def test_match_false(self):   assert _eval('@text.match["^lo"; "hello"]') is False
    def test_search_true(self):   assert _eval('@text.search["ll"; "hello"]') is True
    def test_search_false(self):  assert _eval('@text.search["xyz"; "hello"]') is False
    def test_find(self):          assert _eval('@text.find["\\d+"; "abc 42 xyz"]') == "42"
    def test_find_none(self):     assert _eval('@text.find["\\d+"; "abc"]') is None
    def test_findall(self):       assert _eval('@text.findall["\\d+"; "a1 b2 c3"]') == ["1","2","3"]
    def test_sub(self):           assert _eval('@text.sub["\\d"; "X"; "a1b2"]') == "aXbX"
    def test_sub_n(self):         assert _eval('@text.sub["a"; "b"; "aaa"; 2]') == "bba"
    def test_split_re(self):      assert _eval('@text.split_re["[,;]"; "a,b;c"]') == ["a","b","c"]
    def test_groups(self):
        result = _eval('@text.groups["(\\w+)@(\\w+)"; "ali@gmail"]')
        assert result == ["ali", "gmail"]
    def test_groups_no_match(self):
        assert _eval('@text.groups["(\\d+)"; "abc"]') == []

    def test_match_case_insensitive(self):
        import re as _re
        # pass flag as integer literal so no re import is needed in exec context
        flag = _re.IGNORECASE
        code = transpile(parse(f'@import[re]\n@var[__r__; @text.match["hello"; "HELLO"; re.IGNORECASE]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] is True

    def test_findall_case_insensitive(self):
        import re as _re
        code = transpile(parse(f'@import[re]\n@var[__r__; @text.findall["[a-z]+"; "Hello World"; re.IGNORECASE]]'))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["__r__"] == ["Hello", "World"]


# ════════════════════════════════════════════════════════════
#  @text — html escape
# ════════════════════════════════════════════════════════════

class TestTextHtml:
    def test_escape(self):
        assert _eval('@text.escape_html["<b>hi & there</b>"]') == "&lt;b&gt;hi &amp; there&lt;/b&gt;"
    def test_unescape(self):
        assert _eval('@text.unescape_html["&lt;b&gt;"]') == "<b>"


# ════════════════════════════════════════════════════════════
#  @text — slug / clean
# ════════════════════════════════════════════════════════════

class TestTextClean:
    def test_slug(self):
        assert _eval('@text.slug["Hello, World!"]') == "hello-world"
    def test_slug_spaces(self):
        assert _eval('@text.slug["foo  bar baz"]') == "foo-bar-baz"
    def test_clean(self):
        assert _eval('@text.clean["  hello   world  "]') == "hello world"
    def test_remove_digits(self):
        assert _eval('@text.remove_digits["a1b2c3"]') == "abc"
    def test_remove_punct(self):
        assert _eval('@text.remove_punct["hello, world!"]') == "hello world"
    def test_only_digits(self):
        assert _eval('@text.only_digits["abc123def456"]') == "123456"


# ════════════════════════════════════════════════════════════
#  @http — transpile smoke tests (no network calls)
# ════════════════════════════════════════════════════════════

class TestHttpTranspile:
    def _t(self, expr):
        code = transpile(parse(f"@var[__r__; {expr}]"))
        compile(code, "<t>", "exec")
        return code

    def test_get(self):       assert "requests.get(" in self._t('@http.get["https://x.com"]')
    def test_post(self):      assert "requests.post(" in self._t('@http.post["https://x.com"; {}]')
    def test_put(self):       assert "requests.put(" in self._t('@http.put["https://x.com"; {}]')
    def test_patch(self):     assert "requests.patch(" in self._t('@http.patch["https://x.com"; {}]')
    def test_delete(self):    assert "requests.delete(" in self._t('@http.delete["https://x.com"]')
    def test_head(self):      assert "requests.head(" in self._t('@http.head["https://x.com"]')
    def test_options(self):   assert "requests.options(" in self._t('@http.options["https://x.com"]')
    def test_form(self):      assert "data=" in self._t('@http.form["https://x.com"; {"k":"v"}]')
    def test_json(self):      assert ".json()" in self._t('@http.json[res]')
    def test_text(self):      assert ".text" in self._t('@http.text[res]')
    def test_bytes(self):     assert ".content" in self._t('@http.bytes[res]')
    def test_status(self):    assert ".status_code" in self._t('@http.status[res]')
    def test_ok(self):        assert ".ok" in self._t('@http.ok[res]')
    def test_headers_r(self): assert ".headers" in self._t('@http.headers[res]')
    def test_cookies(self):   assert ".cookies" in self._t('@http.cookies[res]')
    def test_url(self):       assert ".url" in self._t('@http.url[res]')
    def test_download(self):  assert "stream=True" in self._t('@http.download["https://x.com"; "f.bin"]')
    def _t_async(self, expr):
        code = transpile(parse(f"@var[__r__; {expr}]"))
        wrapped = f"async def __check__():\n" + "\n".join("    " + l for l in code.splitlines())
        compile(wrapped, "<t>", "exec")
        return code

    def test_async_get(self): assert "httpx" in self._t_async('@http.async_get["https://x.com"]')
    def test_async_post(self):assert "httpx" in self._t_async('@http.async_post["https://x.com"; {}]')
    def test_async_json(self):assert ".json()" in self._t_async('@http.async_json["https://x.com"]')
    def test_async_text(self):assert ".text" in self._t_async('@http.async_text["https://x.com"]')


class TestHttpSsrf:
    def test_localhost_blocked(self):
        from cruhon.core.libs.http_ import _check_url
        with pytest.raises(PermissionError):
            _check_url("http://localhost/secret")

    def test_private_blocked(self):
        from cruhon.core.libs.http_ import _check_url
        with pytest.raises(PermissionError):
            _check_url("http://192.168.1.1/admin")

    def test_public_allowed(self):
        from cruhon.core.libs.http_ import _check_url
        assert _check_url("https://api.example.com/data") == "https://api.example.com/data"

    def test_custom_timeout_no_conflict(self):
        code = transpile(parse('@var[r; @http.get["https://x.com"; timeout=60]]'))
        assert code.count("timeout=") == 1
        assert "timeout=60" in code

    def test_default_timeout_added(self):
        code = transpile(parse('@var[r; @http.get["https://x.com"]]'))
        assert f"timeout={30}" in code


class TestHttpSession:
    def _t(self, expr):
        code = transpile(parse(f"@var[__r__; {expr}]"))
        compile(code, "<t>", "exec")
        return code

    def test_session_create(self):
        assert "requests.Session()" in self._t('@http.session[]')

    def test_session_get(self):
        assert ".get(" in self._t('@http.session_get[s; "https://x.com"]')

    def test_session_post(self):
        assert ".post(" in self._t('@http.session_post[s; "https://x.com"; {}]')

    def test_session_put(self):
        assert ".put(" in self._t('@http.session_put[s; "https://x.com"; {}]')

    def test_session_patch(self):
        assert ".patch(" in self._t('@http.session_patch[s; "https://x.com"; {}]')

    def test_session_delete(self):
        assert ".delete(" in self._t('@http.session_delete[s; "https://x.com"]')

    def test_session_close(self):
        assert ".close()" in self._t('@http.session_close[s]')


# ════════════════════════════════════════════════════════════
#  @csv
# ════════════════════════════════════════════════════════════

class TestCsvRead:
    def test_read(self, in_tmp):
        (in_tmp / "d.csv").write_text("name,age\nAli,25\nVeli,30\n")
        rows = _eval('@csv.read["d.csv"]')
        assert rows == [{"name": "Ali", "age": "25"}, {"name": "Veli", "age": "30"}]

    def test_read_custom_delimiter(self, in_tmp):
        (in_tmp / "d.csv").write_text("name;age\nAli;25\n")
        rows = _eval('@csv.read["d.csv"; ";"]')
        assert rows[0] == {"name": "Ali", "age": "25"}

    def test_rows(self, in_tmp):
        (in_tmp / "d.csv").write_text("a,b\n1,2\n3,4\n")
        rows = _eval('@csv.rows["d.csv"]')
        assert rows == [["a", "b"], ["1", "2"], ["3", "4"]]

    def test_headers(self, in_tmp):
        (in_tmp / "d.csv").write_text("x,y,z\n1,2,3\n")
        assert _eval('@csv.headers["d.csv"]') == ["x", "y", "z"]

    def test_read_string(self):
        rows = _eval('@csv.read_string["name,age\\nAli,25\\n"]')
        assert rows == [{"name": "Ali", "age": "25"}]


class TestCsvWrite:
    def test_write_and_read(self, in_tmp):
        _run('@csv.write["out.csv"; [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]]')
        rows = _eval('@csv.read["out.csv"]')
        assert rows == [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]

    def test_write_rows(self, in_tmp):
        _run('@csv.write_rows["out.csv"; [["a","b"],[1,2],[3,4]]]')
        rows = _eval('@csv.rows["out.csv"]')
        assert rows[0] == ["a", "b"]

    def test_append(self, in_tmp):
        _run('@csv.write["out.csv"; [{"x": "1"}]]')
        _run('@csv.append["out.csv"; {"x": "2"}]')
        rows = _eval('@csv.read["out.csv"]')
        assert len(rows) == 2
        assert rows[1]["x"] == "2"


class TestCsvQuery:
    def test_filter(self):
        rows = [{"name": "Ali", "age": "25"}, {"name": "Veli", "age": "30"}]
        result = [r for r in rows if r.get("name") == "Ali"]
        assert result == [{"name": "Ali", "age": "25"}]

    def test_filter_inline(self):
        code = transpile(parse(
            '@var[rows; [{"k": "a"}, {"k": "b"}]]\n'
            '@var[r; @csv.filter[rows; "k"; "a"]]'
        ))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["r"] == [{"k": "a"}]

    def test_col(self):
        code = transpile(parse(
            '@var[rows; [{"name": "Ali", "age": "25"}, {"name": "Veli", "age": "30"}]]\n'
            '@var[names; @csv.col[rows; "name"]]'
        ))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["names"] == ["Ali", "Veli"]

    def test_count(self):
        code = transpile(parse(
            '@var[rows; [{"a": 1}, {"a": 2}]]\n'
            '@var[n; @csv.count[rows]]'
        ))
        ns: dict = {}
        exec(compile(code, "<t>", "exec"), ns)
        assert ns["n"] == 2

    def test_to_json(self, in_tmp):
        (in_tmp / "d.csv").write_text("name,age\nAli,25\n")
        result = _eval('@csv.to_json["d.csv"]')
        parsed = json.loads(result)
        assert parsed == [{"name": "Ali", "age": "25"}]

    def test_to_json_indent(self, in_tmp):
        (in_tmp / "d.csv").write_text("name,age\nAli,25\n")
        result = _eval('@csv.to_json["d.csv"; 2]')
        assert "\n" in result
