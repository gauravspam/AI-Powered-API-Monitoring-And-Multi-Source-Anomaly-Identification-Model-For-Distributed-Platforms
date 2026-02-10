#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def iter_files_in_dir(base: Path, exclude_dir_names: set[str]) -> list[Path]:
    for dirpath, dirnames, filenames in os.walk(base):
        # prune directories in-place to avoid descending into excluded ones [web:1]
        dirnames[:] = [d for d in dirnames if d not in exclude_dir_names]  # [web:1]

        cur_dir = Path(dirpath)
        for name in sorted(filenames):
            yield cur_dir / name


def process_path(
    path: Path,
    root: Path,
    max_bytes: int,
    header: str,
    exclude_dir_names: set[str],
) -> None:
    if path.is_dir():
        it = iter_files_in_dir(path, exclude_dir_names)
    else:
        it = [path]

    for fp in it:
        try:
            st = fp.stat()
        except OSError as e:
            sys.stderr.write(f"error stat {fp}: {e}\n")
            continue

        if max_bytes and st.st_size > max_bytes:
            rel = fp.relative_to(root) if fp.is_relative_to(root) else fp
            sys.stderr.write(f"skip (too large {st.st_size} bytes): {rel}\n")
            continue

        rel = fp.relative_to(root) if fp.is_relative_to(root) else fp

        # header with relative path
        sys.stdout.write(f"\n{header} {rel.as_posix()} {header}\n")

        # run `cat file` and stream output directly to stdout [web:2]
        try:
            subprocess.run(["cat", str(fp)], check=False)  # [web:2]
        except FileNotFoundError:
            sys.stderr.write(
                "error: `cat` not found (are you on Windows without MSYS/WSL?)\n"
            )
            raise SystemExit(127)
        except OSError as e:
            sys.stderr.write(f"error running cat on {fp}: {e}\n")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run `cat` on each file under given folders and/or individual files and print their relative paths."
    )
    ap.add_argument(
        "paths",
        nargs="+",
        help="Folders and/or files to process (relative or absolute).",  # [web:5]
    )
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
    exclude_dir_names = set(args.exclude_dir)

    for p in args.paths:
        base = Path(p).expanduser().resolve()

        if not base.exists():
            sys.stderr.write(f"error: path does not exist: {base}\n")
            continue

        # both files and dirs are allowed; only reject non-file, non-dir
        if not (base.is_dir() or base.is_file()):
            sys.stderr.write(f"error: not a regular file or directory: {base}\n")
            continue

        process_path(
            base,
            root=root,
            max_bytes=args.max_bytes,
            header=args.header,
            exclude_dir_names=exclude_dir_names,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
