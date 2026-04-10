#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


class Node:
    __slots__ = ("children", "is_file", "note")

    def __init__(self) -> None:
        self.children: dict[str, Node] = {}
        self.is_file: bool = False
        self.note: str | None = None


@dataclass(frozen=True)
class FileToCat:
    fp: Path
    display_rel: PurePosixPath


DEFAULT_ARTIFACT_EXTS = {".jar", ".class", ".pyc", ".pyo", ".pth"}
DEFAULT_ARTIFACT_DIRS = {"bin"}

DEFAULT_PRUNE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "venv",
}


def norm_ext(s: str) -> str | None:
    s = s.strip()
    if not s:
        return None
    if not s.startswith("."):
        s = "." + s
    return s.lower()


def to_display_rel(p: Path, root: Path) -> PurePosixPath:
    if p.is_relative_to(root):
        return PurePosixPath(p.relative_to(root).as_posix())
    return PurePosixPath(p.as_posix())


def excluded_by_patterns(
    display_path: PurePosixPath, is_dir: bool, patterns: list[str]
) -> bool:
    if not patterns:
        return False

    s = display_path.as_posix()
    candidates = [s]
    if is_dir and not s.endswith("/"):
        candidates.append(s + "/")

    for pat in patterns:
        for c in candidates:
            if fnmatch.fnmatchcase(c, pat):
                return True
    return False


def add_node(
    tree: Node, display_path: PurePosixPath, is_file: bool, note: str | None
) -> None:
    parts = list(display_path.parts)
    if not parts:
        return

    cur = tree
    for part in parts[:-1]:
        cur = cur.children.setdefault(part, Node())

    leaf = cur.children.setdefault(parts[-1], Node())
    if is_file:
        leaf.is_file = True
    if note is not None:
        leaf.note = note


def print_tree(root_label: str, node: Node, ascii_only: bool) -> None:
    if ascii_only:
        tee, ell, pipe, space = "+-- ", "`-- ", "|   ", "    "
    else:
        tee, ell, pipe, space = "├── ", "└── ", "│   ", "    "

    sys.stdout.write(f"{root_label}\n")

    def children_sorted(n: Node):
        items = list(n.children.items())
        items.sort(key=lambda kv: (kv[1].is_file, kv[0]))  # dirs first
        return items

    def rec(n: Node, prefix: str) -> None:
        items = children_sorted(n)
        for i, (name, child) in enumerate(items):
            last = i == len(items) - 1
            connector = ell if last else tee
            label = name + (f" {child.note}" if child.note else "")
            sys.stdout.write(f"{prefix}{connector}{label}\n")
            if child.children:
                rec(child, prefix + (space if last else pipe))

    rec(node, "")


