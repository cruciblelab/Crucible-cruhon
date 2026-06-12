# Cruhon Library Support

Cruhon wraps Python libraries with its own syntax.
The user must have the relevant Python library already installed when using `@import[lib]`.

---

## ✅ Any Python standard-library module just works

As of the stdlib passthrough, **`@import[<module>]` accepts any module in the
Python standard library** — no per-module registration needed. The transpiler
checks `sys.stdlib_module_names`, so these all work out of the box:

```clpy
@import[sqlite3]
@import[collections]
@import[hashlib]
@import[csv]
@import[itertools]
@import[subprocess]
@import[uuid]
@import[secrets]
# … every stdlib module
```

Once imported, call into them with plain Python expressions:

```clpy
@import[sqlite3]
@var[conn; sqlite3.connect("data.db")]
@var[rows; conn.execute("SELECT * FROM users").fetchall()]
```

Third-party packages (not in the stdlib) must be registered explicitly — see
the table below and the Contributing section.

---

## ✅ Registered third-party libraries

| Cruhon               | Python          |
|----------------------|-----------------|
| `@import[requests]`  | `requests`      |
| `@import[discord]`   | `discord.py`    |
| `@import[httpx]`     | `httpx`         |

---

## ✨ Helper namespaces (simplified, non-coder friendly)

These are Cruhon-native command sets that wrap stdlib modules with a far
simpler surface. You do **not** need `@import` for them.

### Core namespaces

| Namespace   | Wraps                                   | Commands |
|-------------|-----------------------------------------|----------|
| `@file.*`   | `pathlib` / `os` / `shutil` / `glob` / `tempfile` | read, write, append, copy, move, glob, mkdir, json, touch, symlink, chmod, stat… |
| `@date.*`   | `datetime` / `time` / `calendar` / `zoneinfo` | now, format, parse, add, diff, weekday, timezone, UTC, ISO calendar… |
| `@text.*`   | `re` / `str` / `textwrap` / `html` | upper, lower, split, replace, regex, encode, decode, slug, partition… |
| `@http.*`   | `requests` / `httpx`                    | get, post, put, delete, upload, auth, async_get, async_post… |
| `@json.*`   | `json`                                  | load, dump |
| `@store.*`  | in-memory key/value                     | set, get, clear |
| `@ctx.*`    | execution context dict                  | set, get, push, pop |

### Extended namespaces (stdlib wrappers)

| Namespace   | Wraps                                   | Commands |
|-------------|-----------------------------------------|----------|
| `@crypto.*` | `hashlib` / `hmac` / `secrets` / `base64` / `uuid` | md5, sha256, hash, pbkdf2, scrypt, hmac, token, uuid, b64_encode… |
| `@log.*`    | `logging`                               | setup, debug, info, warning, error, to_file, get, child… |
| `@config.*` | `configparser` / `json` / `tomllib` / `os.environ` | load, save, get, set, keys, dotenv, env… |
| `@shell.*`  | `subprocess` / `os` / `sys` / `shutil`  | run, output, lines, code, ok, bg, kill, terminate, wait, env… |
| `@archive.*`| `zipfile` / `tarfile` / `gzip` / `bz2` / `lzma` | zip, unzip, tar, untar, gzip, gunzip, bzip2, lzma… |
| `@mail.*`   | `smtplib` / `imaplib` / `email`         | send, send_html, imap_connect, imap_search, imap_fetch… |
| `@csv.*`    | `csv`                                   | read, write, filter, to_json… |

### Python stdlib wrappers (new in v2.1)

One-line access to the most-used Python standard libraries. No `@import` needed.

