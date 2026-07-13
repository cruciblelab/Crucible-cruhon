# Cruhon Library Reference

**v2.10.0 — 128 namespaces · 1875+ commands**

All built-in namespaces are available without `@import`. Just call them.

---

## Any Python standard-library module works with `@import`

`@import` accepts every module in the Python standard library — no registration
needed. The transpiler checks `sys.stdlib_module_names`:

```clpy
@import[sqlite3]
@import[hashlib]
@import[subprocess]
@import[uuid]
# … every stdlib module
```

Once imported, use plain Python expressions:

```clpy
@import[sqlite3]
@var[conn; sqlite3.connect("data.db")]
@var[rows; conn.execute("SELECT * FROM users").fetchall()]
```

Third-party packages not in the stdlib must be registered explicitly (see below).

---

## Registered third-party libraries

| Cruhon | Python |
|---|---|
| `@import[requests]` | `requests` |
| `@import[httpx]` | `httpx` |
| `@import[discord]` | `discord.py` |

---

## Built-in namespaces (no `@import` needed)

---

### Core — Cruhon-native

| Namespace | Wraps | Commands |
|---|---|---|
| `@file.*` | `pathlib` / `os` / `shutil` / `glob` / `tempfile` | abspath, append, basename, bytes, chmod, copy, copytree, cwd, delete, dirname, exists, expanduser, ext, glob, hardlink, home, is_dir, is_file, is_link, join, lines, list, mkdir, move, mtime, read, read_json, realpath, rename, rmdir, samefile, size, stat, stem, symlink, temp, tempdir, touch, walk, write, write_bytes, write_json |
| `@date.*` | `datetime` / `time` / `calendar` / `zoneinfo` | add, combine, day, days_in_month, diff, diff_days, diff_seconds, format, from_iso, from_timestamp, hour, is_weekend, iso, isocalendar, isoweek, isoyear, make, make_time, microsecond, minute, month, month_name, now, parse, replace, second, sleep, sub, timedelta, timestamp, timezone, to_timezone, today, total_seconds, utc, utcnow, weekday, weekday_name, year |
| `@text.*` | `re` / `str` / `textwrap` / `html` | capitalize, casefold, center, clean, contains, count, decode, dedent, encode, endswith, escape_html, expandtabs, fill, find, findall, format, groups, indent, index, is_alnum, is_alpha, is_ascii, is_decimal, is_digit, is_identifier, is_lower, is_numeric, is_printable, is_space, is_upper, join, len, lines, ljust, lower, lstrip, maketrans, match, only_digits, pad_left, pad_right, partition, remove_digits, remove_punct, repeat, replace, reverse, rindex, rjust, rpartition, rsplit, rstrip, search, slice, slug, split, split_re, startswith, strip, sub, swapcase, template, title, translate, truncate, unescape_html, upper, words, wrap, zfill |
| `@http.*` | `requests` / `httpx` | async_delete, async_get, async_json, async_patch, async_post, async_put, async_text, auth_get, auth_post, bytes, cookies, delete, download, elapsed, encoding, form, get, head, headers, json, ok, options, patch, post, put, raise_for_status, session, session_close, session_delete, session_get, session_patch, session_post, session_put, status, text, upload, url |
| `@crypto.*` | `hashlib` / `hmac` / `secrets` / `base64` / `uuid` | b64_decode, b64_encode, b64url_decode, b64url_encode, blake2b, blake2s, compare, hash, hash_bytes, hash_file, hex_decode, hex_encode, hmac, md5, pbkdf2, random_bytes, random_int, scrypt, sha1, sha256, sha3_256, sha3_512, sha512, token, token_bytes, token_url, uuid, uuid1, uuid3, uuid5 |
| `@log.*` | `logging` | child, clear, critical, debug, disable, enable, error, exception, format, get, handlers, info, set_level, setup, to_file, warning |
| `@config.*` | `json` / `tomllib` / `configparser` / `os.environ` | dotenv, env, env_all, env_del, env_set, get, has, keys, load, reload, save, sections, set |
| `@shell.*` | `subprocess` / `os` / `sys` / `shutil` | args, bg, bg_stdin, cd, code, communicate, cpu_count, cwd, env, env_all, env_del, env_set, exists, exit, home, hostname, kill, lines, ok, output, pid, pipe, platform, poll, python_version, returncode, run, terminate, username, wait, which |
| `@archive.*` | `zipfile` / `tarfile` / `gzip` / `bz2` / `lzma` | bunzip2, bzip2, gunzip, gzip, is_tar, is_zip, lzma, size, tar, tar_extract_one, tar_list, unlzma, untar, unzip, zip, zip_add, zip_extract_one, zip_list, zip_read |
| `@mail.*` | `smtplib` / `imaplib` / `email` | attach, body, close, connect, connect_tls, deliver, html_message, imap_close, imap_connect, imap_fetch, imap_fetch_all, imap_list, imap_search, imap_select, login, message, parse, send, send_html, send_with_attachment, sender, subject |
| `@csv.*` | `csv` | append, col, count, filter, headers, read, read_string, rows, to_json, write, write_rows |
| `@store.*` | in-memory dict | all, clear, delete, get, set |
| `@color.*` | ANSI codes | blue, bold, cyan, dim, green, red, reset, yellow |
| `@ctx.*` | `__ctx__` dict | clear, delete, get, pop, push, set |
| `@json.*` | `json` | dump, load, parse, pretty, read, stringify, write |

