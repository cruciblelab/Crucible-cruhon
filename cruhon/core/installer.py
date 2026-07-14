"""
cruhon/core/installer.py
=========================
`cruhon install <source>` — fetch a mod from PyPI or GitHub and make it
available to the current project, without hand-copying folders around.

Supported source forms:
  cruhon install cruhon-discord              → pip install cruhon-discord
  cruhon install owner/repo                  → GitHub, default branch, whole repo
  cruhon install github:owner/repo           → same, explicit prefix
  cruhon install gh:owner/repo               → same, short prefix
  cruhon install owner/repo@v1.2.0           → a specific branch/tag/commit
  cruhon install owner/repo#mods/cruhon-x    → a mod living in a subdirectory
                                                (monorepo — e.g. this repo's
                                                own mods/cruhon-discord)
  cruhon install owner/repo@main#mods/x      → both together

A source is treated as PyPI only when it has no "/" (PyPI package names
can't contain one) and no explicit "github:"/"gh:" prefix. Anything with
a "/" is GitHub-shaped by default — no prefix required.

Every install is validated before anything is placed in the project:
the fetched thing must contain a mod.json with at least "name" and
"version", and if it declares a "cruhon" version constraint, the
running Cruhon must satisfy it (same check load_mod_from_path() uses).
Nothing partial is left behind on failure.

GitHub installs land in <project>/mods/<mod-name>/, exactly where a
hand-copied local mod would go — load_all_mods() picks it up with no
extra wiring. PyPI installs are picked up automatically by
load_pip_mods() once pip has installed the package.
"""
from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

from .mod_loader import _is_compatible, CRUHON_VERSION


class InstallError(Exception):
    """Raised for any install failure — invalid source, network error,
    missing/invalid mod.json, version incompatibility, etc."""


# ─────────────────────────────────────────────────────────────
# SOURCE PARSING
# ─────────────────────────────────────────────────────────────

_GITHUB_RE = re.compile(
    r"^(?:(?P<scheme>github|gh):)?"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
    r"(?:@(?P<ref>[A-Za-z0-9_./-]+))?"
    r"(?:#(?P<subpath>[A-Za-z0-9_./-]+))?$"
)


def _parse_source(source: str) -> tuple[str, dict]:
    """
    Returns ("pypi", {"name": ...}) or ("github", {"owner", "repo", "ref", "subpath"}).
    Raises InstallError for a malformed source string.
    """
    source = source.strip()
    if not source:
        raise InstallError("Empty install source.")

    if "/" not in source and not source.startswith(("github:", "gh:")):
        return "pypi", {"name": source}

    m = _GITHUB_RE.match(source)
    if not m:
        raise InstallError(
            f"Could not parse install source: {source!r}. "
            "Expected a PyPI package name, or owner/repo[@ref][#subpath] "
            "(optionally prefixed with github:/gh:)."
        )
    return "github", {
        "owner": m.group("owner"),
        "repo": m.group("repo"),
        "ref": m.group("ref"),
        "subpath": m.group("subpath"),
    }


# ─────────────────────────────────────────────────────────────
# MANIFEST VALIDATION — shared by both install paths
# ─────────────────────────────────────────────────────────────

def _validate_manifest(mod_dir: Path) -> dict:
    """
    Confirm mod_dir looks like a real Cruhon mod: mod.json with at
    least name+version, __init__.py present, and (if declared) the
    running Cruhon satisfies the mod's "cruhon" version constraint.

    Raises InstallError with a clear reason on any failure.
    """
    manifest_path = mod_dir / "mod.json"
    init_path = mod_dir / "__init__.py"

    if not manifest_path.exists():
        raise InstallError(
            f"No mod.json found in {mod_dir} — this doesn't look like a "
            "Cruhon mod (was it actually written for Cruhon?)."
        )
    if not init_path.exists():
        raise InstallError(
            f"mod.json found but no __init__.py in {mod_dir} — "
            "incomplete/invalid mod."
        )

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise InstallError(f"mod.json in {mod_dir} is not valid JSON: {e}") from e

    if not manifest.get("name"):
        raise InstallError(f"mod.json in {mod_dir} is missing required field 'name'.")
    if not manifest.get("version"):
        raise InstallError(f"mod.json in {mod_dir} is missing required field 'version'.")

    cruhon_req = manifest.get("cruhon")
    if cruhon_req and not _is_compatible(cruhon_req):
        raise InstallError(
            f"{manifest['name']} requires cruhon {cruhon_req}, "
            f"installed is {CRUHON_VERSION}."
        )

    return manifest


