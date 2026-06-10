"""
Archive stdlib wrappers for Cruhon — @archive.*

Covers zipfile / tarfile / gzip / shutil so a non-coder can compress,
extract, inspect and manage archives without knowing any module names.

━━━ ZIP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @archive.zip[src; dest]           — zip file/dir → dest.zip
  @archive.unzip[src; dest]         — extract zip to dest dir
  @archive.zip_list[path]           → list of file names in zip
  @archive.zip_add[zip; file]       — add a file to existing zip
  @archive.zip_read[zip; name]      → read file content from zip (str)
  @archive.zip_extract_one[zip; name; dest] — extract single file

━━━ TAR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @archive.tar[src; dest]           — tar.gz file/dir → dest.tar.gz
  @archive.untar[src; dest]         — extract tar/tar.gz to dest dir
  @archive.tar_list[path]           → list of member names in tar
  @archive.tar_extract_one[tar; name; dest] — extract single member

━━━ GZIP ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @archive.gzip[src; dest]          — compress single file with gzip
  @archive.gunzip[src; dest]        — decompress .gz file

━━━ INSPECT ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @archive.is_zip[path]             → bool
  @archive.is_tar[path]             → bool
  @archive.size[path]               → uncompressed total size (bytes, zip/tar)
"""
from ..registry import register_lib, register_lib_call

_MOD = "cruhon.core.libs.archive_"


# ── Runtime helpers ───────────────────────────────────────────────────────────

def _zip(src: str, dest: str):
    import os, zipfile
    src = str(src)
    dest = str(dest)
    if not dest.endswith(".zip"):
        dest += ".zip"
    if os.path.isdir(src):
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(src):
                for f in files:
                    fp = os.path.join(root, f)
                    zf.write(fp, os.path.relpath(fp, start=os.path.dirname(src)))
    else:
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(src, os.path.basename(src))


def _unzip(src: str, dest: str):
    import zipfile
    with zipfile.ZipFile(str(src), "r") as zf:
        zf.extractall(str(dest))


def _zip_list(path: str) -> list:
    import zipfile
    with zipfile.ZipFile(str(path), "r") as zf:
        return zf.namelist()


def _zip_add(zip_path: str, file_path: str):
    import zipfile, os
    with zipfile.ZipFile(str(zip_path), "a", zipfile.ZIP_DEFLATED) as zf:
        zf.write(str(file_path), os.path.basename(str(file_path)))


def _zip_read(zip_path: str, name: str) -> str:
    import zipfile
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        return zf.read(str(name)).decode("utf-8", errors="replace")


def _zip_extract_one(zip_path: str, name: str, dest: str):
    import zipfile
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        zf.extract(str(name), str(dest))


def _tar(src: str, dest: str):
    import os, tarfile
    src = str(src)
    dest = str(dest)
    if not (dest.endswith(".tar.gz") or dest.endswith(".tgz") or dest.endswith(".tar")):
        dest += ".tar.gz"
    mode = "w:gz" if dest.endswith(".gz") else "w"
    with tarfile.open(dest, mode) as tf:
        tf.add(src, arcname=os.path.basename(src))


def _untar(src: str, dest: str):
    import tarfile
    with tarfile.open(str(src), "r:*") as tf:
        tf.extractall(str(dest))


def _tar_list(path: str) -> list:
    import tarfile
    with tarfile.open(str(path), "r:*") as tf:
        return tf.getnames()


def _tar_extract_one(tar_path: str, name: str, dest: str):
    import tarfile
    with tarfile.open(str(tar_path), "r:*") as tf:
        tf.extract(str(name), str(dest))


def _gzip(src: str, dest: str):
    import gzip, shutil
    with open(str(src), "rb") as f_in, gzip.open(str(dest), "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def _gunzip(src: str, dest: str):
    import gzip, shutil
    with gzip.open(str(src), "rb") as f_in, open(str(dest), "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)


def _archive_size(path: str) -> int:
    import zipfile, tarfile
    path = str(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as zf:
            return sum(i.file_size for i in zf.infolist())
    try:
        with tarfile.open(path, "r:*") as tf:
            return sum(m.size for m in tf.getmembers() if m.isfile())
    except Exception:
        return -1


def _ref(fn: str) -> str:
    return f"__import__({_MOD!r}, fromlist=[{fn!r}]).{fn}"


def register():
    register_lib("archive", None)

    # ── ZIP ──────────────────────────────────────────────────────
    register_lib_call("archive", "zip",
        lambda a: f"{_ref('_zip')}({a[0]}, {a[1]})")

    register_lib_call("archive", "unzip",
        lambda a: f"{_ref('_unzip')}({a[0]}, {a[1]})")

    register_lib_call("archive", "zip_list",
        lambda a: f"{_ref('_zip_list')}({a[0]})")

    register_lib_call("archive", "zip_add",
        lambda a: f"{_ref('_zip_add')}({a[0]}, {a[1]})")

    register_lib_call("archive", "zip_read",
        lambda a: f"{_ref('_zip_read')}({a[0]}, {a[1]})")

    register_lib_call("archive", "zip_extract_one",
        lambda a: f"{_ref('_zip_extract_one')}({a[0]}, {a[1]}, {a[2]})")

    # ── TAR ──────────────────────────────────────────────────────
    register_lib_call("archive", "tar",
        lambda a: f"{_ref('_tar')}({a[0]}, {a[1]})")

    register_lib_call("archive", "untar",
        lambda a: f"{_ref('_untar')}({a[0]}, {a[1]})")

    register_lib_call("archive", "tar_list",
        lambda a: f"{_ref('_tar_list')}({a[0]})")

    register_lib_call("archive", "tar_extract_one",
        lambda a: f"{_ref('_tar_extract_one')}({a[0]}, {a[1]}, {a[2]})")

    # ── GZIP ─────────────────────────────────────────────────────
    register_lib_call("archive", "gzip",
        lambda a: f"{_ref('_gzip')}({a[0]}, {a[1]})")

    register_lib_call("archive", "gunzip",
        lambda a: f"{_ref('_gunzip')}({a[0]}, {a[1]})")

    # ── INSPECT ──────────────────────────────────────────────────
    register_lib_call("archive", "is_zip",
        lambda a: f"__import__('zipfile').is_zipfile({a[0]})")

    register_lib_call("archive", "is_tar",
        lambda a: f"__import__('tarfile').is_tarfile({a[0]})")

    register_lib_call("archive", "size",
        lambda a: f"{_ref('_archive_size')}({a[0]})")
