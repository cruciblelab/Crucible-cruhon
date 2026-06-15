# Cruhon Library Reference

**v2.9.0 — 127 namespaces · 1822+ commands**

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
| `@file.*` | `pathlib` / `os` / `shutil` / `glob` / `tempfile` | read, write, append, copy, move, glob, mkdir, mkdirs, delete, rename, touch, symlink, hardlink, chmod, chown, stat, size, exists, is_file, is_dir, readlines, writelines, json, write_json, yaml, write_yaml, head, tail, grep, hash, abs, resolve, parent, name, stem, suffix |
| `@date.*` | `datetime` / `time` / `calendar` / `zoneinfo` | now, utcnow, today, format, parse, timestamp, from_timestamp, add, sub, diff_days, diff_hours, diff_minutes, weekday, isoweek, isoformat, to_timezone, in_timezone, is_past, is_future, year, month, day, hour, minute, second, start_of_day, end_of_day, midnight |
| `@text.*` | `re` / `str` / `textwrap` / `html` | upper, lower, title, capitalize, swapcase, casefold, strip, lstrip, rstrip, contains, startswith, endswith, count, index, split, rsplit, partition, rpartition, join, lines, words, replace, format, repeat, reverse, translate, len, slice, truncate, pad_left, pad_right, center, zfill, wrap, fill, indent, dedent, match, search, find, findall, sub, split_re, groups, encode, decode, escape_html, unescape_html, slug, clean, remove_digits, remove_punct, only_digits |
| `@http.*` | `requests` / `httpx` | get, post, put, patch, delete, head, options, upload, auth_get, auth_post, json, text, status, ok, headers, elapsed, cookies, url, async_get, async_post, async_put, async_delete, async_json, async_text, session, session_get, session_post, timeout_get |
| `@crypto.*` | `hashlib` / `hmac` / `secrets` / `base64` / `uuid` | md5, sha1, sha256, sha512, sha3_256, sha3_512, blake2b, blake2s, hash, hash_bytes, hash_file, pbkdf2, scrypt, hmac, compare, token, token_url, token_bytes, random_int, random_bytes, uuid, uuid1, uuid3, uuid5, b64_encode, b64_decode, b64url_encode, b64url_decode, hex_encode, hex_decode |
| `@log.*` | `logging` | setup, debug, info, warning, error, critical, exception, to_file, to_stream, get, child, getLogger, setLevel, addHandler, formatter, basicConfig, disable, reset, handlers, capture_warnings |
| `@config.*` | `json` / `tomllib` / `configparser` / `os.environ` | load, loads, save, dump, get, set, keys, values, has, dotenv, env, env_int, env_float, env_bool, env_list, require, merge, flatten, from_str, to_str |
| `@shell.*` | `subprocess` / `os` / `sys` / `shutil` | run, output, lines, code, ok, check, bg, kill, terminate, wait, wait_output, pipe, env, env_set, env_del, which, cwd, chdir, username, uid, gid, pid, cpu_count, hostname, is_root |
| `@archive.*` | `zipfile` / `tarfile` / `gzip` / `bz2` / `lzma` | zip, unzip, zip_list, zip_add, zip_read, zip_extract_one, tar, untar, tar_list, tar_extract_one, gzip, gunzip, bzip2, bunzip2, lzma, unlzma, is_zip, is_tar, size |
| `@mail.*` | `smtplib` / `imaplib` / `email` | send, send_html, send_with_attachment, message, html_message, attach, connect, connect_tls, login, deliver, close, parse, subject, sender, body, imap_connect, imap_list, imap_select, imap_search, imap_fetch, imap_fetch_all, imap_close |
| `@csv.*` | `csv` | read, write, append, filter, to_json, from_json, headers, rows, column, select, map, sort, group, pivot, dict_reader, dict_writer |
| `@store.*` | in-memory dict | set, get, all, clear, delete, has, keys, values, items, update, setdefault, pop |
| `@color.*` | ANSI codes | red, green, blue, yellow, cyan, magenta, white, black, bright_red, bright_green, bold, dim, italic, underline, reset, strip |
| `@ctx.*` | `__ctx__` dict | set, get, push, pop, clear, delete, keys, values, items, has, update |
| `@json.*` | `json` | load, dump, loads, dumps, indent, sort_keys, compact |

---

### Text & Math