| Namespace        | Wraps          | Commands |
|------------------|----------------|----------|
| `@random.*`      | `random`       | random, randint, randrange, uniform, choice, choices, sample, shuffle, seed, gauss… |
| `@collections.*` | `collections`  | Counter, defaultdict, deque, namedtuple, OrderedDict, ChainMap… |
| `@itertools.*`   | `itertools`    | chain, cycle, product, permutations, combinations, groupby, accumulate, islice, flatten, pairwise… |
| `@functools.*`   | `functools`    | reduce, partial, lru_cache, cache, cached_property, wraps, total_ordering, singledispatch… |
| `@sys.*`         | `sys`          | argv, exit, path, version, platform, getsizeof, maxsize, stdin/out/err… |
| `@io.*`          | `io`           | StringIO, BytesIO, read, write, getvalue, seek, tell, open… |
| `@copy.*`        | `copy`         | copy, deepcopy, replace |
| `@base64.*`      | `base64`       | encode, decode, urlsafe_encode, urlsafe_decode, b32/b16… |
| `@url.*`         | `urllib.parse` | parse, join, quote, unquote, encode, parse_qs, scheme, netloc, path, query… |
| `@statistics.*`  | `statistics`   | mean, fmean, median, mode, multimode, quantiles, stdev, variance, correlation… |
| `@contextlib.*`  | `contextlib`   | contextmanager, suppress, nullcontext, redirect_stdout, closing, ExitStack… |
| `@enum.*`        | `enum`         | Enum, IntEnum, StrEnum, Flag, auto, create, unique, names, values… |
| `@dataclasses.*` | `dataclasses`  | dataclass, field, asdict, astuple, fields, replace, is_dataclass, make_dataclass… |
| `@typing.*`      | `typing`       | Optional, Union, List, Dict, Tuple, Any, Callable, cast, TypeVar, Literal… |
| `@threading.*`   | `threading`    | Thread, Lock, RLock, Event, Semaphore, Condition, Barrier, Timer, current_thread… |
| `@queue.*`       | `queue`        | Queue, LifoQueue, PriorityQueue, SimpleQueue, put, get, empty, full, qsize… |
| `@heapq.*`       | `heapq`        | heappush, heappop, heapify, heappushpop, heapreplace, nlargest, nsmallest, merge |
| `@bisect.*`      | `bisect`       | bisect_left, bisect_right, bisect, insort_left, insort_right, insort |
| `@operator.*`    | `operator`     | itemgetter, attrgetter, methodcaller, add, sub, mul, eq, lt, contains… |
| `@pprint.*`      | `pprint`       | print, format, pp, isreadable, isrecursive, saferepr, PrettyPrinter |

### More stdlib wrappers (expanded in v2.3)

Backing namespaces for the `cruhon-shortcuts` plugin. No `@import` needed.

| Namespace        | Wraps          | Commands |
|------------------|----------------|----------|
| `@string.*`      | `string`       | ascii_letters, ascii_lowercase, ascii_uppercase, digits, hexdigits, octdigits, punctuation, whitespace, printable, template, substitute, safe_substitute, formatter, capwords, ascii_to_int, int_to_ascii, filter, exclude, count_in, maketrans, translate, random_lower, random_upper, random_digits_str |
| `@struct.*`      | `struct`       | pack, unpack, unpack_list, first, pack_into, unpack_from, iter_unpack, calcsize, compile, pad, byte_order, to_hex, from_hex_str, native |
| `@zlib.*`        | `zlib`         | compress, decompress, decompress_text, compress_b64, decompress_b64, compress_str, decompress_str, crc32, crc32_hex, adler32, adler32_hex, compressor, decompressor, ratio, saved_bytes, is_zlib |
| `@calendar.*`    | `calendar`     | is_leap, leap_days, month_range, days_in_month, weekday, month_name, month_abbr, day_name, day_abbr, month_dates, year_dates, month_text, year_text, weekheader, is_weekday, is_weekend, first_weekday_of, get_first_weekday, day_of_year, week_of_year, quarter, next_month, prev_month, timegm |
| `@email.*`       | `email`        | message, make, set_content, add_html, set_header, attach_file, attach_text, attach_bytes, parse, parse_bytes, subject, sender, recipients, cc, bcc, reply_to, date_header, message_id, content_type, header, headers, body, html_body, is_multipart, parts, as_string, to_bytes, all_attachments, set_cc, set_bcc, set_reply_to, parse_address, format_address, valid_address, address_list |

### Data & format wrappers (new in v2.4)

Standard-library backed. No `@import` needed.