---

### Text & Math

| Namespace | Wraps | Commands |
|---|---|---|
| `@math.*` | `math` | abs, acos, asin, atan, atan2, ceil, clamp, comb, cos, degrees, dist, e, exp, factorial, floor, gcd, hypot, inf, isclose, isfinite, isinf, isnan, lcm, lerp, log, log10, log2, max, min, nan, perm, pi, pow, prod, radians, rand, random, round, sign, sin, sqrt, sum, tan, tau |
| `@random.*` | `random` | betavariate, choice, choices, expovariate, gauss, getstate, randint, random, randrange, sample, seed, setstate, shuffle, triangular, uniform |
| `@cmath.*` | `cmath` | acos, acosh, asin, asinh, atan, atanh, complex, conjugate, cos, cosh, e, exp, inf, is_close, is_finite, is_inf, is_nan, log, log10, modulus, nan, phase, pi, polar, rect, sin, sinh, sqrt, tan, tanh, tau |
| `@decimal.*` | `decimal` | abs, add, ceil, compare, div, floor, is_zero, make, mul, quantize, round, sqrt, sub, sum, to_float, to_int, to_str |
| `@fraction.*` | `fractions` | add, denominator, div, from_float, from_str, limit, make, mul, numerator, sub, to_float, to_str, to_tuple |
| `@statistics.*` | `statistics` | correlation, covariance, fmean, geometric_mean, harmonic_mean, linear_regression, mean, median, median_grouped, median_high, median_low, mode, multimode, pstdev, pvariance, quantiles, stdev, variance |
| `@textwrap.*` | `textwrap` | center, dedent, fill, indent, shorten, truncate, wrap |
| `@string.*` | `string` | ascii_letters, ascii_lowercase, ascii_to_int, ascii_uppercase, capwords, count_in, digits, exclude, filter, formatter, hexdigits, int_to_ascii, maketrans, octdigits, printable, punctuation, random_digits_str, random_lower, random_upper, safe_substitute, substitute, template, translate, whitespace |
| `@unicode.*` | `unicodedata` | bidirectional, category, combining, decimal, digit, lookup, mirrored, name, nfc, nfd, nfkc, nfkd, normalize, numeric, strip_accents, unidata_version |
| `@codecs.*` | `codecs` | decode, decode_err, encode, encode_err, hex, lookup, name, open, reader, rot13, unhex, unzip, writer, zip |
| `@colorsys.*` | `colorsys` | blend, from_hls, from_hsv, from_yiq, hex_to_hls, hex_to_hsv, hex_to_rgb, luminance, rgb_to_hex, to_hls, to_hsv, to_yiq |

---

### Data & Formats