| Namespace | Wraps | Commands |
|---|---|---|
| `@math.*` | `math` | sqrt, floor, ceil, round, abs, pow, log, log2, log10, exp, sin, cos, tan, asin, acos, atan, atan2, degrees, radians, gcd, lcm, isclose, isfinite, isinf, isnan, factorial, comb, perm, prod, sum, min, max, clamp, lerp, sign, hypot, dist, pi, e, tau, inf, nan |
| `@random.*` | `random` | random, randint, randrange, uniform, choice, choices, sample, shuffle, seed, gauss, normalvariate, expovariate, getrandbits, randbytes, triangular, betavariate, gammavariate, lognormvariate, weibullvariate |
| `@cmath.*` | `cmath` | sqrt, exp, log, log10, phase, polar, rect, sin, cos, tan, asin, acos, atan, sinh, cosh, tanh, asinh, acosh, atanh, isclose, isfinite, isinf, isnan, pi, e, tau, inf, infj, nan, nanj |
| `@decimal.*` | `decimal` | make, to_float, to_str, to_int, add, sub, mul, div, mod, pow, sum, round, quantize, floor, ceil, sqrt, abs, compare, is_zero, is_nan, is_inf, is_finite, places, money, context, getcontext, setcontext |
| `@fraction.*` | `fractions` | make, from_float, from_str, numerator, denominator, to_float, to_str, to_tuple, add, sub, mul, div, limit |
| `@statistics.*` | `statistics` | mean, fmean, geometric_mean, harmonic_mean, median, median_low, median_high, median_grouped, mode, multimode, quantiles, stdev, pstdev, variance, pvariance, covariance, correlation, linear_regression |
| `@textwrap.*` | `textwrap` | wrap, fill, shorten, dedent, indent, columns, truncate |
| `@string.*` | `string` | ascii_letters, ascii_lowercase, ascii_uppercase, digits, hexdigits, octdigits, punctuation, whitespace, printable, template, substitute, safe_substitute, formatter, capwords, ascii_to_int, int_to_ascii, filter, exclude, count_in, maketrans, translate, random_lower, random_upper, random_digits_str |
| `@unicode.*` | `unicodedata` | name, lookup, category, bidirectional, combining, mirrored, numeric, digit, decimal, normalize, nfc, nfd, nfkc, nfkd, strip_accents, unidata_version |
| `@codecs.*` | `codecs` | encode, decode, encode_err, decode_err, rot13, hex, unhex, zip, unzip, lookup, name, open, reader, writer |
| `@colorsys.*` | `colorsys` | to_hsv, from_hsv, to_hls, from_hls, to_yiq, from_yiq, hex_to_rgb, rgb_to_hex, hex_to_hsv, hex_to_hls, luminance, blend |

---

### Data & Formats

| Namespace | Wraps | Commands |
|---|---|---|
| `@collections.*` | `collections` | Counter, counter_most_common, counter_total, counter_update, defaultdict, defaultdict_list, defaultdict_int, defaultdict_set, deque, namedtuple, OrderedDict, ChainMap, chain_map, group_by, histogram |
| `@itertools.*` | `itertools` | chain, chain_from, cycle, repeat, count, zip_longest, product, permutations, combinations, combinations_with_replacement, groupby, accumulate, islice, takewhile, dropwhile, filterfalse, starmap, flatten, pairwise, batched |
| `@functools.*` | `functools` | reduce, partial, lru_cache, cache, cached_property, wraps, total_ordering, singledispatch, update_wrapper, cmp_to_key, compose |
| `@operator.*` | `operator` | add, sub, mul, truediv, floordiv, mod, pow, neg, pos, abs, and_, or_, xor, not_, lshift, rshift, lt, le, eq, ne, ge, gt, contains, getitem, setitem, delitem, itemgetter, attrgetter, methodcaller, length_hint, is_, is_not, truth |
| `@xml.*` | `xml.etree.ElementTree` | parse, from_string, to_string, find, find_all, find_text, children, iter, count, tag, text, attrib, get, to_dict, set_text, set_attrib, append_child, remove_child |
| `@toml.*` | `tomllib` | loads, load, get, keys, has, sections, to_dict, nested_get |
| `@yaml.*` | `pyyaml` | loads, dumps, load_file, dump_file, get, has, keys, to_dict, load_all, safe_load |
| `@diff.*` | `difflib` | ratio, quick_ratio, is_similar, unified, context, ndiff, lines, close_matches, best_match, opcodes, matching_blocks |
| `@re.*` | `re` | search, match, fullmatch, findall, finditer, sub, subn, split, compile, escape, group, group1, groups, named, start, end, span, groupdict, count_matches, first, replace_fn |
| `@struct.*` | `struct` | pack, unpack, unpack_list, first, pack_into, unpack_from, iter_unpack, calcsize, compile, pad, to_hex, from_hex_str |
| `@binascii.*` | `binascii` | hexlify, unhexlify, b2a_hex, a2b_hex, b2a_base64, a2b_base64, crc32, crc_hqx |
| `@zlib.*` | `zlib` | compress, decompress, decompress_text, compress_b64, decompress_b64, compress_str, decompress_str, crc32, crc32_hex, adler32, adler32_hex, ratio, is_zlib |
| `@base64.*` | `base64` | encode, decode, urlsafe_encode, urlsafe_decode, b32encode, b32decode, b16encode, b16decode, standard, pad |
| `@pickle.*` | `pickle` | dump, dumps, load, loads, to_file, from_file, copy |
| `@shelve.*` | `shelve` | open, get, set, delete, keys, values, items, has, update, sync, close |
| `@plist.*` | `plistlib` | dumps, loads, to_file, from_file, fmt_xml, fmt_bin, to_dict |
| `@reprlib.*` | `reprlib` | repr, shorten, maxstring, maxlist, maxdict, maxset, maxlong, maxother, recursive_repr |
| `@graphlib.*` | `graphlib` | sort, is_dag, ancestors, descendants, roots, leaves, add_edge, from_dict |
| `@email.*` | `email` | message, make, set_content, add_html, attach_file, parse, subject, sender, recipients, body, html_body, as_string, to_bytes, valid_address, format_address |
| `@calendar.*` | `calendar` | is_leap, leap_days, month_range, days_in_month, weekday, month_name, month_abbr, day_name, day_abbr, month_text, year_text, day_of_year, week_of_year, quarter, next_month, prev_month, timegm |

