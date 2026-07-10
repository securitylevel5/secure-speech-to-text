#!/usr/bin/env python3
import argparse
import os
import secrets
from pathlib import Path

CHUNK = 1024 * 1024  # 1 MiB

def best_effort_delete_ssd(file_path: str) -> None:
    """
    Best-effort secure deletion for SSDs on Windows (and other OSes).
    WARNING: Due to SSD wear leveling, TRIM, and filesystem metadata,
    this cannot guarantee complete erasure.
    """
    p = Path(file_path)

    if not p.exists():
        raise FileNotFoundError(f"{p} not found")

    if p.is_dir():
        raise IsADirectoryError(f"{p} is a directory (only files are supported)")

    # Remove read-only attribute if set
    try:
        os.chmod(p, 0o666)
    except Exception:
        pass  # don't block deletion if chmod fails

    size = p.stat().st_size

    # Overwrite logical file contents in chunks
    if size > 0:
        with open(p, "r+b", buffering=0) as f:
            remaining = size
            while remaining > 0:
                n = min(CHUNK, remaining)
                f.write(secrets.token_bytes(n))
                remaining -= n
            f.flush()
            os.fsync(f.fileno())

    # Rename to a random name to obscure filename remnants in dir listings
    rand_name = p.parent / secrets.token_hex(16)
    os.replace(p, rand_name)

    # Delete the file
    rand_name.unlink(missing_ok=False)

    print("Deleted (best-effort). Note: SSD wear-leveling, metadata and shadow copies may retain data.")

def main():
    parser = argparse.ArgumentParser(
        description="Best-effort file shredder (cannot guarantee secure deletion)."
    )
    parser.add_argument("path", help="Path to the file to delete")
    args = parser.parse_args()
    best_effort_delete_ssd(args.path)

if __name__ == "__main__":
    main()
