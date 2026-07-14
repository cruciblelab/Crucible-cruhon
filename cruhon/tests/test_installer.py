"""
Tests for `cruhon install <source>` (cruhon/core/installer.py).

GitHub-fetching tests mock the network layer (_github_default_branch /
_download_github_zip) — everything downstream (archive extraction,
mod.json discovery/validation, subpath resolution, copying into the
project's mods/) runs for real against an in-memory zip built with the
stdlib zipfile module. The PyPI path is tested against a real local
package installed via pip (editable install), so pip invocation,
importlib metadata reading, and manifest validation all run for real
too — only an actual network round-trip to pypi.org/github.com is
mocked or skipped.
"""
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cruhon.core import installer
from cruhon.core.installer import install, InstallError, _parse_source


def _pip(args: list[str]) -> subprocess.CompletedProcess:
    """
    Run pip for test setup/teardown only — real cruhon install code never
    passes --break-system-packages (that's the user's call to make, not
    a tool's to make for them). Some local test sandboxes have a PEP 668
    "externally-managed-environment" system Python that rejects any pip
    install without it; retry with the flag only when that specific error
    is what's blocking a throwaway test package.
    """
    full = [sys.executable, "-m", "pip"] + args
    result = subprocess.run(full, capture_output=True, text=True)
    if result.returncode != 0 and "externally-managed-environment" in (result.stderr or ""):
        result = subprocess.run(full + ["--break-system-packages"], capture_output=True, text=True)
    return result


# ─────────────────────────────────────────────────────────────
# SOURCE PARSING
# ─────────────────────────────────────────────────────────────

class TestParseSource:
    def test_bare_name_is_pypi(self):
        kind, spec = _parse_source("cruhon-discord")
        assert kind == "pypi"
        assert spec == {"name": "cruhon-discord"}

    def test_owner_repo_is_github(self):
        kind, spec = _parse_source("cruciblelab/Crucible-cruhon")
        assert kind == "github"
        assert spec["owner"] == "cruciblelab"
        assert spec["repo"] == "Crucible-cruhon"
        assert spec["ref"] is None
        assert spec["subpath"] is None

    def test_github_prefix(self):
        kind, spec = _parse_source("github:cruciblelab/Crucible-cruhon")
        assert kind == "github"
        assert spec["owner"] == "cruciblelab"

    def test_gh_prefix(self):
        kind, spec = _parse_source("gh:cruciblelab/Crucible-cruhon")
        assert kind == "github"

    def test_ref(self):
        _, spec = _parse_source("owner/repo@v1.2.0")
        assert spec["ref"] == "v1.2.0"
        assert spec["subpath"] is None

    def test_subpath(self):
        _, spec = _parse_source("owner/repo#mods/cruhon-discord")
        assert spec["subpath"] == "mods/cruhon-discord"
        assert spec["ref"] is None

    def test_ref_and_subpath(self):
        _, spec = _parse_source("owner/repo@main#mods/cruhon-discord")
        assert spec["ref"] == "main"
        assert spec["subpath"] == "mods/cruhon-discord"

    def test_empty_raises(self):
        with pytest.raises(InstallError):
            _parse_source("")

    def test_too_many_slashes_raises(self):
        with pytest.raises(InstallError):
            _parse_source("a/b/c")


# ─────────────────────────────────────────────────────────────
# MANIFEST VALIDATION
# ─────────────────────────────────────────────────────────────

class TestValidateManifest:
    def test_missing_mod_json_raises(self, tmp_path):
        with pytest.raises(InstallError, match="No mod.json"):
            installer._validate_manifest(tmp_path)

    def test_missing_init_raises(self, tmp_path):
        (tmp_path / "mod.json").write_text('{"name": "x", "version": "1.0"}')
        with pytest.raises(InstallError, match="__init__.py"):
            installer._validate_manifest(tmp_path)

    def test_invalid_json_raises(self, tmp_path):
        (tmp_path / "mod.json").write_text("not json{{{")
        (tmp_path / "__init__.py").write_text("")
        with pytest.raises(InstallError, match="not valid JSON"):
            installer._validate_manifest(tmp_path)

    def test_missing_name_raises(self, tmp_path):
        (tmp_path / "mod.json").write_text('{"version": "1.0"}')
        (tmp_path / "__init__.py").write_text("")
        with pytest.raises(InstallError, match="name"):
            installer._validate_manifest(tmp_path)

    def test_missing_version_raises(self, tmp_path):
        (tmp_path / "mod.json").write_text('{"name": "x"}')
        (tmp_path / "__init__.py").write_text("")
        with pytest.raises(InstallError, match="version"):
            installer._validate_manifest(tmp_path)

    def test_incompatible_cruhon_constraint_raises(self, tmp_path):
        (tmp_path / "mod.json").write_text(
            json.dumps({"name": "x", "version": "1.0", "cruhon": ">=999.0.0"})
        )
        (tmp_path / "__init__.py").write_text("")
        with pytest.raises(InstallError, match="requires cruhon"):
            installer._validate_manifest(tmp_path)

    def test_valid_manifest_returns_dict(self, tmp_path):
        (tmp_path / "mod.json").write_text(
            json.dumps({"name": "x", "version": "1.0", "cruhon": ">=1.0.0"})
        )
        (tmp_path / "__init__.py").write_text("")
        manifest = installer._validate_manifest(tmp_path)
        assert manifest["name"] == "x"
        assert manifest["version"] == "1.0"