---

### File & Path

| Namespace | Wraps | Commands |
|---|---|---|
| `@pathlib.*` | `pathlib` | path, abs, resolve, exists, is_file, is_dir, name, stem, suffix, suffixes, parent, parts, anchor, drive, root, join, with_name, with_stem, with_suffix, read, write, mkdir, rmdir, touch, unlink, rename, rglob, glob, stat, owner, chmod, iterdir, relative_to, is_relative_to, as_uri |
| `@glob.*` | `glob` | glob, iglob, recursive, escape, fnmatch, filter, translate |
| `@tempfile.*` | `tempfile` | file, dir, named, spooled, mkstemp, mkdtemp, tempdir, gettempdir |
| `@fnmatch.*` | `fnmatch` | match, fnmatchcase, filter, translate |
| `@fileinput.*` | `fileinput` | lines, input, filename, lineno, filelineno, fileno, isfirstline, isstdin, close |
| `@stat.*` | `stat` | mode_str, is_dir, is_file, is_link, is_socket, is_block, is_char, is_fifo, mode_bits, permissions, S_ISREG, S_ISDIR |
| `@shutil.*` | `shutil` | copy, copy2, copyfile, copymode, copystat, move, tree, rmtree, which, disk_usage, disk_free, disk_total, chown, make_archive, unpack_archive, get_archive_formats, get_unpack_formats |
| `@filecmp.*` | `filecmp` | equal, shallow, dircmp, same_files, diff_files, left_only, right_only, common, compare, clear_cache |
| `@linecache.*` | `linecache` | line, lines, count, check, clear |
| `@mmap.*` | `mmap` | read, slice, size, find, rfind, contains, count, open, seek, tell, read_at, write_at, put, flush, close, closed |
| `@zipapp.*` | `zipapp` | create, interpreter, main, is_archive, copy |
| `@configparser.*` | `configparser` | load, loads, new, get, getint, getfloat, getbool, sections, keys, items, has, set, add_section, remove_section, remove_key, read_dict, to_dict, has_section, save, dumps |

---

### OS & System