| Namespace | Wraps | Commands |
|---|---|---|
| `@collections.*` | `collections` | ChainMap, Counter, OrderedDict, UserDict, UserList, UserString, chainmap_new_child, counter_most_common, counter_subtract, counter_update, defaultdict, deque, deque_append, deque_appendleft, deque_extend, deque_pop, deque_popleft, deque_rotate, namedtuple, ordered_move_to_end |
| `@itertools.*` | `itertools` | accumulate, chain, chain_from_iterable, combinations, combinations_with_replacement, compress, count, cycle, dropwhile, filterfalse, flatten, groupby, islice, pairwise, permutations, product, repeat, starmap, takewhile, tee, zip_longest |
| `@functools.*` | `functools` | cache, cached_property, cmp_to_key, lru_cache, partial, reduce, singledispatch, singledispatchmethod, total_ordering, update_wrapper, wraps |
| `@operator.*` | `operator` | abs, add, and_, attrgetter, concat, contains, delitem, eq, floordiv, ge, getitem, gt, itemgetter, le, length_hint, lt, methodcaller, mod, mul, ne, neg, not_, or_, pos, pow, setitem, sub, truediv, xor |
| `@xml.*` | `xml.etree.ElementTree` | attrib, children, count, find, find_all, find_text, from_string, get, iter, parse, tag, text, to_dict, to_string |
| `@toml.*` | `tomllib` | get, has, keys, load, loads |
| `@yaml.*` | `pyyaml` | dump_file, dumps, from_json, get, load_all, load_file, loads, parse, stringify, to_json |
| `@diff.*` | `difflib` | best_match, close_matches, context, is_similar, lines, ndiff, quick_ratio, ratio, unified |
| `@re.*` | `re` | compile, count, escape, findall, finditer, fullmatch, group1, groups, is_match, match, named, replace_first, search, split, sub, subn |
| `@struct.*` | `struct` | byte_order, calcsize, compile, first, from_hex_str, iter_unpack, native, pack, pack_into, pad, to_hex, unpack, unpack_from, unpack_list |
| `@binascii.*` | `binascii` | a2b_base64, a2b_hex, b2a_base64, b2a_hex, crc32, crc_hqx, hexlify, unhexlify |
| `@zlib.*` | `zlib` | adler32, adler32_hex, compress, compress_b64, compress_str, compressor, crc32, crc32_hex, decompress, decompress_b64, decompress_str, decompress_text, decompressor, is_zlib, ratio, saved_bytes |
| `@base64.*` | `base64` | b16decode, b16encode, b32decode, b32encode, decode, decode_bytes, encode, encode_bytes, urlsafe_decode, urlsafe_encode |
| `@pickle.*` | `pickle` | append_to, compress, copy, decompress, dumps, dumps_proto, from_base64, from_hex, is_pickle, load, load_gz, load_list, loads, protocol, save, save_gz, size, to_base64, to_hex |
| `@shelve.*` | `shelve` | all, clear, close, count, delete, get, has, increment, items, keys, open, pop, rename, set, setdefault, sync, update, values |
| `@plist.*` | `plistlib` | dumps, dumps_binary, fmt, from_json, get, has, items, keys, load, load_binary, loads, loads_binary, merge, remove, save, save_binary, set, to_dict, to_json, values |
| `@reprlib.*` | `reprlib` | recursive, repr, short |
| `@graphlib.*` | `graphlib` | add, done, is_dag, new, ready, sort, sort_groups |
| `@email.*` | `email` | add_html, address_list, all_attachments, as_string, attach_bytes, attach_file, attach_text, bcc, body, cc, content_type, date_header, format_address, header, headers, html_body, is_multipart, make, message, message_id, parse, parse_address, parse_bytes, parts, recipients, reply_to, sender, set_bcc, set_cc, set_content, set_header, set_reply_to, subject, to_bytes, valid_address |
| `@calendar.*` | `calendar` | day_abbr, day_name, day_of_year, days_in_month, first_weekday_of, get_first_weekday, is_leap, is_weekday, is_weekend, leap_days, month_abbr, month_dates, month_name, month_range, month_text, next_month, prev_month, quarter, timegm, week_of_year, weekday, weekheader, year_dates, year_text |

---