| Namespace      | Wraps                   | Commands |
|----------------|-------------------------|----------|
| `@xml.*`       | `xml.etree.ElementTree` | parse, from_string, to_string, find, find_all, find_text, children, iter, count, tag, text, attrib, get, to_dict |
| `@toml.*`      | `tomllib`               | loads, load, get, keys, has (read-only — see note below) |
| `@diff.*`      | `difflib`               | ratio, quick_ratio, is_similar, unified, context, ndiff, lines, close_matches, best_match |
| `@decimal.*`   | `decimal`               | make, to_float, to_str, to_int, add, sub, mul, div, sum, round, quantize, floor, ceil, sqrt, abs, compare, is_zero |
| `@fraction.*`  | `fractions`             | make, from_float, from_str, numerator, denominator, to_float, to_str, to_tuple, add, sub, mul, div, limit |
| `@ip.*`        | `ipaddress`             | address, network, interface, version, is_private, is_global, is_loopback, is_multicast, hosts, num_addresses, netmask, broadcast, network_address, contains, supernet, to_int, from_int |
| `@platform.*`  | `platform`              | system, release, version, platform, node, machine, processor, architecture, python_version, python_version_tuple, python_impl, python_compiler, uname, is_windows, is_linux, is_mac, is_64bit |
| `@unicode.*`   | `unicodedata`           | name, lookup, category, bidirectional, combining, mirrored, numeric, digit, decimal, normalize, nfc, nfd, nfkc, nfkd, strip_accents, unidata_version |
| `@binascii.*`  | `binascii`              | hexlify, unhexlify, b2a_hex, a2b_hex, b2a_base64, a2b_base64, crc32, crc_hqx |
| `@shlex.*`     | `shlex`                 | split, join, quote, quote_all |

`@decimal` uses exact base-10 arithmetic — `@decimal.add["0.1"; "0.2"]`
returns `0.3` exactly, with no binary rounding error. `@toml` is read-only
(`tomllib` is a parser); to write TOML build the string or use a
third-party package.

### Plugin namespaces

| Namespace   | Type    | Commands |
|-------------|---------|----------|
| `@db.*`     | plugin  | 138 commands — see `mods/cruhon-db` |
| `@discord.*`| plugin  | ~60 commands — see `mods/cruhon-discord` |

### Shortcut plugin (`cruhon-shortcuts`)

A fully configurable shortcut layer over **every** namespace. It does not add
a namespace of its own — instead it installs:

- **Global aliases** — `@read` → `@file.read`, `@now` → `@date.now`,
  `@uuid` → `@crypto.uuid`, `@rand` → `@random.randint`, `@mean` →
  `@statistics.mean`, `@compress_b64` → `@zlib.compress_b64`, and hundreds more.
- **Method aliases** — `@file.cat`, `@file.ls`, `@date.ts`, `@http.fetch`, …
- **200+ new convenience methods** — `@file.head`, `@file.tail`, `@file.grep`,
  `@date.tomorrow`, `@date.age`, `@random.password`, `@statistics.summary`,
  `@collections.histogram`, `@string.random`, `@struct.hexdump`, …

Everything is toggleable from `mods/cruhon-shortcuts/mod.json`:

```json
{
  "groups": "all",
  "global_aliases": true,
  "method_aliases": true,
  "disabled": ["@get[", "@post["],
  "custom": { "@slurp[": "@file.read[" }
}
```

`groups` accepts `"all"` or any subset of: `file`, `http`, `date`, `text`,
`math`, `crypto`, `collections`, `system`, `data`, `stdlib`, `types`, `io`,
`binary`. See `mods/cruhon-shortcuts/` for the full per-group command list.

### Extended shortcut plugin (`cruhon-shortcuts-pro`)

A second shortcut plugin (`mods/cruhon-shortcuts-pro/`) with higher-level
composite operations. Can be loaded alongside `cruhon-shortcuts` — all
global-rewrite names are distinct. Configuration via `mod.json`:

```json
{
  "groups": "all",
  "disabled": [],
  "custom": {}
}
```

`groups` accepts `"all"` or any subset of: `math`, `lists`, `dicts`, `text`,
`logic`.