| Namespace | Wraps | Commands |
|---|---|---|
| `@os.*` | `os` | env, path, getcwd, listdir, makedirs, remove, rename, stat, chmod, access, getpid, getppid, getuid, getgid |
| `@sys.*` | `sys` | argv, exit, path, path_append, path_remove, version, version_info, platform, getsizeof, maxsize, stdin, stdout, stderr, exc_info, settrace, setprofile, getrecursionlimit, setrecursionlimit, intern, is_finalizing, modules, builtin_module_names, flags |
| `@platform.*` | `platform` | system, node, release, version, machine, processor, architecture, python_version, python_impl, python_compiler, uname, is_windows, is_linux, is_mac, is_64bit, libc_ver |
| `@gc.*` | `gc` | collect, enable, disable, isenabled, count, get_count, threshold, set_threshold, get_threshold, get_objects, get_referrers, get_referents, freeze, unfreeze, is_tracked, is_finalized |
| `@inspect.*` | `inspect` | signature, parameters, members, getmembers, source, getsource, file, getfile, module, getmodule, isfunction, ismethod, isclass, ismodule, isbuiltin, iscoroutinefunction, isasyncgenfunction, doc, getdoc, annotations, getannotations, stack, currentframe, callerframe |
| `@traceback.*` | `traceback` | format, print, format_exc, print_exc, format_list, extract_tb, extract_stack, format_tb, format_stack, last, clear_frames |
| `@warnings.*` | `warnings` | warn, warn_explicit, ignore, error, once, always, default, simplefilter, resetwarnings, catch_warnings |
| `@weakref.*` | `weakref` | ref, proxy, finalize, deref, is_alive, WeakValueDictionary, WeakKeyDictionary, WeakSet |
| `@types.*` | `types` | new_class, SimpleNamespace, MappingProxy, is_function, is_method, is_lambda, is_generator, is_coroutine, is_async_gen, is_builtin, FunctionType, MethodType, ModuleType, GeneratorType, CoroutineType |
| `@abc.*` | `abc` | abstract, abstractmethod, abstractclassmethod, abstractstaticmethod, isabstract, ABC, ABCMeta, abstractproperty |
| `@signal.*` | `signal` | handler, send, alarm, pause, set_wakeup, getsignal, raise_signal, SIG_DFL, SIG_IGN, SIGINT, SIGTERM, SIGUSR1, SIGUSR2, SIGALRM, SIGCHLD |
| `@atexit.*` | `atexit` | register, unregister, handlers |
| `@locale.*` | `locale` | setlocale, getlocale, getpreferredencoding, format_number, format_string, currency, str, atoi, atof, strxfrm, normalize, locale_alias |
| `@gettext.*` | `gettext` | translation, gettext, ngettext, pgettext, npgettext, bindtextdomain, textdomain, find, install, dgettext, dngettext |
| `@sysconfig.*` | `sysconfig` | get_path, get_paths, get_config_var, get_config_vars, get_platform, get_python_version, variables, schemes, scheme_names |
| `@resource.*` | `resource` | getrlimit, setrlimit, getrusage, RLIMIT_CPU, RLIMIT_DATA, RLIMIT_FSIZE, RLIMIT_STACK, RLIMIT_AS, RLIMIT_NOFILE, RLIMIT_NPROC, RUSAGE_SELF, RUSAGE_CHILDREN, utime, stime, maxrss |
| `@errno.*` | `errno` | name, description, code, all, ENOENT, EEXIST, EACCES, EPERM, ENOTEMPTY, EINVAL, EBADF, ENOTDIR, EISDIR, EROFS, ENOSPC, EBUSY |
| `@getpass.*` | `getpass` | password, user, terminal |
| `@numbers.*` | `numbers` | is_number, is_complex, is_real, is_rational, is_integral |

---

### Networking

| Namespace | Wraps | Commands |
|---|---|---|
| `@socket.*` | `socket` | hostname, fqdn, host_to_ip, ip_to_host, resolve, connect, send, recv, close, is_open, free_port, tcp, udp, server, bind, listen, accept, send_to, recv_from, set_timeout, reuse, local, peer, shutdown, file |
| `@ssl.*` | `ssl` | wrap, context, client_context, server_context, load_cert, load_key, load_ca, check_hostname, verify_mode, protocols, ciphers, get_cert, get_peer_cert, CERT_REQUIRED, CERT_OPTIONAL, CERT_NONE, TLSv1_2, TLSv1_3 |
| `@ftp.*` | `ftplib` | connect, login, list, download, upload, delete, rename, mkdir, rmdir, cwd, pwd, passive, size, quit |
| `@pop3.*` | `poplib` | connect, connect_ssl, list, stat, retrieve, delete, reset, quit, noop, top, uidl |
| `@xmlrpc.*` | `xmlrpc.client` | client, call, multi_call, fault, close |
| `@httpserver.*` | `http.server` | serve, serve_async, threaded, stop, close, port, handler, directory |
| `@selectors.*` | `selectors` | new, close, watch_read, watch_write, register, modify, unwatch, watched, count, read, write, wait |
| `@ip.*` | `ipaddress` | address, network, interface, version, is_private, is_global, is_loopback, is_multicast, hosts, num_addresses, netmask, broadcast, network_address, contains, supernet, to_int, from_int |
| `@url.*` | `urllib.parse` | parse, join, quote, unquote, quote_plus, unquote_plus, encode, parse_qs, parse_qsl, scheme, netloc, path, query, fragment, username, password, port, hostname, unparse, urlencode |
| `@html.*` | `html` / `re` | escape, unescape, strip_tags, text, links, images, tags |
| `@webbrowser.*` | `webbrowser` | open, open_new, open_tab, get, browsers, controller |
| `@mimetypes.*` | `mimetypes` | guess, guess_ext, guess_all, is_text, charset, known, types_map, suffix_map, add |
| `@httpx.*` | `httpx` | get, post, put, delete, patch, head, options, client, async_client, timeout, follow_redirects |

