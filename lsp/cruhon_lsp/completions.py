"""
Static completion data for all Cruhon commands and stdlib namespace methods.
"""
from __future__ import annotations
from lsprotocol import types

CIK = types.CompletionItemKind

# (name, kind, detail/signature, documentation)
COMMANDS: list[tuple[str, types.CompletionItemKind, str, str]] = [
    # ── Assignment ─────────────────────────────────────────────
    ("var",      CIK.Variable, "@var[name; value]",                 "Declare or assign a variable. Type annotation: @var[name: type; value] or @var[name: type]."),
    ("const",    CIK.Variable, "@const[NAME; value]",               "Declare a constant (uppercase by convention). Type annotation: @const[NAME: type; value]."),
    ("let",      CIK.Function, "@let[x; v1; y; v2; ...]",           "Assign multiple variables in one command."),
    ("inc",      CIK.Function, "@inc[name]",                        "Increment a variable by 1, or by n: @inc[x; 2]."),
    ("dec",      CIK.Function, "@dec[name]",                        "Decrement a variable by 1, or by n: @dec[x; 2]."),
    ("swap",     CIK.Function, "@swap[a; b]",                       "Swap two variables via tuple assignment."),
    # ── Control flow ───────────────────────────────────────────
    ("if",       CIK.Keyword,  "@if[condition]\n    ...\n@end",     "Conditional block."),
    ("elif",     CIK.Keyword,  "@elif[condition]",                  "Else-if branch inside @if."),
    ("else",     CIK.Keyword,  "@else",                             "Else branch inside @if."),
    ("end",      CIK.Keyword,  "@end",                              "Close a block (@if, @for, @func, etc.)."),
    ("for",      CIK.Keyword,  "@for[item; iterable]\n    ...\n@end", "For loop over an iterable."),
    ("foreach",  CIK.Keyword,  "@foreach[item; iterable]\n    ...\n@end", "For-each with automatic index variable __i__."),
    ("while",    CIK.Keyword,  "@while[condition]\n    ...\n@end",  "While loop."),
    ("repeat",   CIK.Keyword,  "@repeat[n]\n    ...\n@end",         "Repeat the body exactly n times."),
    ("break",    CIK.Keyword,  "@break",                            "Break out of the nearest loop."),
    ("continue", CIK.Keyword,  "@continue",                         "Continue to the next loop iteration."),
    ("return",   CIK.Keyword,  "@return[value]",                    "Return a value from a @func."),
    ("pass",     CIK.Keyword,  "@pass",                             "No-op placeholder."),
    # ── Functions / classes ────────────────────────────────────
    ("func",     CIK.Function, "@func[name; p1; p2]\n    ...\n@end", "Define a named function."),
    ("class",    CIK.Class,    "@class[Name]\n    ...\n@end",       "Define a class."),
    ("macro",    CIK.Function, "@macro[name; p1; ...]\n    ...\n@end", "Define a reusable named macro."),
    ("call",     CIK.Function, "@call[name; arg1; arg2]",           "Call a defined @macro."),
    ("decorator",CIK.Function, "@decorator[name]\n    @func[...]\n@end", "Apply a decorator to a function."),
    # ── Templates / pipelines ──────────────────────────────────
    ("template", CIK.Snippet,  "@template[name]\n    {key} placeholder\n@end", "Define a named string template with {key} placeholders."),
    ("render",   CIK.Function, "@render[name; key=value]",          "Render a template with key=value substitutions (inline or statement)."),
    ("pipeline", CIK.Function, "@pipeline[name; fn1; fn2; ...]",    "Define a named function-composition pipeline."),
    ("apply",    CIK.Function, "@apply[pipeline_name; value]",      "Apply a pipeline to a value (inline or statement)."),
    ("spread",   CIK.Function, "@spread[fn; iterable]",             "Call fn(*iterable) — spread positional args (inline or statement)."),
    ("unpack",   CIK.Function, "@unpack[fn; mapping]",              "Call fn(**mapping) — spread keyword args (inline or statement)."),
    # ── Retry / timeout ───────────────────────────────────────
    ("retry",    CIK.Keyword,  "@retry[n]\n    ...\n@end",          "Retry the body up to n times on exception. Optional: @retry[n; ExcType]."),
    ("timeout",  CIK.Keyword,  "@timeout[seconds]\n    ...\n@end",  "Run body with a wall-clock deadline; raises TimeoutError if exceeded."),
    # ── Exceptions ─────────────────────────────────────────────
    ("try",      CIK.Keyword,  "@try\n    ...\n@catch[Exception]\n    ...\n@end", "Try/catch block."),
    ("catch",    CIK.Keyword,  "@catch[ExcType]",                   "Catch clause for @try."),
    ("finally",  CIK.Keyword,  "@finally",                          "Finally clause, always executed."),
    ("raise",    CIK.Keyword,  "@raise[ExcType; message]",          "Raise an exception."),
    ("with",     CIK.Keyword,  "@with[expr; name]\n    ...\n@end",  "Context manager block."),
    # ── Async ──────────────────────────────────────────────────
    ("async",    CIK.Keyword,  "@async[name]\n    ...\n@end",       "Define an async function."),
    ("await",    CIK.Keyword,  "@await[expr]",                      "Await an async expression."),
    # ── Modules ────────────────────────────────────────────────
    ("import",   CIK.Module,   "@import[module]",                   "Import a Python module."),
    ("module",   CIK.Module,   "@module[name]\n    ...\n@end",      "Define a Cruhon module."),
    ("export",   CIK.Module,   "@export[name]",                     "Export a name from the current module."),
    ("use",      CIK.Module,   "@use[module_path]",                 "Import all exports from a .clpy module."),
    ("from",     CIK.Module,   "@from[module; name]",               "Import a specific name from a .clpy module."),
    # ── Pattern matching ───────────────────────────────────────
    ("match",    CIK.Keyword,  "@match[value]\n    @case[p]\n        ...\n    @default\n        ...\n@end", "Structural pattern matching."),
    ("case",     CIK.Keyword,  "@case[pattern]",                    "Match case branch. Supports guards: @case[n if n > 0]."),
    ("default",  CIK.Keyword,  "@default",                          "Default (fallthrough) case in @match."),
    # ── I/O ────────────────────────────────────────────────────
    ("print",    CIK.Function, "@print[value]",                     "Print a value to stdout. Supports f-string interpolation."),
    ("input",    CIK.Function, "@input[prompt]",                    "Read a line from stdin (inline or statement)."),
    # ── Misc ───────────────────────────────────────────────────
    ("assert",   CIK.Function, "@assert[condition]",                "Assert a condition; optional message: @assert[cond; msg]."),
    ("del",      CIK.Keyword,  "@del[name]",                        "Delete a variable."),
    ("global",   CIK.Keyword,  "@global[name]",                     "Declare a global variable reference."),
    ("nonlocal", CIK.Keyword,  "@nonlocal[name]",                   "Declare a nonlocal variable reference."),
    ("yield",    CIK.Keyword,  "@yield[value]",                     "Yield a value from a generator function."),
    ("raw",      CIK.Snippet,  "@raw\n    # Python code here\n@end", "Embed raw Python code verbatim."),
    ("env",      CIK.Function, "@env[KEY]",                         "Read an environment variable. Optional default: @env[KEY; default]."),
    ("ctx",      CIK.Function, "@ctx[key]",                         "Read a context variable (__ctx__)."),
    # ── Inline expressions ─────────────────────────────────────
    ("list",     CIK.Function, "@list[a; b; c]",                    "Create a list literal."),
    ("dict",     CIK.Function, "@dict[k1; v1; k2; v2]",            "Create a dict from key-value pairs."),
    ("set",      CIK.Function, "@set[a; b; c]",                     "Create a set."),
    ("tuple",    CIK.Function, "@tuple[a; b]",                      "Create a tuple."),
    ("comp",     CIK.Function, "@comp[expr; var; iterable]",        "List comprehension. Optional: condition and type= (dict/set/gen)."),
    ("dictcomp", CIK.Function, "@dictcomp[key; val; var; iter]",    "Dict comprehension."),
    ("setcomp",  CIK.Function, "@setcomp[expr; var; iter]",         "Set comprehension."),
    ("gencomp",  CIK.Function, "@gencomp[expr; var; iter]",         "Generator expression."),
    ("pipe",     CIK.Function, "@pipe[value; fn1; fn2; ...]",       "Pipe a value through a chain of functions."),
    ("when",     CIK.Function, "@when[condition; if_true; if_false]", "Ternary (inline conditional): (if_true if cond else if_false)."),
    ("lambda",   CIK.Function, "@lambda[params; body]",             "Create a lambda: (lambda params: body)."),
    ("fetch",    CIK.Function, "@fetch[url]",                       "HTTP GET (inline): requests.get(url)."),
    # ── Type system (v2.7) ─────────────────────────────────────
    ("type",      CIK.Keyword,  "@type[Name; Alias]",                "Type alias declaration. Emits Name = Alias."),
    ("dataclass", CIK.Class,    "@dataclass[Name]\n    @var[field: type]\n@end", "Define a dataclass. Fields use @var[name: type] or @var[name: type; default]."),
]