### File & Path

Path manipulation is covered by `@file.*` (`abspath`, `dirname`, `basename`,
`join`, `stem`, `ext`, `exists`, `is_dir`, `is_file`, `realpath`, …) — there
is no separate `@pathlib.*` namespace.

| Namespace | Wraps | Commands |
|---|---|---|
| `@glob.*` | `glob` | any, by_ext, by_ext_r, count, dirs, dirs_r, escape, files, files_r, first, glob, largest, newest, oldest, rglob, sort_by_date, sort_by_name, sort_by_size |
| `@tempfile.*` | `tempfile` | dir, file, gettempdir, in_dir, in_dir_dir, mkstemp, named |
| `@fnmatch.*` | `fnmatch` | all_match, any_match, filter, ifilter, imatch, match, reject, translate |
| `@fileinput.*` | `fileinput` | contains, count_chars, count_lines, count_words, grep, grep_n, head, lines, lines_multi, lines_raw, numbered, replace, replace_save, slice, strip_empty, tail, unique_lines |
| `@stat.*` | `stat` | executable, filemode, is_dir, is_exec, is_file, is_link, is_readable, is_writable, mode, octal, of, perms, readable, writable |
| `@shutil.*` | `shutil` | archive_formats, chown, copy, copy2, copy_data, copy_mode, copy_stat, copy_tree, disk_usage, free, make_archive, move, rm, rmtree, terminal_size, unpack, which |
| `@filecmp.*` | `filecmp` | clear_cache, common, compare, diff_files, dircmp, equal, left_only, right_only, same_files, shallow |
| `@linecache.*` | `linecache` | check, clear, count, line, lines |
| `@mmap.*` | `mmap` | close, contains, count, find, flush, get, length, open, put, read, search, size, slice |
| `@zipapp.*` | `zipapp` | copy, create, interpreter, is_archive, main |
| `@configparser.*` | `configparser` | add_section, dumps, get, getbool, getfloat, getint, has, has_section, items, keys, load, loads, new, read_dict, remove_key, remove_section, save, sections, set, to_dict |

---

### OS & System

| Namespace | Wraps | Commands |
|---|---|---|
| `@os.*` | `os` | env, path |
| `@sys.*` | `sys` | argv, argv_get, executable, exit, getrecursionlimit, getsizeof, maxsize, modules, path, path_append, path_insert, platform, prefix, setrecursionlimit, stderr, stdin, stdout, version, version_info |
| `@platform.*` | `platform` | architecture, is_64bit, is_linux, is_mac, is_windows, machine, node, platform, processor, python_compiler, python_impl, python_version, python_version_tuple, release, system, uname, version |
| `@gc.*` | `gc` | collect, count, disable, enable, freeze, garbage, is_enabled, is_tracked, objects, referents, referrers, set_threshold, stats, threshold, unfreeze |
| `@inspect.*` | `inspect` | annotations, closure, comments, defaults, doc, file, frame, is_abstract, is_async_generator, is_builtin, is_class, is_coroutine, is_function, is_generator, is_generator_function, is_method, is_module, is_routine, members, module, mro, parameters, signature, source, source_file, source_lines, stack, unwrap |
| `@traceback.*` | `traceback` | extract, format, format_exception, format_frames, frames, message, print, print_stack, stack |
| `@warnings.*` | `warnings` | always, deprecated, error, filter, ignore, once, reset, warn |
| `@weakref.*` | `weakref` | count, deref, dict, finalize, is_alive, key_dict, proxy, ref, refs, set |
| `@types.*` | `types` | cell, is_async_generator, is_builtin, is_code, is_coroutine, is_frame, is_function, is_generator, is_lambda, is_method, is_module, is_traceback, method, module, namespace, new_class, readonly, resolve_bases |
| `@abc.*` | `abc` | abstract_methods, cache_token, is_abstract, is_instance, is_subclass, register |
| `@signal.*` | `signal` | alarm, default, describe, get, get_timer, ignore, name, number, on, pause, send, set_timer, valid |
| `@atexit.*` | `atexit` | register, run, unregister |
| `@locale.*` | `locale` | atof, atoi, currency, currency_intl, decimal, delocalize, encoding, format, get, normalize, number, set |
| `@gettext.*` | `gettext` | find, install, plural, t, translation |
| `@sysconfig.*` | `sysconfig` | path, path_names, paths, platform, var, vars, version |
| `@resource.*` | `resource` | limit, max_rss, page_size, set_limit, sys_time, usage, user_time |
| `@errno.*` | `errno` | EACCES, EAGAIN, EBADF, EEXIST, EINVAL, EISDIR, ENOENT, ENOTDIR, ENOTEMPTY, EPERM, all, code, description, name |
| `@getpass.*` | `getpass` | ask, password, user |
| `@numbers.*` | `numbers` | is_complex, is_integral, is_number, is_rational, is_real |

