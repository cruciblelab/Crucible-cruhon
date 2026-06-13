"""
cruhon/core/cache.py
====================
Transpile cache — avoids re-parsing and re-transpiling unchanged .clpy files.

Cache location:  <project_root>/.cruhon_cache/
Cache format:    opaque binary — magic header + key hash + marshal'd code object.
                 NOT a readable Python file; cannot be directly imported or executed
                 outside the Cruhon runner.

Cache key:       SHA-256 of:
                   file content
                   + all @include / @use dependency file contents (recursive)
                   + Cruhon version string
                   + Python version (major.minor)
                   + loaded mod names + versions (sorted)

Invalidation:    Any change to any of the above inputs → cache miss → re-transpile.

Errors:          All cache operations are best-effort. Any read/write failure
                 silently falls back to full transpilation. A run never fails
                 because of a cache problem.
"""
from __future__ import annotations

import hashlib
import marshal
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Binary magic that identifies a valid Cruhon cache file.
_MAGIC = b"CRUHON\x00CACHE\x00V1\n"

# Regex to extract path arguments from @include and @use without a full parse.
# Handles: @include["path"], @include[path], @use["path"], @use[path as alias]
_DEP_RE = re.compile(
    r'@(?:include|use)\s*\[\s*["\']?([^"\';\]\s]+)["\']?'
)


# ─────────────────────────────────────────────────────────────
# DEPENDENCY SCANNING
# ─────────────────────────────────────────────────────────────

def _scan_deps(source: str, base_dir: Path, visited: set) -> list[Path]:
    """
    Regex scan for @include / @use dependencies without a full parse.

    Returns a list of resolved dependency paths (not including base_dir itself).
    visited is mutated in place to prevent cycles.
    """
    deps: list[Path] = []
    for m in _DEP_RE.finditer(source):
        raw = m.group(1).strip()
        # @use supports "path as alias" — strip the alias part
        if " as " in raw:
            raw = raw.split(" as ", 1)[0].strip()
        # Resolve relative to current file's directory
        candidate = (base_dir / raw).resolve()
        if not candidate.suffix:
            candidate = candidate.with_suffix(".clpy")
        if candidate in visited or not candidate.exists():
            continue
        visited.add(candidate)
        deps.append(candidate)
        # Recurse into dependency
        try:
            sub_source = candidate.read_text(encoding="utf-8")
            deps.extend(_scan_deps(sub_source, candidate.parent, visited))
        except OSError:
            pass
    return deps


# ─────────────────────────────────────────────────────────────
# KEY BUILDING
# ─────────────────────────────────────────────────────────────

def build_key(
    source: str,
    base_dir: Path,
    cruhon_version: str,
    mod_fingerprint: str,
) -> str:
    """
    Build a hex cache key from all cache-invalidating inputs.

    Inputs:
      source          — raw .clpy source text
      base_dir        — directory of the source file (for dep resolution)
      cruhon_version  — e.g. "2.7.0"
      mod_fingerprint — sorted "name:version|..." string of loaded mods
    """
    h = hashlib.sha256()

    # 1. File content
    h.update(source.encode("utf-8"))

    # 2. All dependency file contents (sorted for determinism)
    deps = sorted(_scan_deps(source, base_dir, set()), key=lambda p: str(p))
    for dep in deps:
        try:
            h.update(dep.read_bytes())
        except OSError:
            h.update(str(dep).encode())  # include path even if unreadable

    # 3. Cruhon version
    h.update(cruhon_version.encode("ascii"))

    # 4. Python version (major.minor) — marshal format varies across versions
    h.update(f"{sys.version_info.major}.{sys.version_info.minor}".encode("ascii"))

    # 5. Mod fingerprint
    h.update(mod_fingerprint.encode("utf-8"))

    return h.hexdigest()


# ─────────────────────────────────────────────────────────────
# PATH HELPERS
# ─────────────────────────────────────────────────────────────

def _cache_file(source_path: Path, cache_dir: Path) -> Path:
    """Return the .cache path for a given source file."""
    try:
        rel = source_path.relative_to(cache_dir.parent)
    except ValueError:
        rel = Path(source_path.name)
    return cache_dir / (str(rel) + ".cache")


# ─────────────────────────────────────────────────────────────
# LOAD
# ─────────────────────────────────────────────────────────────

def try_load(
    source_path: Path,
    key: str,
    cache_dir: Path,
) -> Optional[object]:
    """
    Try to load a cached code object.

    Returns a compiled code object on hit, None on any miss or error.
    Silently deletes corrupted cache files.
    """
    cp = _cache_file(source_path, cache_dir)
    try:
        data = cp.read_bytes()
    except OSError:
        return None  # file doesn't exist — normal cache miss

    try:
        if not data.startswith(_MAGIC):
            raise ValueError("bad magic")
        rest = data[len(_MAGIC):]
        nl = rest.index(b"\n")
        stored_key = rest[:nl].decode("ascii")
        if stored_key != key:
            return None  # key mismatch — stale cache
        return marshal.loads(rest[nl + 1:])
    except Exception:
        # Corrupted file — delete and treat as miss
        try:
            cp.unlink(missing_ok=True)
        except OSError:
            pass
        return None


# ─────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────

def save(
    source_path: Path,
    key: str,
    python_code: str,
    filename: str,
    cache_dir: Path,
) -> None:
    """
    Compile python_code and atomically write a cache file.

    All errors are silently swallowed — a failed cache write never
    interrupts a successful run.
    """
    cp = _cache_file(source_path, cache_dir)
    try:
        code_obj = compile(python_code, f"<cruhon:{filename}>", "exec")
        payload = (
            _MAGIC
            + key.encode("ascii") + b"\n"
            + marshal.dumps(code_obj)
        )
        cp.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: write to a temp file, then rename.
        # This prevents partial cache files if the process is interrupted.
        fd, tmp = tempfile.mkstemp(dir=cp.parent, prefix=".cruhon_tmp_")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(payload)
            os.replace(tmp, cp)  # atomic on POSIX; near-atomic on Windows
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except Exception:
        pass  # cache write failure is always silent


# ─────────────────────────────────────────────────────────────
# MANAGEMENT
# ─────────────────────────────────────────────────────────────

def clear(cache_dir: Path) -> int:
    """Delete all .cache files under cache_dir. Returns count deleted."""
    count = 0
    try:
        for p in cache_dir.rglob("*.cache"):
            try:
                p.unlink()
                count += 1
            except OSError:
                pass
    except Exception:
        pass
    return count


def stats(cache_dir: Path) -> dict:
    """Return basic cache statistics."""
    total_files = 0
    total_bytes = 0
    try:
        for p in cache_dir.rglob("*.cache"):
            try:
                total_files += 1
                total_bytes += p.stat().st_size
            except OSError:
                pass
    except Exception:
        pass
    return {"files": total_files, "bytes": total_bytes, "dir": str(cache_dir)}