def cat_files(files: list[FileToCat], header: str, root: Path) -> int:
    for e in files:
        rel = e.fp.relative_to(root) if e.fp.is_relative_to(root) else e.fp
        sys.stdout.write(f"\n{header} {rel.as_posix()} {header}\n")
        try:
            result = subprocess.run(["cat", "--", str(e.fp)], check=False)
            if result.returncode != 0:
                return result.returncode
            sys.stdout.write("\n")
        except FileNotFoundError:
            sys.stderr.write(
                "error: `cat` not found (are you on Windows without MSYS/WSL?)\n"
            )
            return 127
        except OSError as ex:
            sys.stderr.write(f"error running cat on {e.fp}: {ex}\n")
            return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Print a combined tree for given paths; cat only non-excluded files."
    )
    ap.add_argument(
        "paths",
        nargs="+",
        help="Folders and/or files to process (relative or absolute).",
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
        help="Skip cat for files larger than this size (0 = no limit).",
    )

    # Traversal pruning (affects tree + cat).
    ap.add_argument(
        "--prune-dir",
        action="append",
        default=list(DEFAULT_PRUNE_DIRS),
        help="Directory name to NOT traverse (repeatable). Affects tree + cat.",
    )

    # Cat exclusions (do NOT remove from tree).
    ap.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name: exclude cat for any file under a dir with this name (repeatable). Still shown in tree.",
    )
    ap.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob pattern to exclude from cat (repeatable). If it matches a directory path, it excludes that subtree from cat. Still shown in tree.",
    )
    ap.add_argument(
        "--exclude-ext",
        action="append",
        default=[],
        help="File extension to exclude from cat (repeatable). Accepts 'jar' or '.jar'. Still shown in tree.",
    )
    ap.add_argument(
        "--exclude-artifacts",
        action="store_true",
        help="Preset: excludes dirs {bin} and extensions {jar,class,pyc,pyo,pth} from cat (still shown in tree).",
    )

    ap.add_argument(
        "--header",
        default="==============",
        help="Header delimiter to print around relative path.",
    )
    ap.add_argument(
        "--tree", action="store_true", help="Print the combined tree before cat output."
    )
    ap.add_argument(
        "--tree-only",
        action="store_true",
        help="Only print the tree and exit (implies --tree).",
    )
    ap.add_argument(
        "--ascii-tree",
        action="store_true",
        help="Use ASCII connectors (+--, `--) instead of Unicode.",
    )
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()

    prune_dir_names = set(args.prune_dir)

    exclude_cat_dir_names = set(args.exclude_dir)
    exclude_patterns = list(args.exclude)

    exclude_exts: set[str] = set()
    for x in args.exclude_ext:
        nx = norm_ext(x)
        if nx:
            exclude_exts.add(nx)

    if args.exclude_artifacts:
        exclude_cat_dir_names |= DEFAULT_ARTIFACT_DIRS
        exclude_exts |= DEFAULT_ARTIFACT_EXTS

    tree = Node()
    files_to_cat: list[FileToCat] = []
    seen_files: set[Path] = set()

    def dir_cat_blocked_reason(dp: Path, disp: PurePosixPath) -> str | None:
        if dp.name in exclude_cat_dir_names:
            return f"(cat-excluded dir name: {dp.name})"
        if excluded_by_patterns(disp, is_dir=True, patterns=exclude_patterns):
            return "(cat-excluded by pattern)"
        return None

    def file_cat_exclusion_reason(
        fp: Path, disp: PurePosixPath, parent_blocked: bool
    ) -> str | None:
        if parent_blocked:
            return "(cat-excluded by ancestor dir)"
        suf = fp.suffix.lower()
        if suf and suf in exclude_exts:
            return f"(cat-excluded ext {suf})"
        if excluded_by_patterns(disp, is_dir=False, patterns=exclude_patterns):
            return "(cat-excluded by pattern)"
        return None

    def handle_file(fp: Path, parent_blocked: bool) -> None:
        nonlocal files_to_cat

        if fp in seen_files:
            return
        seen_files.add(fp)

        disp = to_display_rel(fp, root)

        reason = file_cat_exclusion_reason(fp, disp, parent_blocked)
        if reason is not None:
            add_node(tree, disp, is_file=True, note=reason)
            return

        try:
            st = fp.stat()
        except OSError as e:
            add_node(tree, disp, is_file=True, note=f"(stat error: {e})")
            return

        if args.max_bytes and st.st_size > args.max_bytes:
            add_node(
                tree,
                disp,
                is_file=True,
                note=f"(cat-skipped: too large {st.st_size} bytes)",
            )
            return

        add_node(tree, disp, is_file=True, note=None)
        files_to_cat.append(FileToCat(fp=fp, display_rel=disp))

    for p in args.paths:
        base = Path(p).expanduser().resolve()
        if not base.exists():
            sys.stderr.write(f"error: path does not exist: {base}\n")
            continue

        disp_base = to_display_rel(base, root)

        if base.is_file():
            # file input: show it in tree, cat based on file rules (no parent dir context)
            handle_file(base, parent_blocked=False)
            continue

        if not base.is_dir():
            sys.stderr.write(f"error: not a regular file or directory: {base}\n")
            continue

        # per-directory "cat blocked" state, propagated to children
        blocked: dict[Path, bool] = {}
        blocked[base] = dir_cat_blocked_reason(base, disp_base) is not None

        # add the base directory node
        note = dir_cat_blocked_reason(base, disp_base)
        add_node(tree, disp_base, is_file=False, note=note)

        for dirpath, dirnames, filenames in os.walk(base, topdown=True):
            cur_dir = Path(dirpath)
            disp_cur = to_display_rel(cur_dir, root)

            # always show current dir node
            cur_note = dir_cat_blocked_reason(cur_dir, disp_cur)
            add_node(tree, disp_cur, is_file=False, note=cur_note)

            cur_blocked = blocked.get(cur_dir, False) or (cur_note is not None)

            # build child block-state + prune recursion ONLY by --prune-dir
            kept: list[str] = []
            for d in dirnames:
                dp = cur_dir / d
                disp_d = to_display_rel(dp, root)

                d_note = dir_cat_blocked_reason(dp, disp_d)
                add_node(tree, disp_d, is_file=False, note=d_note)

                blocked[dp] = cur_blocked or (d_note is not None)

                if d in prune_dir_names:
                    # show it, but don't descend
                    add_node(tree, disp_d, is_file=False, note="(pruned)")
                    continue
                kept.append(d)

            dirnames[:] = kept  # prune recursion when topdown=True [web:89]

            for name in sorted(filenames):
                fp = cur_dir / name
                # always show file node; cat depends on rules
                handle_file(fp, parent_blocked=cur_blocked)

    files_to_cat.sort(key=lambda x: x.display_rel.as_posix())

    if args.tree or args.tree_only:
        print_tree(root_label=root.as_posix(), node=tree, ascii_only=args.ascii_tree)

    if args.tree_only:
        return 0

    # cat in stable order
    return cat_files(files=files_to_cat, header=args.header, root=root)


if __name__ == "__main__":
    raise SystemExit(main())