| Group    | Highlights |
|----------|-----------|
| `math`   | `@clamp`, `@lerp`, `@sign`, `@percent`, `@frange`, `@gcd`, `@lcm`, `@factorial`, `@sin/cos/tan`, `@degrees`, `@log2/log10`, `@is_close`, `@math.inf/e/tau/nan` |
| `lists`  | `@window`, `@transpose`, `@unzip`, `@rotate_list`, `@head_n`, `@tail_n`, `@interleave`, `@dedupe`, `@flat`, `@zip_all`, `@cartesian`, `@chunks`, `@sorted_by`, `@pairs`, `@take_while`, `@drop_while` |
| `dicts`  | `@pick_keys`, `@omit_keys`, `@map_vals`, `@filter_keys`, `@deep_merge`, `@dict_diff`, `@flat_dict`, `@swap_kv`, `@rename_key`, `@key_of`, `@values_where` |
| `text`   | `@camel_case`, `@snake_case`, `@kebab_case`, `@pascal_case`, `@word_freq`, `@normalize_ws`, `@excerpt`, `@initials`, `@squeeze`, `@ordinal`, `@pluralize`, `@de_accent`, `@wrap_lines` |
| `logic`  | `@coalesce`, `@first_true`, `@count_if`, `@any_match`, `@all_match`, `@none_match`, `@first_where`, `@last_where`, `@default_if_none`, `@safe_get`, `@group_by`, `@tally` |

### Data shortcut plugin (`cruhon-shortcuts-data`)

A third shortcut plugin (`mods/cruhon-shortcuts-data/`) for the v2.4 data
& format namespaces. Loads cleanly alongside the other two shortcut
plugins. Configuration via `mod.json`:

```json
{
  "groups": "all",
  "disabled": [],
  "custom": {}
}
```

`groups` accepts `"all"` or any subset of: `format`, `numbers`, `system`.

| Group     | Highlights |
|-----------|-----------|
| `format`  | `@xml_parse`, `@xml_load`, `@xml_dict`, `@xml_text`, `@toml_load`, `@toml_get`, `@diff_ratio`, `@similar`, `@closest`, `@fuzzy`, plus `@xml.text_all`, `@diff.changed`, `@toml.flatten` |
| `numbers` | `@dec_of`, `@dec_add`, `@dec_round`, `@money`, `@frac`, `@frac_str`, `@frac_add`, plus `@decimal.money`, `@decimal.percent`, `@decimal.average`, `@fraction.reciprocal` |
| `system`  | `@ip_addr`, `@is_private_ip`, `@ip_hosts`, `@os_name`, `@py_version`, `@machine`, `@hostname`, `@char_name`, `@strip_accents`, `@hexlify`, `@unhexlify`, `@sh_split`, plus `@ip.is_ipv4/is_ipv6`, `@platform.summary`, `@binascii.hex_spaced` |

### `@file` quick reference

```clpy
@file.write["notes.txt"; "hello"]      # overwrite (creates parent dirs)
@file.append["notes.txt"; " more"]     # append
@var[text; @file.read["notes.txt"]]    # read full text
@var[rows; @file.lines["notes.txt"]]   # list of lines
@file.copy["a.txt"; "b.txt"]           # copy / move / rename / delete
@var[found; @file.glob["*.txt"]]       # glob, list, walk
@file.write_json["d.json"; {"k": 1}]   # JSON read/write
@var[data; @file.read_json["d.json"]]
```

All path-taking `@file` commands are sandboxed to the working directory —
traversal outside cwd (`../../etc/passwd`) is blocked.

### `@date` quick reference

```clpy
@var[now; @date.now[]]
@var[stamp; @date.format["%Y-%m-%d %H:%M"]]   # format now
@var[when; @date.parse["2024-03-10"; "%Y-%m-%d"]]
@var[future; @date.add[@date.now[]; days=7]]   # arithmetic
@var[gap; @date.diff_days[future; @date.now[]]]
@var[name; @date.weekday_name[@date.now[]]]    # "Monday"
@var[d; @date.make[2024; 1; 15]]               # build a date
```

`@date` commands accept either a datetime object or an ISO string.

---

## ❌ Unsupported Library Error

```
@import[pandas]
# Error: Library 'pandas' is not yet supported in Cruhon.
# See library.md for the full list.
```

This only happens for **third-party** packages that haven't been registered.
Standard-library modules never hit this error.

---

## Contributing

Adding a third-party library wrapper is straightforward:

1. Add `register_lib("libname", "python_module")` to `cruhon/core/registry.py`
2. If needed, customize method calls with `register_lib_call()`
3. Add an entry to this file
4. Open a PR

Libraries can also be added as community mods — see `mods/README.md`

---

## Community

- **Discord:** https://discord.gg/SPf5VZ6QPG
- **Email:** cruciblelab@hotmail.com