---

### Concurrency

| Namespace | Wraps | Commands |
|---|---|---|
| `@asyncio.*` | `asyncio` | run, sleep, gather, wait_for, task, cancel, done, result, all_tasks, current_task, shield, ensure, loop, new_loop, set_loop, run_loop, close_loop, lock, event, condition, semaphore, queue, open, serve, timeout, iscoroutine, isfuture, istask |
| `@threading.*` | `threading` | Thread, start, join, is_alive, daemon, Lock, RLock, acquire, release, Event, event_set, event_clear, event_wait, event_is_set, Semaphore, BoundedSemaphore, Condition, Barrier, Timer, current_thread, main_thread, active_count, enumerate, get_ident, settrace, local |
| `@multiprocessing.*` | `multiprocessing` | cpus, pool, map, starmap, apply, imap, process, start, join, current, active, set_start, queue, manager, lock, event, semaphore, pipe, value, array |
| `@futures.*` | `concurrent.futures` | threads, processes, shutdown, submit, result, done, running, cancelled, cancel, exception, on_done, thread_map, process_map, map, wait_first, as_done |
| `@queue.*` | `queue` | Queue, LifoQueue, PriorityQueue, SimpleQueue, put, put_nowait, get, get_nowait, empty, full, qsize, task_done, join |
| `@sched.*` | `sched` | new, run, after, at, cancel, empty, queue |

---

### Serialization & Database

| Namespace | Wraps | Commands |
|---|---|---|
| `@sqlite.*` | `sqlite3` | open, close, execute, executemany, fetchall, fetchone, fetchmany, commit, rollback, tables, columns, insert, update, delete, select, count, exists, transaction, attach, pragma, row_factory, timeout, cursor, lastrowid |
| `@pickle.*` | `pickle` | dump, dumps, load, loads, to_file, from_file, copy |
| `@shelve.*` | `shelve` | open, get, set, delete, keys, values, items, has, update, sync, close |
| `@plist.*` | `plistlib` | dumps, loads, to_file, from_file, fmt_xml, fmt_bin |
| `@configparser.*` | `configparser` | load, loads, new, get, getint, getfloat, getbool, sections, keys, items, has, set, add_section, remove_section, remove_key, read_dict, to_dict, has_section, save, dumps |

---

### Testing & Profiling

| Namespace | Wraps | Commands |
|---|---|---|
| `@unittest.*` | `unittest` | run, discover, runner, assert_equal, assert_not_equal, assert_true, assert_false, assert_none, assert_not_none, assert_in, assert_not_in, assert_raises, assert_almost_equal, assert_greater, assert_less, count, failures, errors, mock, patch |
| `@doctest.*` | `doctest` | run, testmod, testfile, globs, verbose, optionflags, DocTestSuite, DocFileSuite, teststring |
| `@timeit.*` | `timeit` | time, repeat, stmt, auto, default_number, default_repeat, timer, Timer |
| `@profile.*` | `cProfile` | run, sort, stats, dump, top, cumulative, callers, callees, enable, disable, clear |
| `@tracemalloc.*` | `tracemalloc` | start, stop, is_tracing, snapshot, top, compare, peak, size, clear_traces, get_traced_memory, get_traceback_limit, set_traceback_limit |

---

### Developer Tools