# Namespace → (description, [methods])
NAMESPACES: dict[str, tuple[str, list[str]]] = {
    "file":       ("File I/O",             ["read", "write", "append", "lines", "exists", "size", "delete", "copy", "move", "list", "glob", "mkdir", "cwd", "ext", "basename", "dirname", "head", "tail", "grep", "find", "joinpath", "parent", "relpath", "with_suffix", "stem", "line_count", "read_bytes", "modified", "touch", "is_file", "is_dir"]),
    "math":       ("Math",                 ["sqrt", "floor", "ceil", "round", "abs", "pow", "log", "log2", "log10", "exp", "sin", "cos", "tan", "asin", "acos", "atan", "pi", "e", "inf", "nan", "hypot", "degrees", "radians"]),
    "http":       ("HTTP requests",        ["get", "post", "put", "delete", "patch", "head", "options", "json", "download", "async_get", "async_post", "async_json"]),
    "json":       ("JSON",                 ["loads", "dumps", "load_file", "dump_file", "get", "set", "keys", "values", "has", "pretty", "flatten", "merge"]),
    "random":     ("Random",               ["int", "float", "choice", "choices", "shuffle", "sample", "seed", "uuid", "password", "hex", "bytes"]),
    "time":       ("Time",                 ["now", "sleep", "timestamp", "format", "parse", "diff", "since", "perf"]),
    "date":       ("Date utilities",       ["today", "now", "format", "parse", "diff", "add_days", "tomorrow", "yesterday", "weekday", "age", "strftime"]),
    "text":       ("Text / string",         ["upper", "lower", "title", "capitalize", "strip", "lstrip", "rstrip", "split", "rsplit", "join", "replace", "sub", "search", "match", "findall", "contains", "startswith", "endswith", "count", "index", "is_digit", "is_alpha", "is_alnum", "is_space", "is_numeric", "encode", "decode", "center", "ljust", "rjust", "zfill", "slug", "clean", "wrap", "dedent", "partition", "rpartition", "swapcase"]),
    "os":         ("OS utilities",         ["getcwd", "listdir", "exists", "getenv", "environ", "run", "popen", "exit", "sep", "expanduser", "abspath"]),
    "sys":        ("System",               ["argv", "path", "version", "platform", "exit", "stdin", "stdout", "executable"]),
    "re":         ("Regex",                ["match", "search", "fullmatch", "findall", "finditer", "sub", "subn", "split", "compile", "escape", "is_match", "groups", "group1", "named", "count", "replace_first"]),
    "yaml":       ("YAML",                 ["loads", "dumps", "load_file", "dump_file", "parse", "stringify", "get", "to_json", "from_json"]),
    "image":      ("Image (Pillow)",       ["open", "new", "save", "resize", "rotate", "crop", "convert", "size", "width", "height", "thumbnail", "flip_h", "flip_v", "grayscale", "show", "format", "to_bytes", "paste"]),
    "pdf":        ("PDF (pdfplumber)",     ["open", "pages", "page_count", "text", "text_of", "words", "tables", "table_of", "metadata", "lines"]),
    "xml":        ("XML",                  ["parse", "from_string", "find", "find_all", "to_dict", "find_text", "text_all"]),
    "toml":       ("TOML",                 ["loads", "load", "get", "keys", "has"]),
    "decimal":    ("Exact decimals",       ["make", "add", "sub", "mul", "div", "round", "sum", "sqrt", "quantize", "money", "percent", "average"]),
    "fraction":   ("Fractions",            ["make", "from_float", "add", "sub", "mul", "div", "numerator", "denominator", "limit", "reciprocal"]),
    "diff":       ("Difflib",              ["ratio", "is_similar", "unified", "ndiff", "close_matches", "best_match", "changed"]),
    "ip":         ("IP addresses",         ["address", "network", "is_private", "version", "hosts", "num_addresses", "contains", "is_ipv4", "is_ipv6", "first_host"]),
    "platform":   ("Platform info",        ["system", "release", "machine", "python_version", "is_windows", "is_linux", "is_mac", "summary"]),
    "unicode":    ("Unicode",              ["name", "lookup", "category", "numeric", "normalize", "nfc", "nfkc", "strip_accents"]),
    "binascii":   ("Binascii",             ["hexlify", "unhexlify", "b2a_base64", "a2b_base64", "crc32", "hex_spaced"]),
    "shlex":      ("Shell lexing",         ["split", "join", "quote", "quote_all"]),
    "string":     ("String utils",         ["capwords", "template", "substitute", "ascii_letters", "ascii_lowercase", "ascii_uppercase", "digits", "punctuation", "whitespace", "printable", "random", "random_lower", "random_upper", "random_digits_str", "filter", "exclude", "ascii_to_int", "int_to_ascii", "count_in", "translate"]),
    "struct":     ("Struct packing",       ["pack", "unpack", "calcsize", "hexdump", "unpack_list", "first", "pad", "byte_order", "to_hex", "from_hex"]),
    "zlib":       ("Compression",          ["compress", "decompress", "compress_b64", "decompress_b64", "compress_str", "decompress_str", "crc32", "adler32", "adler32_hex", "saved_bytes", "is_zlib", "compress_ratio"]),
    "calendar":   ("Calendar",             ["is_leap", "days_in_month", "month_name", "day_name", "month_text", "is_weekday", "is_weekend", "day_of_year", "week_of_year", "quarter", "next_month", "prev_month"]),
    "email":      ("Email",                ["make", "parse", "parse_address", "valid_address", "body", "html_body", "to_bytes", "all_attachments", "address_list", "quick", "cc", "bcc"]),
    "collections":("Collections",          ["counter", "deque", "ordered", "defaultdict", "namedtuple", "most_common"]),
    "itertools":  ("Itertools",            ["chain", "zip_longest", "product", "combinations", "permutations", "islice", "cycle", "repeat", "count", "groupby", "takewhile", "dropwhile"]),
    "functools":  ("Functools",            ["reduce", "partial", "lru_cache", "cached_property", "wraps", "total_ordering"]),
    "io":         ("IO",                   ["StringIO", "BytesIO", "read", "write", "getvalue"]),
    "copy":       ("Copy",                 ["copy", "deepcopy"]),
    "base64":     ("Base64",               ["encode", "decode", "encode_bytes", "decode_bytes", "urlsafe_encode", "urlsafe_decode"]),
    "url":        ("URL",                  ["encode", "decode", "parse", "join", "quote", "unquote", "build"]),
    "statistics": ("Statistics",           ["mean", "median", "mode", "stdev", "variance", "pstdev", "pvariance", "fmean", "summary"]),
    "color":      ("Color",                ["hex_to_rgb", "rgb_to_hex", "lighten", "darken", "blend", "is_valid", "complementary"]),
    "crypto":     ("Crypto/hash",          ["md5", "sha1", "sha256", "sha512", "hmac", "uuid", "token", "token_bytes"]),
    "contextlib": ("Contextlib",           ["suppress", "contextmanager", "nullcontext", "redirect_stdout"]),
    "enum":       ("Enum",                 ["make", "names", "values", "from_value"]),
    "dataclasses":("Dataclasses",          ["make", "fields", "asdict", "astuple", "replace"]),
    "typing":     ("Typing",               ["List", "Dict", "Optional", "Union", "Tuple", "Any", "Callable"]),
    "threading":  ("Threading",            ["thread", "lock", "event", "start", "join", "is_alive"]),
    "queue":      ("Queue",                ["Queue", "put", "get", "empty", "full", "qsize"]),
    "heapq":      ("Heapq",                ["push", "pop", "heapify", "nlargest", "nsmallest", "merge"]),
    "bisect":     ("Bisect",               ["left", "right", "insort_left", "insort_right"]),
    "operator":   ("Operator",             ["add", "sub", "mul", "truediv", "floordiv", "mod", "pow", "neg", "lt", "le", "eq", "ne", "ge", "gt", "and_", "or_", "not_", "getitem"]),
    "pprint":     ("Pretty print",         ["pprint", "pformat", "isreadable", "isrecursive"]),
    "log":        ("Logging",               ["setup", "debug", "info", "warning", "error", "critical", "get", "child", "to_file", "set_level", "format", "disable", "enable"]),
    "config":     ("Config files",          ["load", "save", "reload", "get", "set", "sections", "keys", "has", "env", "env_set", "env_del", "dotenv"]),
    "shell":      ("Shell / subprocess",    ["run", "output", "lines", "code", "ok", "bg", "pipe", "kill", "terminate", "wait", "communicate", "poll", "getcwd", "username", "hostname", "cpu_count", "env", "which", "home"]),
    "archive":    ("Archives",              ["zip", "unzip", "zip_list", "zip_add", "zip_read", "zip_extract_one", "tar", "untar", "tar_list", "tar_extract_one", "gzip", "gunzip", "bzip2", "bunzip2", "lzma", "unlzma", "inspect"]),
    "mail":       ("Mail (SMTP/IMAP)",      ["send", "send_html", "send_with_attachment", "message", "html_message", "attach", "connect", "connect_tls", "login", "deliver", "close", "parse", "subject", "imap_connect", "imap_list", "imap_select", "imap_search", "imap_fetch", "imap_close"]),
    "csv":        ("CSV files",             ["read", "rows", "headers", "read_string", "write", "write_rows", "append", "filter", "col", "count", "to_json"]),
    "store":      ("Key-value store",       ["set", "get", "delete", "all", "keys", "values", "clear", "has"]),
    "db":         ("Database (SQLite/Postgres/MySQL)", ["connect", "close", "ping", "reconnect", "in_transaction", "exec", "execmany", "query", "fetchone", "fetchall", "fetchmany", "insert", "insertmany", "update", "delete", "table_exists", "tables", "columns", "count", "get", "begin", "commit", "rollback", "transaction", "savepoint", "vacuum", "backup", "truncate", "db_type", "server_version"]),
    # New in v2.8.0 — database & serialization
    "sqlite":     ("SQLite3",                  ["connect", "close", "commit", "rollback", "begin", "in_transaction", "set_timeout", "as_dict", "execute", "executemany", "executescript", "fetchall", "fetchone", "fetchmany", "scalar", "query", "query_one", "run", "all_rows", "find", "find_one", "exists", "to_dicts", "search", "delete_many", "insert", "insert_many", "upsert", "update", "delete", "truncate", "create_table", "drop_table", "table_exists", "tables", "columns", "column_types", "count", "index_create", "index_drop", "as_dicts", "row_as_dict", "last_id", "changes", "sum", "avg", "min_val", "max_val", "savepoint", "release", "rollback_to", "wal_mode", "foreign_keys", "user_version", "export_csv", "import_csv", "export_json", "vacuum", "backup", "integrity_check", "pragma", "views", "page_count", "page_size"]),
    "pickle":     ("Pickle serialization",     ["dumps", "loads", "dumps_proto", "copy", "save", "load", "save_gz", "load_gz", "to_base64", "from_base64", "to_hex", "from_hex", "is_pickle", "size", "protocol", "append_to", "load_list", "compress", "decompress"]),
    # New in v2.8.0 — file & path
    "glob":       ("File pattern matching",    ["glob", "rglob", "escape", "files", "files_r", "dirs", "dirs_r", "by_ext", "by_ext_r", "count", "any", "first", "newest", "oldest", "largest", "sort_by_name", "sort_by_date", "sort_by_size"]),
    "tempfile":   ("Temporary files/dirs",     ["file", "named", "in_dir", "mkstemp", "dir", "in_dir_dir", "gettempdir"]),
    "fnmatch":    ("Filename pattern match",   ["match", "imatch", "filter", "ifilter", "reject", "translate", "any_match", "all_match"]),
    "fileinput":  ("Multi-file line tools",    ["lines", "lines_raw", "lines_multi", "numbered", "head", "tail", "slice", "grep", "grep_n", "contains", "count_lines", "count_words", "count_chars", "replace", "replace_save", "strip_empty", "unique_lines"]),
    "stat":       ("File mode inspection",     ["of", "mode", "filemode", "octal", "perms", "is_file", "is_dir", "is_link", "is_exec", "is_readable", "is_writable", "readable", "writable", "executable"]),
    "shelve":     ("Shelve persistent dict",   ["open", "close", "sync", "get", "set", "delete", "has", "pop", "setdefault", "keys", "values", "items", "all", "count", "clear", "update", "rename", "increment"]),
    "plist":      ("Property list (plistlib)", ["load", "save", "load_binary", "save_binary", "loads", "dumps", "loads_binary", "dumps_binary", "get", "set", "has", "keys", "values", "items", "merge", "remove", "to_json", "from_json", "to_dict", "fmt"]),
    "textwrap":   ("Text wrap & fill",         ["wrap", "fill", "shorten", "indent", "dedent", "center", "truncate"]),
    "getpass":    ("Secure password prompts",  ["ask", "password", "user"]),
    "cmath":      ("Complex-number math",      ["complex", "rect", "polar", "phase", "modulus", "conjugate", "sqrt", "exp", "log", "log10", "sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "asinh", "acosh", "atanh", "is_nan", "is_inf", "is_finite", "is_close", "pi", "e", "tau", "inf", "nan"]),
    "array":      ("Compact typed arrays",     ["of", "zeros", "range", "to_bytes", "from_bytes", "to_list", "item_size", "typecode", "length", "sum", "min", "max", "index", "count_of", "get", "slice", "append", "extend", "insert", "pop", "remove", "set", "reverse", "concat", "byteswap", "to_file", "from_file"]),
    "gc":         ("Garbage-collector control", ["collect", "enable", "disable", "is_enabled", "count", "stats", "threshold", "set_threshold", "objects", "referrers", "referents", "is_tracked", "garbage", "freeze", "unfreeze"]),
    "inspect":    ("Object introspection",     ["source", "source_lines", "doc", "comments", "file", "module", "signature", "parameters", "mro", "members", "source_file", "annotations", "defaults", "closure", "unwrap", "frame", "stack", "is_function", "is_class", "is_method", "is_module", "is_generator", "is_coroutine", "is_builtin", "is_abstract", "is_generator_function", "is_async_generator", "is_routine"]),
    "traceback":  ("Exception formatting",     ["format", "print", "format_exception", "message", "stack", "print_stack", "extract", "frames", "format_frames"]),
    "warnings":   ("Warning control",          ["warn", "deprecated", "ignore", "once", "always", "error", "filter", "reset"]),
    "weakref":    ("Weak references",          ["ref", "proxy", "deref", "is_alive", "count", "refs", "dict", "key_dict", "set", "finalize"]),
    "types":      ("Dynamic type helpers",     ["namespace", "readonly", "new_class", "module", "method", "cell", "resolve_bases", "is_function", "is_lambda", "is_method", "is_module", "is_generator", "is_builtin", "is_coroutine", "is_async_generator", "is_frame", "is_code", "is_traceback"]),
    "abc":        ("Abstract base classes",    ["is_abstract", "abstract_methods", "cache_token", "register", "is_subclass", "is_instance"]),
    "signal":     ("OS signal helpers",        ["number", "name", "describe", "valid", "get", "on", "ignore", "default", "send", "alarm", "set_timer", "get_timer", "pause"]),
    "mmap":       ("Memory-mapped reads",      ["read", "slice", "size", "find", "contains", "count", "open", "get", "put", "length", "search", "flush", "close"]),
    "atexit":     ("Exit-time callbacks",      ["register", "unregister", "run"]),
    "locale":     ("Locale-aware formatting",  ["get", "set", "encoding", "number", "decimal", "currency", "atof", "atoi", "currency_intl", "delocalize", "normalize", "format"]),
    "gettext":    ("Message translation",      ["t", "plural", "translation", "install", "find"]),
    "argparse":   ("CLI argument parsing",     ["parse", "parse_dict", "new", "add", "run", "run_known", "to_dict"]),
    "sysconfig":  ("Install paths & config",   ["paths", "path", "path_names", "vars", "var", "platform", "version"]),
    "resource":   ("Process resource usage",   ["usage", "max_rss", "user_time", "sys_time", "limit", "set_limit", "page_size"]),
    "socket":     ("TCP/IP sockets",           ["hostname", "fqdn", "host_to_ip", "ip_to_host", "resolve", "connect", "send", "recv", "close", "is_open", "free_port", "tcp", "server", "bind", "listen", "accept", "udp", "send_to", "recv_from", "set_timeout", "reuse", "local", "peer", "shutdown", "file"]),
    "ssl":        ("TLS/SSL helpers",          ["context", "unverified", "server_context", "wrap", "server_cert", "cert_dict", "pem_to_der", "verify_paths", "load_ca", "set_ciphers", "ciphers", "check_hostname"]),
    "ftp":        ("FTP client",               ["new", "connect", "connect_tls", "quit", "list", "details", "pwd", "cwd", "size", "download", "upload", "delete", "rename", "mkdir", "rmdir", "passive", "command"]),
    "pop3":       ("POP3 mail retrieval",      ["connect", "connect_ssl", "login", "quit", "count", "size", "list", "get", "text", "top", "uidl", "delete", "reset", "noop"]),
    "xmlrpc":     ("XML-RPC client",           ["client", "call", "dumps", "loads", "binary", "datetime"]),
    "httpserver": ("Tiny HTTP server",         ["files", "server", "handler", "threaded", "handle_one", "serve", "serve_async", "port", "close", "stop"]),
    "selectors":  ("I/O multiplexing",         ["new", "close", "watch_read", "watch_write", "register", "modify", "unwatch", "watched", "count", "read", "write", "wait"]),
    "html":       ("HTML escape & scrape",     ["escape", "unescape", "strip_tags", "text", "links", "images", "tags"]),
    "webbrowser": ("Open URLs in a browser",   ["open", "open_new", "open_tab", "get"]),
    "mimetypes":  ("Guess MIME types",         ["guess", "full", "is_text", "is_image", "extension", "extensions", "add", "types", "suffix_map", "encodings_map", "init"]),
    "multiprocessing": ("Process parallelism", ["cpus", "pool", "map", "starmap", "apply", "imap", "process", "start", "join", "current", "active", "set_start", "queue", "manager", "lock", "event", "semaphore", "pipe", "value", "array"]),
    "futures":    ("Thread/process pools",     ["threads", "processes", "shutdown", "thread_map", "process_map", "map", "submit", "result", "done", "running", "cancelled", "cancel", "exception", "on_done", "wait", "wait_first", "as_done"]),
    "sched":      ("Event scheduling",         ["new", "run", "after", "at", "cancel", "empty", "queue"]),
    "timeit":     ("Micro-benchmarking",       ["run", "each", "repeat", "best", "auto"]),
    "profile":    ("Deterministic profiling",  ["run", "calls", "time", "print", "dump"]),
    "doctest":    ("Docstring example tests",  ["run", "passed", "examples", "module", "object"]),
    "unittest":   ("Run TestCase classes",     ["run", "passed", "count", "failures", "suite", "run_suite", "discover", "assert_equal", "assert_true", "assert_in", "assert_raises", "mock", "patch"]),
    "ast":        ("Python source ↔ AST",     ["parse", "dump", "unparse", "compile", "literal", "walk", "node_types", "names", "functions", "classes", "imports", "constants", "docstring", "is_valid", "parse_eval", "fields", "children", "fix", "increment"]),
    "dis":        ("Bytecode disassembler",    ["disasm", "instructions", "opnames", "stack_size", "consts", "names", "varnames", "code", "code_info", "opname"]),
    "keyword":    ("Keyword inspection",       ["is_keyword", "is_soft", "all", "soft", "count"]),
    "importlib":  ("Dynamic import helpers",   ["load", "attr", "reload", "from_path", "exists", "invalidate", "spec", "find", "origin"]),
    "graphlib":   ("Topological sorting",      ["sort", "sort_groups", "is_dag", "new", "add", "ready", "done"]),
    "reprlib":    ("Truncating repr",          ["repr", "short", "recursive"]),
    "tracemalloc": ("Memory allocation trace", ["start", "stop", "is_tracing", "snapshot", "top", "diff", "current"]),
    "shutil":     ("High-level file ops",      ["copy", "copy_data", "copy_tree", "copy2", "move", "rm", "rmtree", "disk_usage", "free", "which", "unpack", "make_archive", "archive_formats", "terminal_size", "copy_mode", "copy_stat", "chown"]),
    "filecmp":    ("File/dir comparison",      ["equal", "shallow", "dircmp", "same_files", "diff_files", "left_only", "right_only", "common", "compare", "clear_cache"]),
    "configparser": ("INI config files",       ["load", "loads", "new", "get", "getint", "getfloat", "getbool", "sections", "keys", "items", "has", "set", "add_section", "remove_section", "remove_key", "read_dict", "to_dict", "has_section", "save", "dumps"]),
    "errno":      ("OS error-code helpers",    ["name", "description", "code", "all", "ENOENT", "EEXIST", "EACCES", "EPERM", "ENOTEMPTY", "EINVAL", "EBADF"]),
    "linecache":  ("Cached source lines",      ["line", "lines", "count", "check", "clear"]),
    "numbers":    ("Numeric-tower ABC checks", ["is_number", "is_complex", "is_real", "is_rational", "is_integral"]),
}


def build_command_completions() -> list[types.CompletionItem]:
    items = []
    for name, kind, detail, doc in COMMANDS:
        items.append(types.CompletionItem(
            label=f"@{name}",
            kind=kind,
            detail=detail,
            documentation=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**`{detail}`**\n\n{doc}",
            ),
            insert_text=name,
        ))
    return items


def build_namespace_completions() -> list[types.CompletionItem]:
    items = []
    for ns, (desc, _methods) in NAMESPACES.items():
        items.append(types.CompletionItem(
            label=f"@{ns}",
            kind=CIK.Module,
            detail=f"@{ns}.* — {desc}",
            documentation=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**`@{ns}.*`** — {desc}\n\nType `@{ns}.` to see available methods.",
            ),
            insert_text=ns,
        ))
    return items


def build_method_completions(namespace: str) -> list[types.CompletionItem]:
    if namespace not in NAMESPACES:
        return []
    desc, methods = NAMESPACES[namespace]
    return [
        types.CompletionItem(
            label=method,
            kind=CIK.Method,
            detail=f"@{namespace}.{method}[...]",
            documentation=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**`@{namespace}.{method}[...]`** — {desc} method.",
            ),
            insert_text=method,
        )
        for method in methods
    ]


def get_command_docs(name: str) -> str | None:
    for cmd_name, _kind, detail, doc in COMMANDS:
        if cmd_name == name:
            return f"**`{detail}`**\n\n{doc}"
    return None


def get_namespace_docs(namespace: str, method: str | None = None) -> str | None:
    if namespace not in NAMESPACES:
        return None
    desc, methods = NAMESPACES[namespace]
    if method:
        if method in methods:
            return f"**`@{namespace}.{method}[...]`** — {desc} method."
        return None
    return f"**`@{namespace}.*`** — {desc}.\n\nMethods: {', '.join(methods[:8])}{'...' if len(methods) > 8 else ''}"