# ─────────────────────────────────────────────────────────────
# PYPI INSTALL
# ─────────────────────────────────────────────────────────────

_VALIDATE_SNIPPET = """
import importlib, importlib.metadata as im, json, sys
name = sys.argv[1]
module_name = name.replace("-", "_")
out = {}
try:
    dist = im.distribution(name)
    out["version"] = dist.metadata.get("Version", "?")
    reqs = dist.metadata.get_all("Requires-Dist") or []
except Exception as e:
    print(json.dumps({"error": f"distribution metadata unreadable: {e}"}))
    sys.exit(0)
try:
    module = importlib.import_module(module_name)
except ImportError as e:
    print(json.dumps({"error": f"couldn't be imported as {module_name}: {e}"}))
    sys.exit(0)
out["has_register"] = hasattr(module, "register")
out["cruhon_requires"] = getattr(module, "CRUHON_REQUIRES", None)
if out["cruhon_requires"] is None:
    for req in reqs:
        if req.startswith("cruhon ") or req.startswith("cruhon>=") or req.startswith("cruhon>"):
            out["cruhon_requires"] = req.split("cruhon", 1)[1].strip().lstrip("=").lstrip()
            break
print(json.dumps(out))
"""


def _install_pypi(name: str, log) -> dict:
    log(f"Installing {name} from PyPI...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", name],
            capture_output=True, text=True, timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise InstallError(f"Failed to run pip: {e}") from e

    if result.returncode != 0:
        raise InstallError(
            f"pip install {name} failed:\n{result.stderr.strip() or result.stdout.strip()}"
        )

    if not name.startswith("cruhon-"):
        raise InstallError(
            f"{name} was installed, but its package name doesn't start "
            "with 'cruhon-' — this isn't a Cruhon mod naming convention "
            "match, refusing to register it as one. It's still installed "
            "via pip if you needed it for something else."
        )

    # Validate in a fresh subprocess, not this already-running process:
    # a package that didn't exist when this interpreter started isn't
    # guaranteed to be importable here (site/.pth processing happens once
    # at interpreter startup) even though pip install just succeeded. A
    # subsequent `cruhon run` — always a fresh process — sees it fine;
    # this mirrors that instead of chasing same-process import caching.
    try:
        check = subprocess.run(
            [sys.executable, "-c", _VALIDATE_SNIPPET, name],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise InstallError(f"Failed to validate {name} after install: {e}") from e

    if check.returncode != 0 or not check.stdout.strip():
        raise InstallError(
            f"Failed to validate {name} after install:\n"
            f"{check.stderr.strip() or check.stdout.strip()}"
        )
    info = json.loads(check.stdout.strip().splitlines()[-1])

    if "error" in info:
        raise InstallError(f"{name} installed via pip but {info['error']}")
    if not info.get("has_register"):
        raise InstallError(
            f"{name} was installed and imports fine, but has no register() "
            "function — this doesn't look like it was written for Cruhon."
        )

    cruhon_req = info.get("cruhon_requires")
    if cruhon_req and not _is_compatible(cruhon_req):
        raise InstallError(
            f"{name} requires cruhon {cruhon_req}, installed is {CRUHON_VERSION}. "
            f"It has been pip-installed but will be skipped at load time."
        )

    version = info.get("version", "?")
    log(f"✓ {name} v{version} installed and validated as a Cruhon mod.")
    return {"name": name, "version": version, "source": "pypi"}


# ─────────────────────────────────────────────────────────────
# GITHUB INSTALL
# ─────────────────────────────────────────────────────────────

def _http_get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "cruhon-installer"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise InstallError(f"GitHub request failed ({e.code}) for {url}") from e
    except urllib.error.URLError as e:
        raise InstallError(f"Could not reach GitHub: {e.reason}") from e


def _github_default_branch(owner: str, repo: str) -> str:
    data = _http_get(f"https://api.github.com/repos/{owner}/{repo}")
    try:
        return json.loads(data).get("default_branch", "main")
    except json.JSONDecodeError:
        return "main"


def _download_github_zip(owner: str, repo: str, ref: str) -> bytes:
    # This form works uniformly for branch names, tag names, and commit
    # SHAs — no need to guess whether ref is a branch or a tag.
    url = f"https://github.com/{owner}/{repo}/archive/{ref}.zip"
    return _http_get(url, timeout=60)


def _find_mod_dirs(root: Path) -> list[Path]:
    """Every directory under root containing a mod.json, root itself included."""
    found = []
    if (root / "mod.json").exists():
        found.append(root)
    for p in sorted(root.rglob("mod.json")):
        if p.parent != root:
            found.append(p.parent)
    return found


def _install_github(owner: str, repo: str, ref: Optional[str],
                     subpath: Optional[str], project_dir: Path, log) -> dict:
    resolved_ref = ref or _github_default_branch(owner, repo)
    log(f"Fetching {owner}/{repo}@{resolved_ref} from GitHub...")
    zip_bytes = _download_github_zip(owner, repo, resolved_ref)

    with tempfile.TemporaryDirectory(prefix="cruhon_install_") as tmp:
        tmp_path = Path(tmp)
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                zf.extractall(tmp_path)
        except zipfile.BadZipFile as e:
            raise InstallError(f"GitHub returned an invalid archive: {e}") from e

        # GitHub zips nest everything under a single "<repo>-<ref>/" dir.
        roots = [p for p in tmp_path.iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise InstallError("Unexpected archive layout from GitHub.")
        repo_root = roots[0]

        if subpath:
            mod_dir = repo_root / subpath
            if not mod_dir.is_dir():
                raise InstallError(
                    f"Subpath {subpath!r} not found in {owner}/{repo}@{resolved_ref}."
                )
            candidates = [mod_dir] if (mod_dir / "mod.json").exists() else []
        else:
            candidates = _find_mod_dirs(repo_root)

        if not candidates:
            raise InstallError(
                f"No mod.json found in {owner}/{repo}@{resolved_ref}"
                + (f" at {subpath}" if subpath else "")
                + " — this doesn't look like a Cruhon mod "
                  "(was it actually written for Cruhon?)."
            )
        if len(candidates) > 1:
            rels = ", ".join(str(c.relative_to(repo_root)) for c in candidates)
            raise InstallError(
                f"Multiple mods found in {owner}/{repo}: {rels}. "
                f"Specify which one with owner/repo#<subpath>."
            )

        mod_dir = candidates[0]
        manifest = _validate_manifest(mod_dir)

        dest = project_dir / "mods" / manifest["name"]
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(mod_dir, dest)

    log(f"✓ {manifest['name']} v{manifest['version']} installed to {dest}")
    return {"name": manifest["name"], "version": manifest["version"], "source": "github"}


# ─────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ─────────────────────────────────────────────────────────────

def install(source: str, project_dir: Optional[Path] = None, log=print) -> dict:
    """
    Install a mod from PyPI or GitHub into project_dir (defaults to cwd).
    Returns {"name", "version", "source"} on success.
    Raises InstallError on any failure — nothing partial is left behind.
    """
    project_dir = Path(project_dir) if project_dir else Path.cwd()
    kind, spec = _parse_source(source)

    if kind == "pypi":
        return _install_pypi(spec["name"], log)
    return _install_github(
        spec["owner"], spec["repo"], spec["ref"], spec["subpath"], project_dir, log
    )