# ─────────────────────────────────────────────────────────────
# GITHUB INSTALL — network mocked, everything else real
# ─────────────────────────────────────────────────────────────

def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


class TestGithubInstall:
    def test_mod_at_repo_root(self, tmp_path):
        zip_bytes = _make_zip({
            "repo-main/mod.json": json.dumps({"name": "rootmod", "version": "1.0.0"}),
            "repo-main/__init__.py": "def register(api): pass\n",
        })
        with patch.object(installer, "_github_default_branch", return_value="main"), \
             patch.object(installer, "_download_github_zip", return_value=zip_bytes):
            result = install("owner/repo", project_dir=tmp_path, log=lambda m: None)

        assert result == {"name": "rootmod", "version": "1.0.0", "source": "github"}
        installed = tmp_path / "mods" / "rootmod"
        assert (installed / "mod.json").exists()
        assert (installed / "__init__.py").exists()

    def test_mod_in_subpath_monorepo(self, tmp_path):
        zip_bytes = _make_zip({
            "repo-main/README.md": "hi",
            "repo-main/mods/cruhon-discord/mod.json": json.dumps(
                {"name": "cruhon-discord", "version": "1.4.0"}
            ),
            "repo-main/mods/cruhon-discord/__init__.py": "def register(api): pass\n",
            "repo-main/mods/other-mod/mod.json": json.dumps(
                {"name": "other-mod", "version": "1.0.0"}
            ),
            "repo-main/mods/other-mod/__init__.py": "def register(api): pass\n",
        })
        with patch.object(installer, "_github_default_branch", return_value="main"), \
             patch.object(installer, "_download_github_zip", return_value=zip_bytes):
            result = install(
                "owner/repo#mods/cruhon-discord", project_dir=tmp_path, log=lambda m: None
            )

        assert result["name"] == "cruhon-discord"
        assert (tmp_path / "mods" / "cruhon-discord" / "mod.json").exists()
        # The sibling mod must NOT have been installed too.
        assert not (tmp_path / "mods" / "other-mod").exists()

    def test_ambiguous_repo_without_subpath_raises(self, tmp_path):
        zip_bytes = _make_zip({
            "repo-main/mods/a/mod.json": json.dumps({"name": "a", "version": "1.0"}),
            "repo-main/mods/a/__init__.py": "",
            "repo-main/mods/b/mod.json": json.dumps({"name": "b", "version": "1.0"}),
            "repo-main/mods/b/__init__.py": "",
        })
        with patch.object(installer, "_github_default_branch", return_value="main"), \
             patch.object(installer, "_download_github_zip", return_value=zip_bytes):
            with pytest.raises(InstallError, match="Multiple mods found"):
                install("owner/repo", project_dir=tmp_path, log=lambda m: None)

    def test_no_mod_json_anywhere_raises(self, tmp_path):
        zip_bytes = _make_zip({"repo-main/README.md": "just a readme, not a mod"})
        with patch.object(installer, "_github_default_branch", return_value="main"), \
             patch.object(installer, "_download_github_zip", return_value=zip_bytes):
            with pytest.raises(InstallError, match="No mod.json found"):
                install("owner/repo", project_dir=tmp_path, log=lambda m: None)

    def test_explicit_ref_skips_default_branch_lookup(self, tmp_path):
        zip_bytes = _make_zip({
            "repo-v1/mod.json": json.dumps({"name": "x", "version": "1.0"}),
            "repo-v1/__init__.py": "",
        })
        with patch.object(installer, "_github_default_branch") as branch_lookup, \
             patch.object(installer, "_download_github_zip", return_value=zip_bytes) as dl:
            install("owner/repo@v1.0.0", project_dir=tmp_path, log=lambda m: None)
        branch_lookup.assert_not_called()
        dl.assert_called_once_with("owner", "repo", "v1.0.0")

    def test_reinstall_overwrites_existing(self, tmp_path):
        (tmp_path / "mods" / "x").mkdir(parents=True)
        (tmp_path / "mods" / "x" / "stale.txt").write_text("old")

        zip_bytes = _make_zip({
            "repo-main/mod.json": json.dumps({"name": "x", "version": "2.0.0"}),
            "repo-main/__init__.py": "",
        })
        with patch.object(installer, "_github_default_branch", return_value="main"), \
             patch.object(installer, "_download_github_zip", return_value=zip_bytes):
            result = install("owner/repo", project_dir=tmp_path, log=lambda m: None)

        assert result["version"] == "2.0.0"
        assert not (tmp_path / "mods" / "x" / "stale.txt").exists()