| Namespace | Wraps | Commands |
|---|---|---|
| `@ast.*` | `ast` | parse, dump, unparse, compile, literal, walk, node_types, names, functions, classes, imports, constants, docstring, is_valid, parse_eval, fields, children, fix, increment |
| `@dis.*` | `dis` | bytecode, instructions, opnames, consts, varnames, freevars, cellvars, stack_size, code_info, opname |
| `@tokenize.*` | `tokenize` | tokens, names, strings, numbers, comments, ops, keywords, type, string, start, end, line, NAME, OP, NUMBER, STRING, COMMENT, NEWLINE, INDENT, DEDENT, tok_name, untokenize, count, unique_names |
| `@keyword.*` | `keyword` | iskeyword, issoftkeyword, all, soft_all, kwlist, softkwlist |
| `@importlib.*` | `importlib` | import_module, reload, find_spec, source_hash, from_name, is_frozen, origin, submodule_search_locations, spec_from_file |
| `@pdb.*` | `pdb` | bp, breakpoint, pm, run, runeval, runcall, new, set_bp, clear_bp, clear_all, list_bps |
| `@runpy.*` | `runpy` | module, module_ns, is_module, path, path_ns, find, result |
| `@reprlib.*` | `reprlib` | repr, shorten, maxstring, maxlist, maxdict, maxset, maxlong, maxother, recursive_repr |
| `@graphlib.*` | `graphlib` | sort, is_dag, ancestors, descendants, roots, leaves, add_edge, from_dict |
| `@numbers.*` | `numbers` | is_number, is_complex, is_real, is_rational, is_integral |

---

### Foreign Function Interface

| Namespace | Wraps | Commands |
|---|---|---|
| `@ctypes.*` | `ctypes` | load, load_win, load_util, libc, c_int, c_uint, c_long, c_ulong, c_float, c_double, c_bool, c_char, c_char_p, c_void_p, c_size_t, c_wchar_p, create_buf, create_wbuf, string_at, wstring_at, memmove, memset, byref, pointer, addressof, sizeof, cast, pointer_type, val, set_val |
| `@array.*` | `array` | of, zeros, range, to_bytes, from_bytes, to_list, item_size, typecode, length, sum, min, max, append, extend, insert, pop, remove, set, reverse, concat, byteswap, index, count_of, get, slice, from_file, to_file |

---

### Utilities

| Namespace | Wraps | Commands |
|---|---|---|
| `@argparse.*` | `argparse` | parse, parse_dict, new, add, run, run_known, to_dict |
| `@dataclasses.*` | `dataclasses` | dataclass, field, asdict, astuple, fields, replace, is_dataclass, make_dataclass, FrozenInstanceError |
| `@typing.*` | `typing` | Optional, Union, List, Dict, Tuple, Set, FrozenSet, Deque, Any, Callable, Iterator, Generator, Awaitable, Coroutine, AsyncIterator, Type, ClassVar, Final, Literal, TypeVar, Generic, Protocol, cast, get_type_hints, is_typeddict, overload, no_type_check, runtime_checkable |
| `@enum.*` | `enum` | Enum, IntEnum, StrEnum, Flag, IntFlag, auto, unique, create, names, values, members, from_value, from_name |
| `@contextlib.*` | `contextlib` | contextmanager, suppress, nullcontext, redirect_stdout, redirect_stderr, closing, ExitStack, asynccontextmanager, AbstractContextManager, chdir |
| `@copy.*` | `copy` | copy, deepcopy, replace |
| `@io.*` | `io` | StringIO, BytesIO, read, readline, readlines, write, writelines, getvalue, seek, tell, truncate, close, closed, flush, open, open_bytes, open_write, open_append |
| `@heapq.*` | `heapq` | heappush, heappop, heapify, heappushpop, heapreplace, nlargest, nsmallest, merge |
| `@bisect.*` | `bisect` | bisect_left, bisect_right, bisect, insort_left, insort_right, insort |
| `@pprint.*` | `pprint` | print, format, pp, isreadable, isrecursive, saferepr, PrettyPrinter |
| `@shlex.*` | `shlex` | split, join, quote, quote_all |
| `@calendar.*` | `calendar` | is_leap, leap_days, month_range, days_in_month, weekday, month_name, month_abbr, day_name, month_text, year_text, day_of_year, week_of_year, quarter, timegm |
| `@zipapp.*` | `zipapp` | create, interpreter, main, is_archive, copy |

---

## Third-party / plugin namespaces

| Namespace | Type | Notes |
|---|---|---|
| `@yaml.*` | built-in (optional) | Requires `pip install pyyaml` |
| `@image.*` | built-in (optional) | Requires `pip install pillow` |
| `@pdf.*` | built-in (optional) | Requires `pip install pdfplumber` |
| `@db.*` | plugin | `mods/cruhon-db` — 138 commands |
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
