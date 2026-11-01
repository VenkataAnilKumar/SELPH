"""Encrypt legacy plaintext channel credentials, or re-encrypt under the current key.

Usage (from src/backend, with CREDENTIAL_ENCRYPTION_KEY set in production):
    python scripts/encrypt_credentials.py            # dry run: report only
    python scripts/encrypt_credentials.py --apply    # encrypt plaintext + re-encrypt under the primary key

Safe to re-run. After rotating keys (new key first, old key kept in the list), run with --apply,
then drop the old key from CREDENTIAL_ENCRYPTION_KEY.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.crypto import is_encrypted, reencrypt_secret  # noqa: E402
from app.database import SessionLocal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Raw SQL on purpose: bypass the ORM type so we see exactly what is stored.
        rows = db.execute(text("SELECT id, credential_value FROM channel_credentials")).fetchall()
        plaintext = sum(1 for _, value in rows if not is_encrypted(value))
        print(f"{len(rows)} credential rows, {plaintext} stored as plaintext")
        if not args.apply:
            print("Dry run; pass --apply to encrypt.")
            return 0
        for row_id, value in rows:
            db.execute(
                text("UPDATE channel_credentials SET credential_value = :v WHERE id = :i"),
                {"v": reencrypt_secret(value), "i": row_id},
            )
        db.commit()
        print(f"Encrypted {len(rows)} rows.")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