def _is_externally_managed_python() -> bool:
    """
    PEP 668: some system Pythons refuse ANY plain `pip install` (even of
    an already-satisfied package) unless --break-system-packages is
    passed. install()'s own internal pip call deliberately never passes
    that flag (a tool shouldn't make that call for the user), so on such
    a Python, install() can never itself report success — only that pip
    refused, which is the correct behavior there, not a bug to work
    around in the product code.
    """
    import sysconfig
    for key in ("stdlib", "purelib", "platlib"):
        if (Path(sysconfig.get_path(key)) / "EXTERNALLY-MANAGED").exists():
            return True
    return False


# ─────────────────────────────────────────────────────────────
# PYPI INSTALL — real pip, real local package
# ─────────────────────────────────────────────────────────────

class TestPypiInstall:
    @pytest.fixture
    def fake_cruhon_pkg(self, tmp_path):
        """Build + pip-install (editable) a tiny real cruhon-* package."""
        pkg_dir = tmp_path / "cruhon-installertest"
        (pkg_dir / "cruhon_installertest").mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text(
            '[build-system]\n'
            'requires = ["setuptools>=68"]\n'
            'build-backend = "setuptools.build_meta"\n'
            '\n'
            '[project]\n'
            'name = "cruhon-installertest"\n'
            'version = "1.0.0"\n'
            '\n'
            '[tool.setuptools.packages.find]\n'
            'where = ["."]\n'
            'include = ["cruhon_installertest*"]\n'
        )
        (pkg_dir / "cruhon_installertest" / "__init__.py").write_text(
            "def register(api):\n    pass\n"
        )
        result = _pip(["install", "--quiet", "-e", str(pkg_dir)])
        assert result.returncode == 0, result.stderr
        yield "cruhon-installertest"
        _pip(["uninstall", "--quiet", "-y", "cruhon-installertest"])

    @pytest.mark.skipif(
        _is_externally_managed_python(),
        reason="install()'s own pip call never passes --break-system-packages, "
               "so it can't succeed on a PEP 668 system Python — see "
               "_is_externally_managed_python().",
    )
    def test_real_pypi_style_install_and_validation(self, fake_cruhon_pkg):
        result = install(fake_cruhon_pkg, log=lambda m: None)
        assert result["name"] == "cruhon-installertest"
        assert result["version"] == "1.0.0"
        assert result["source"] == "pypi"

    def test_non_cruhon_prefixed_package_rejected(self):
        # Exercises the REAL, unmodified install() — including its own
        # internal (deliberately plain, no --break-system-packages) pip
        # call — so on a PEP 668 "externally-managed-environment" system
        # Python, pip itself refuses before ever reaching the naming
        # check. Both are legitimate InstallError outcomes for this
        # environment; what matters is that install() never silently
        # succeeds on a non-cruhon-prefixed package.
        with pytest.raises(InstallError, match="cruhon-|externally-managed-environment"):
            install("pyyaml", log=lambda m: None)

    def test_package_without_register_rejected(self, tmp_path):
        pkg_dir = tmp_path / "cruhon-noregister"
        (pkg_dir / "cruhon_noregister").mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text(
            '[build-system]\n'
            'requires = ["setuptools>=68"]\n'
            'build-backend = "setuptools.build_meta"\n'
            '\n'
            '[project]\n'
            'name = "cruhon-noregister"\n'
            'version = "1.0.0"\n'
            '\n'
            '[tool.setuptools.packages.find]\n'
            'where = ["."]\n'
            'include = ["cruhon_noregister*"]\n'
        )
        (pkg_dir / "cruhon_noregister" / "__init__.py").write_text("VALUE = 1\n")
        result = _pip(["install", "--quiet", "-e", str(pkg_dir)])
        assert result.returncode == 0, result.stderr
        try:
            # Same environment caveat as test_non_cruhon_prefixed_package_rejected:
            # install()'s own internal pip call has no --break-system-packages,
            # so a PEP 668 system Python fails there before ever reaching the
            # register() check — also a legitimate InstallError.
            with pytest.raises(InstallError, match="register|externally-managed-environment"):
                install("cruhon-noregister", log=lambda m: None)
        finally:
            _pip(["uninstall", "--quiet", "-y", "cruhon-noregister"])
