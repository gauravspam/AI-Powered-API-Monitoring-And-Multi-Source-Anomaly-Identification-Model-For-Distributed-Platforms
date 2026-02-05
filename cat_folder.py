#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run `cat` on each file under a folder and print its relative path."
    )
    ap.add_argument("folder", help="Folder to traverse (relative or absolute).")
    ap.add_argument(
        "--root",
        default=".",
        help="Root used to compute relative paths (usually repo root).",
    )
    ap.add_argument(
        "--max-bytes",
        type=int,
        default=1_000_000,
        help="Skip files larger than this size (0 = no limit).",
    )
    ap.add_argument(
        "--exclude-dir",
        action="append",
        default=[".git", "node_modules", "__pycache__", "build", "dist", ".venv", "venv"],
        help="Directory name to skip entirely (repeatable).",
    )
    ap.add_argument(
        "--header",
        default="=====",
        help="Header delimiter to print around relative path.",
    )
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    base = Path(args.folder).expanduser().resolve()

    if not base.exists() or not base.is_dir():
        sys.stderr.write(f"error: not a directory: {base}\n")
        return 2

    exclude_dir_names = set(args.exclude_dir)

    for dirpath, dirnames, filenames in os.walk(base):
        # prune directories in-place for performance (prevents descending) [web:1]
        dirnames[:] = [d for d in dirnames if d not in exclude_dir_names]  # [web:1]

        cur_dir = Path(dirpath)

        for name in sorted(filenames):
            fp = (cur_dir / name)

            try:
                st = fp.stat()
            except OSError as e:
                sys.stderr.write(f"error stat {fp}: {e}\n")
                continue

            if args.max_bytes and st.st_size > args.max_bytes:
                rel = fp.relative_to(root) if fp.is_relative_to(root) else fp
                sys.stderr.write(f"skip (too large {st.st_size} bytes): {rel}\n")
                continue

            rel = fp.relative_to(root) if fp.is_relative_to(root) else fp

            # header with relative path
            sys.stdout.write(f"\n{args.header} {rel.as_posix()} {args.header}\n")

            # run `cat file` and stream output directly to our stdout [web:32]
            try:
                subprocess.run(["cat", str(fp)], check=False)  # [web:32]
            except FileNotFoundError:
                sys.stderr.write("error: `cat` not found (are you on Windows without MSYS/WSL?)\n")
                return 127
            except OSError as e:
                sys.stderr.write(f"error running cat on {fp}: {e}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