---

### Networking

| Namespace | Wraps | Commands |
|---|---|---|
| `@socket.*` | `socket` | accept, bind, close, connect, file, fqdn, free_port, host_to_ip, hostname, ip_to_host, is_open, listen, local, peer, recv, recv_from, resolve, reuse, send, send_to, server, set_timeout, shutdown, tcp, udp |
| `@ssl.*` | `ssl` | cert_dict, check_hostname, ciphers, context, load_ca, pem_to_der, server_cert, server_context, set_ciphers, unverified, verify_paths, wrap |
| `@ftp.*` | `ftplib` | command, connect, connect_tls, cwd, delete, details, download, list, mkdir, new, passive, pwd, quit, rename, rmdir, size, upload |
| `@pop3.*` | `poplib` | connect, connect_ssl, count, delete, get, list, login, noop, quit, reset, size, text, top, uidl |
| `@xmlrpc.*` | `xmlrpc.client` | binary, call, client, datetime, dumps, loads |
| `@httpserver.*` | `http.server` | close, files, handle_one, handler, port, serve, serve_async, server, stop, threaded |
| `@selectors.*` | `selectors` | close, count, modify, new, read, register, unwatch, wait, watch_read, watch_write, watched, write |
| `@ip.*` | `ipaddress` | address, broadcast, contains, from_int, hosts, interface, is_global, is_loopback, is_multicast, is_private, netmask, network, network_address, num_addresses, supernet, to_int, version |
| `@url.*` | `urllib.parse` | build, decode, encode, join, netloc, parse, parse_qs, path, query, quote, scheme, split, unquote, unsplit |
| `@html.*` | `html` / `re` | escape, images, links, strip_tags, tags, text, unescape |
| `@webbrowser.*` | `webbrowser` | get, open, open_new, open_tab |
| `@mimetypes.*` | `mimetypes` | add, encodings_map, extension, extensions, full, guess, init, is_image, is_text, suffix_map, types |

Async HTTP (backed by `httpx`) is covered by `@http.async_*` (`async_get`,
`async_post`, `async_put`, `async_patch`, `async_delete`, `async_json`,
`async_text`) — there is no separate `@httpx.*` namespace.

---

### Concurrency

| Namespace | Wraps | Commands |
|---|---|---|
| `@asyncio.*` | `asyncio` | all_tasks, cancel, close_loop, condition, current_task, done, ensure, event, gather, iscoroutine, isfuture, istask, lock, loop, new_loop, open, queue, result, run, run_loop, semaphore, serve, set_loop, shield, sleep, task, timeout, wait_for |
| `@threading.*` | `threading` | Barrier, BoundedSemaphore, Condition, Event, Lock, RLock, Semaphore, Thread, Timer, acquire, active_count, current_thread, daemon, enumerate, event_clear, event_is_set, event_set, event_wait, get_ident, is_alive, join, local, main_thread, release, settrace, start |
| `@multiprocessing.*` | `multiprocessing` | active, apply, array, cpus, current, event, imap, join, lock, manager, map, pipe, pool, process, queue, semaphore, set_start, starmap, start, value |
| `@futures.*` | `concurrent.futures` | as_done, cancel, cancelled, done, exception, map, on_done, process_map, processes, result, running, shutdown, submit, thread_map, threads, wait, wait_first |
| `@queue.*` | `queue` | LifoQueue, PriorityQueue, Queue, SimpleQueue, empty, full, get, get_nowait, join, put, put_nowait, qsize, task_done |
| `@sched.*` | `sched` | after, at, cancel, empty, new, queue, run |

