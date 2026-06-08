# Cruhon Library Support

Cruhon wraps Python libraries with its own syntax.
The user must have the relevant Python library already installed when using `@import[lib]`.

---

## ✅ Supported Libraries

| Cruhon               | Python          | Since   |
|----------------------|-----------------|---------|
| `@import[requests]`  | `requests`      | ✅ v0.1 |
| `@import[discord]`   | `discord.py`    | ✅ v0.1 |
| `@import[json]`      | `json`          | ✅ v0.1 |
| `@import[os]`        | `os`            | ✅ v0.1 |
| `@import[sys]`       | `sys`           | ✅ v0.1 |
| `@import[math]`      | `math`          | ✅ v0.1 |
| `@import[random]`    | `random`        | ✅ v0.1 |
| `@import[time]`      | `time`          | ✅ v0.1 |
| `@import[datetime]`  | `datetime`      | ✅ v0.1 |
| `@import[re]`        | `re`            | ✅ v0.1 |
| `@import[pathlib]`   | `pathlib`       | ✅ v0.1 |
| `@import[asyncio]`   | `asyncio`       | ✅ v0.1 |

---

## 🔜 Coming Soon

| Cruhon               | Python           | Planned |
|----------------------|------------------|---------|
| `@import[sqlite]`    | `sqlite3`        | v0.2    |
| `@import[postgres]`  | `psycopg2`       | v0.2    |
| `@import[flask]`     | `flask`          | v0.2    |
| `@import[fastapi]`   | `fastapi`        | v0.2    |
| `@import[pandas]`    | `pandas`         | v0.3    |
| `@import[numpy]`     | `numpy`          | v0.3    |
| `@import[redis]`     | `redis`          | v0.3    |
| `@import[dotenv]`    | `python-dotenv`  | v0.2    |
| `@import[bs4]`       | `beautifulsoup4` | v0.3    |
| `@import[pillow]`    | `Pillow`         | v0.4    |

---

## ❌ Unsupported Library Error

```
@import[pandas]
# Error: Library 'pandas' is not yet supported in Cruhon.
# See library.md for the full list.
# Want to add it? github.com/cruciblelab/cruhon/blob/main/CONTRIBUTING.md
```

---

## Contributing

Adding a new library wrapper is straightforward:

1. Add `register_lib("libname", "python_module")` to `cruhon/core/registry.py`
2. If needed, customize method calls with `register_lib_call()`
3. Add an entry to this file
4. Open a PR

Libraries can also be added as community mods — see `mods/README.md`
