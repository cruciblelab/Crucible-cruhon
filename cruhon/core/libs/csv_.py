"""
CSV stdlib wrappers for Cruhon — @csv.*

Covers the csv module so a non-coder can read, write, filter and convert
CSV files without knowing DictReader/DictWriter.

━━━ READ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @csv.read[path]                   → list of dicts (DictReader, first row = header)
  @csv.read[path; delimiter]        → custom delimiter
  @csv.rows[path]                   → list of lists (no header assumed)
  @csv.headers[path]                → list of column names from first row
  @csv.read_string[text]            → parse CSV string → list of dicts

━━━ WRITE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @csv.write[path; rows]            — list-of-dicts → file (header inferred)
  @csv.write[path; rows; fieldnames]— explicit column order
  @csv.append[path; row]            — append one dict row
  @csv.write_rows[path; rows]       — list-of-lists → file (no header)

━━━ QUERY / TRANSFORM ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @csv.filter[rows; col; value]     → rows where row[col] == value
  @csv.col[rows; name]              → list of values for one column
  @csv.count[rows]                  → number of rows
  @csv.to_json[path]                → read CSV, return JSON string
  @csv.to_json[path; indent]        → pretty JSON
"""
from ..registry import register_lib, register_lib_call

_MOD = "cruhon.core.libs.csv_"


def _csv_read(path_expr: str, delim_expr: str = None) -> str:
    delim = f", delimiter={delim_expr}" if delim_expr else ""
    return (
        f"(lambda _p: list(__import__('csv').DictReader("
        f"open(_p, newline='', encoding='utf-8'){delim})))({path_expr})"
    )


def _csv_rows(path_expr: str) -> str:
    return (
        f"(lambda _p: list(__import__('csv').reader("
        f"open(_p, newline='', encoding='utf-8'))))({path_expr})"
    )


def _csv_headers(path_expr: str) -> str:
    return (
        f"(lambda _p: next(__import__('csv').reader("
        f"open(_p, newline='', encoding='utf-8'))))({path_expr})"
    )


def _csv_write(path_expr: str, rows_expr: str, fields_expr: str = None) -> str:
    fields = (
        f"fieldnames={fields_expr}"
        if fields_expr else
        f"fieldnames=list({rows_expr}[0].keys()) if {rows_expr} else []"
    )
    return (
        f"(lambda _p, _rows: ("
        f"  (lambda _f, _rows: "
        f"    (__import__('csv').DictWriter(_f, {fields}, extrasaction='ignore').writeheader(),"
        f"     __import__('csv').DictWriter(_f, {fields}, extrasaction='ignore').writerows(_rows))"
        f"  )(open(_p, 'w', newline='', encoding='utf-8'), _rows)"
        f"))({path_expr}, {rows_expr})"
    )


def _csv_append(path_expr: str, row_expr: str) -> str:
    return (
        f"(lambda _p, _row: ("
        f"  (lambda _f: __import__('csv').DictWriter("
        f"    _f, fieldnames=list(_row.keys()), extrasaction='ignore'"
        f"  ).writerow(_row))(open(_p, 'a', newline='', encoding='utf-8'))"
        f"))({path_expr}, {row_expr})"
    )


def _csv_write_rows(path_expr: str, rows_expr: str) -> str:
    return (
        f"(lambda _p, _rows: __import__('csv').writer("
        f"  open(_p, 'w', newline='', encoding='utf-8')"
        f").writerows(_rows))({path_expr}, {rows_expr})"
    )


def register():
    register_lib("csv", "csv")

    # ── READ ─────────────────────────────────────────────────
    register_lib_call("csv", "read",
        lambda a: _csv_read(a[0], a[1] if len(a) > 1 else None))

    register_lib_call("csv", "rows",
        lambda a: _csv_rows(a[0]))

    register_lib_call("csv", "headers",
        lambda a: _csv_headers(a[0]))

    register_lib_call("csv", "read_string",
        lambda a: (
            f"list(__import__('csv').DictReader("
            f"__import__('io').StringIO({a[0]})))"
        ))

    # ── WRITE ────────────────────────────────────────────────
    register_lib_call("csv", "write",
        lambda a: _csv_write(a[0], a[1], a[2] if len(a) > 2 else None))

    register_lib_call("csv", "append",
        lambda a: _csv_append(a[0], a[1]))

    register_lib_call("csv", "write_rows",
        lambda a: _csv_write_rows(a[0], a[1]))

    # ── QUERY / TRANSFORM ────────────────────────────────────
    register_lib_call("csv", "filter",
        lambda a: f"[_r for _r in {a[0]} if str(_r.get({a[1]}, '')) == str({a[2]})]")

    register_lib_call("csv", "col",
        lambda a: f"[_r.get({a[1]}) for _r in {a[0]}]")

    register_lib_call("csv", "count",
        lambda a: f"len({a[0]})")

    register_lib_call("csv", "to_json",
        lambda a: (
            f"__import__('json').dumps("
            f"list(__import__('csv').DictReader(open({a[0]}, newline='', encoding='utf-8'))), "
            f"indent={a[1] if len(a)>1 else 'None'}, ensure_ascii=False)"
        ))