---

### Serialization & Database

| Namespace | Wraps | Commands |
|---|---|---|
| `@sqlite.*` | `sqlite3` | all_rows, as_dict, as_dicts, avg, backup, begin, changes, close, column_types, columns, commit, connect, count, create_table, delete, delete_many, drop_table, execute, executemany, executescript, exists, export_csv, export_json, fetchall, fetchmany, fetchone, find, find_one, foreign_keys, import_csv, in_transaction, index_create, index_drop, insert, insert_many, integrity_check, last_id, max_val, min_val, page_count, page_size, pragma, query, query_one, release, rollback, rollback_to, row_as_dict, run, savepoint, scalar, search, set_timeout, sum, table_exists, tables, to_dicts, truncate, update, upsert, user_version, vacuum, views, wal_mode |
| `@pickle.*` | `pickle` | append_to, compress, copy, decompress, dumps, dumps_proto, from_base64, from_hex, is_pickle, load, load_gz, load_list, loads, protocol, save, save_gz, size, to_base64, to_hex |
| `@shelve.*` | `shelve` | all, clear, close, count, delete, get, has, increment, items, keys, open, pop, rename, set, setdefault, sync, update, values |
| `@plist.*` | `plistlib` | dumps, dumps_binary, fmt, from_json, get, has, items, keys, load, load_binary, loads, loads_binary, merge, remove, save, save_binary, set, to_dict, to_json, values |
| `@configparser.*` | `configparser` | add_section, dumps, get, getbool, getfloat, getint, has, has_section, items, keys, load, loads, new, read_dict, remove_key, remove_section, save, sections, set, to_dict |

---

### Testing & Profiling

| Namespace | Wraps | Commands |
|---|---|---|
| `@unittest.*` | `unittest` | assert_equal, assert_in, assert_raises, assert_true, count, discover, failures, mock, passed, patch, run, run_suite, suite |
| `@doctest.*` | `doctest` | examples, module, object, passed, run |
| `@timeit.*` | `timeit` | auto, best, each, repeat, run |
| `@profile.*` | `cProfile` | calls, dump, print, run, time |
| `@tracemalloc.*` | `tracemalloc` | current, diff, is_tracing, snapshot, start, stop, top |

---

### Developer Tools

| Namespace | Wraps | Commands |
|---|---|---|
| `@ast.*` | `ast` | children, classes, compile, constants, docstring, dump, fields, fix, functions, imports, increment, is_valid, literal, names, node_types, parse, parse_eval, unparse, walk |
| `@dis.*` | `dis` | code, code_info, consts, disasm, instructions, names, opname, opnames, stack_size, varnames |
| `@tokenize.*` | `tokenize` | COMMENT, DEDENT, INDENT, NAME, NEWLINE, NUMBER, OP, STRING, comments, count, end, keywords, line, names, numbers, ops, start, string, strings, tok_name, tokens, type, unique_names, untokenize |
| `@keyword.*` | `keyword` | all, count, is_keyword, is_soft, soft |
| `@importlib.*` | `importlib` | attr, exists, find, from_path, invalidate, load, origin, reload, spec |
| `@pdb.*` | `pdb` | bp, breakpoint, clear_all, clear_bp, list_bps, new, pm, run, runcall, runeval, set_bp |
| `@runpy.*` | `runpy` | find, is_module, module, module_ns, path, path_ns, result |
| `@reprlib.*` | `reprlib` | recursive, repr, short |
| `@graphlib.*` | `graphlib` | add, done, is_dag, new, ready, sort, sort_groups |
| `@numbers.*` | `numbers` | is_complex, is_integral, is_number, is_rational, is_real |

---

### Foreign Function Interface

