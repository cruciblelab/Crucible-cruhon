#!/usr/bin/env python3
"""
One-time migration: encrypt existing plaintext data in place.

Safe to run multiple times — rows already carrying the "enc:v1:" prefix are
skipped, so it never double-encrypts. Run after enabling encryption:

    cd /opt/support-tawk
    venv/bin/python migrate_encrypt.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from server.database import database          # noqa: E402
from server.crypto import encrypt, is_encrypted  # noqa: E402

# (table, primary_key_column, [columns_to_encrypt])
TARGETS = [
    ("conversations",    "id", ["visitor_name", "visitor_email"]),
    ("messages",         "id", ["content"]),
    ("notes",            "id", ["content"]),
    ("offline_messages", "id", ["visitor_name", "visitor_email", "message"]),
    ("ratings",          "id", ["comment"]),
]


def migrate():
    total = 0
    database.connect(reuse_if_open=True)
    with database.atomic():
        for table, pk, columns in TARGETS:
            for col in columns:
                try:
                    rows = database.execute_sql(
                        f"SELECT {pk}, {col} FROM {table}"
                    ).fetchall()
                except Exception as e:
                    print(f"  skip {table}.{col}: {e}")
                    continue
                changed = 0
                for row_id, value in rows:
                    if value in (None, "") or is_encrypted(value):
                        continue
                    enc = encrypt(value)
                    database.execute_sql(
                        f"UPDATE {table} SET {col} = ? WHERE {pk} = ?",
                        (enc, row_id),
                    )
                    changed += 1
                if changed:
                    print(f"  {table}.{col}: encrypted {changed} row(s)")
                total += changed
    print(f"\nDone. {total} value(s) encrypted." if total else "\nNothing to migrate — all data already encrypted.")


if __name__ == "__main__":
    migrate()