| Namespace | Wraps | Commands |
|---|---|---|
| `@ctypes.*` | `ctypes` | addressof, byref, c_bool, c_char, c_char_p, c_double, c_float, c_int, c_long, c_size_t, c_uint, c_ulong, c_void_p, c_wchar_p, cast, create_buf, create_wbuf, libc, load, load_util, load_win, memmove, memset, pointer, pointer_type, set_val, sizeof, string_at, val, wstring_at |
| `@array.*` | `array` | append, byteswap, concat, count_of, extend, from_bytes, from_file, get, index, insert, item_size, length, max, min, of, pop, range, remove, reverse, set, slice, sum, to_bytes, to_file, to_list, typecode, zeros |

---

### Configuration & Secrets

| Namespace | Wraps | Commands |
|---|---|---|
| `@env.*` | `os.environ` | all, bool, expand, float, get, has, int, json, list, load, mask, parse, prefix, require, save, set, setdefault, unset |
| `@config.*` | `json`/`tomllib`/`configparser`/`os.environ` | dotenv, env, env_all, env_del, env_set, get, has, keys, load, reload, save, sections, set |

`@env` is the recommended surface for tokens and DB URLs. Auto-load a `.env`
file with `@env.load[]`, read typed values (`@env.int`, `@env.bool`, …),
fail fast on missing required vars with `@env.require`, and never leak a
secret thanks to `@env.mask` (`"ab••••••89"`).

### Utilities

| Namespace | Wraps | Commands |
|---|---|---|
| `@argparse.*` | `argparse` | add, new, parse, parse_dict, run, run_known, to_dict |
| `@dataclasses.*` | `dataclasses` | FrozenInstanceError, InitVar, KW_ONLY, asdict, astuple, dataclass, field, fields, is_dataclass, make_dataclass, replace |
| `@typing.*` | `typing` | Any, Callable, ClassVar, Dict, Final, List, Literal, NamedTuple, Optional, Protocol, Set, TYPE_CHECKING, Tuple, TypeAlias, TypeVar, Union, cast, get_type_hints, overload, runtime_checkable |
| `@enum.*` | `enum` | Enum, Flag, IntEnum, IntFlag, StrEnum, auto, create, list, members, names, unique, values |
| `@contextlib.*` | `contextlib` | AbstractContextManager, ExitStack, asynccontextmanager, chdir, closing, contextmanager, nullcontext, redirect_stderr, redirect_stdout, suppress |
| `@copy.*` | `copy` | copy, deepcopy, replace |
| `@io.*` | `io` | BytesIO, StringIO, close, closed, flush, getvalue, open, open_append, open_bytes, open_write, read, readline, readlines, seek, tell, truncate, write, writelines |
| `@heapq.*` | `heapq` | heapify, heappop, heappush, heappushpop, heapreplace, merge, nlargest, nsmallest |
| `@bisect.*` | `bisect` | bisect, bisect_left, bisect_right, insort, insort_left, insort_right |
| `@pprint.*` | `pprint` | PrettyPrinter, format, isreadable, isrecursive, pp, print, saferepr |
| `@shlex.*` | `shlex` | join, quote, quote_all, split |
| `@calendar.*` | `calendar` | day_abbr, day_name, day_of_year, days_in_month, first_weekday_of, get_first_weekday, is_leap, is_weekday, is_weekend, leap_days, month_abbr, month_dates, month_name, month_range, month_text, next_month, prev_month, quarter, timegm, week_of_year, weekday, weekheader, year_dates, year_text |
| `@zipapp.*` | `zipapp` | copy, create, interpreter, is_archive, main |

---

## Third-party / plugin namespaces

| Namespace | Type | Notes |
|---|---|---|
| `@yaml.*` | built-in (optional) | dump_file, dumps, from_json, get, load_all, load_file, loads, parse, stringify, to_json |
| `@image.*` | built-in (optional) | convert, crop, flip_h, flip_v, format, grayscale, height, mode, new, open, paste, resize, rotate, save, show, size, thumbnail, to_bytes, width |
| `@pdf.*` | built-in (optional) | crop, lines, metadata, open, page_count, pages, table_of, tables, text, text_of, words |
| `@db.*` | plugin | `mods/cruhon-db` — 172+ commands (SQLite/PostgreSQL/MySQL, sync + async). Includes `connect_env`, `migrate`, `seed`, `dsn_safe`, `attach_panel`/`detach_panel` |
| `@panel.*` | plugin | `mods/cruhon-panel` — live SSE log/metric/event dashboard: `start`, `stop`, `log`, `metric`, `event`, `attach_logging`, `open`, `wait` |
| `@discord.*` | plugin | `mods/cruhon-discord` — ~60 commands |

---

## Shortcut plugins

Four configurable shortcut plugins add aliases and extra convenience methods.
All four load together without naming conflicts.

### `cruhon-shortcuts` (base)

Installs **global aliases** (`@read` → `@file.read`, `@now` → `@date.now`,
`@uuid` → `@crypto.uuid`, `@mean` → `@statistics.mean`, …) and
**method aliases** (`@file.cat`, `@file.ls`, `@date.ts`, `@http.fetch`, …).
Also adds **200+ convenience methods** like `@file.head`, `@file.tail`,
`@date.tomorrow`, `@date.age`, `@random.password`, `@statistics.summary`,
`@collections.histogram`, `@string.random`, `@struct.hexdump`, …

Configure in `mods/cruhon-shortcuts/mod.json`:

```json
{
  "groups": "all",
  "global_aliases": true,
  "method_aliases": true,
  "disabled": [],
  "custom": { "@slurp[": "@file.read[" }
}
```

Groups: `file`, `http`, `date`, `text`, `math`, `crypto`, `collections`,
`system`, `data`, `stdlib`, `types`, `io`, `binary`.

### `cruhon-shortcuts-pro` (high-level composites)

| Group | Highlights |
|---|---|
| `math` | `@clamp`, `@lerp`, `@sign`, `@percent`, `@frange`, `@gcd`, `@lcm`, `@factorial`, `@degrees`, `@log2`, `@is_close` |
| `lists` | `@window`, `@transpose`, `@rotate_list`, `@head_n`, `@tail_n`, `@interleave`, `@dedupe`, `@flat`, `@chunks`, `@sorted_by`, `@take_while`, `@drop_while` |
| `dicts` | `@pick_keys`, `@omit_keys`, `@map_vals`, `@filter_keys`, `@deep_merge`, `@dict_diff`, `@flat_dict`, `@swap_kv` |
| `text` | `@camel_case`, `@snake_case`, `@kebab_case`, `@pascal_case`, `@word_freq`, `@excerpt`, `@initials`, `@ordinal`, `@pluralize` |
| `logic` | `@coalesce`, `@first_true`, `@count_if`, `@any_match`, `@all_match`, `@none_match`, `@first_where`, `@last_where`, `@group_by`, `@tally` |

### `cruhon-shortcuts-data`

Covers `@re.*`, `@yaml.*`, `@image.*`, `@pdf.*` plus all v2.4 namespaces:

| Alias | Targets |
|---|---|
| `@toml_load`, `@toml_get`, `@toml_has` | `@toml.*` |
| `@money`, `@exact_add`, `@exact_round` | `@decimal.*` |
| `@ratio_frac`, `@one_third` | `@fraction.*` |
| `@is_private_ip`, `@ip_hosts`, `@subnet` | `@ip.*` |
| `@match_re`, `@find_re`, `@replace_re` | `@re.*` |
| `@yaml_load`, `@yaml_dump` | `@yaml.*` |
| `@img_open`, `@img_resize`, `@img_save` | `@image.*` |
| `@pdf_text`, `@pdf_pages` | `@pdf.*` |

---

## Notes

- **`@decimal`** uses exact base-10 arithmetic — `@decimal.add["0.1"; "0.2"]` returns `0.3` exactly.
- **`@toml`** is read-only (`tomllib` is a parser only); write TOML by building the string.
- **`@resource`** is Unix-only — not available on Windows.
- **`@yaml`**, **`@image`**, **`@pdf`** require optional pip packages.
- **`@asyncio.sleep`**, **`@asyncio.gather`**, **`@asyncio.open`**, and **`@asyncio.serve`** emit `await` expressions — use them inside `@async[...]` functions.
- **`@ctypes.load_util`** uses `ctypes.util.find_library` which may not find all libraries on all platforms.
