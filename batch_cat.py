#!/usr/bin/env python3
"""
Batch runner for cat_folder.py commands.
Edit the JOBS list below to configure which folders to process and with what options.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

# ============================================================================
# CONFIGURATION - Edit this section to change your commands
# ============================================================================

# Path to your cat_folder.py script (adjust if needed)
CAT_FOLDER_SCRIPT = "./cat_folder.py"

# List of jobs to run. Each job is a dict with:
#   - "path": folder or file to process (required)
#   - "tree": True to show tree (default: False)
#   - "tree_only": True to skip cat (default: False)
#   - "exclude_artifacts": True to exclude jar/class/pyc/pth (default: False)
#   - "exclude_ext": list of extensions to exclude (e.g., ["png", "svg"])
#   - "exclude": list of glob patterns to exclude from cat
#   - "exclude_dir": list of directory names to exclude from cat
#   - "prune_dir": list of directory names to prune from tree+cat
#   - "max_bytes": skip files larger than this (default: 1000000)
#   - "ascii_tree": True to use ASCII tree connectors (default: False)
#   - "header": custom header delimiter (default: "=====")
JOBS = [
    {
        "path": "infrastructure",
        "tree": True,
    },
    {
        "path": "frontend",
        "tree": True,
        "exclude_artifacts": True,
        "exclude_ext": ["png"],
        "exclude": ["*/package-lock.json"],
    },
    {
        "path": "backend-service",
        "tree": True,
        "exclude_artifacts": True,
        "exclude_dir": ["bin", "build", ".gradle", "logs"],
    },
    {
        "path": "ml-service",
        "tree": True,
        "exclude_artifacts": True,
        "exclude_dir": ["data"],
        "prune_dir": ["logs", "tf_gpu", "venv", "plots"],
    },
]

# ============================================================================
# EXECUTION LOGIC - No need to edit below unless you want to customize behavior
# ============================================================================


def build_command(job: dict[str, Any]) -> list[str]:
    """Build subprocess command from job config."""
    cmd = [sys.executable, CAT_FOLDER_SCRIPT]

    # Positional argument: path
    if "path" not in job:
        raise ValueError("Job missing required 'path' key")
    cmd.append(job["path"])

    # Optional flags
    if job.get("tree"):
        cmd.append("--tree")

    if job.get("tree_only"):
        cmd.append("--tree-only")

    if job.get("exclude_artifacts"):
        cmd.append("--exclude-artifacts")

    if job.get("ascii_tree"):
        cmd.append("--ascii-tree")

    # Repeatable options
    for ext in job.get("exclude_ext", []):
        cmd.extend(["--exclude-ext", ext])

    for pattern in job.get("exclude", []):
        cmd.extend(["--exclude", pattern])

    for dirname in job.get("exclude_dir", []):
        cmd.extend(["--exclude-dir", dirname])

    for dirname in job.get("prune_dir", []):
        cmd.extend(["--prune-dir", dirname])

    # Single-value options
    if "max_bytes" in job:
        cmd.extend(["--max-bytes", str(job["max_bytes"])])

    if "header" in job:
        cmd.extend(["--header", job["header"]])

    if "root" in job:
        cmd.extend(["--root", job["root"]])

    return cmd


def main() -> int:
    script_path = Path(CAT_FOLDER_SCRIPT)
    if not script_path.exists():
        sys.stderr.write(f"Error: cat_folder.py not found at {script_path.resolve()}\n")
        sys.stderr.write(f"Update CAT_FOLDER_SCRIPT in {__file__}\n")
        return 1

    # Create output directory
    output_dir = Path("cat_output")
    output_dir.mkdir(exist_ok=True)

    total = len(JOBS)
    failed = []

    for i, job in enumerate(JOBS, start=1):
        path = job.get("path", "unknown")
        print(f"\n{'=' * 80}")
        print(f"[{i}/{total}] Processing: {path}")
        print(f"{'=' * 80}\n")

        try:
            cmd = build_command(job)

            # Generate output filename
            safe_name = path.replace("/", "_").replace("\\", "_")
            output_file = output_dir / f"{safe_name}.txt"

            # Show the command being run
            cmd_str = " ".join(cmd)
            print(f"$ {cmd_str}")
            print(f"→ Output: {output_file}\n")

            # Run and redirect to file
            with open(output_file, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    cmd, stdout=f, stderr=subprocess.PIPE, text=True
                )

            if result.returncode != 0:
                failed.append((path, result.returncode))
                sys.stderr.write(
                    f"⚠️  Job failed with exit code {result.returncode}: {path}\n"
                )
                if result.stderr:
                    sys.stderr.write(f"Error output:\n{result.stderr}\n")
            else:
                # Show file size
                size_kb = output_file.stat().st_size / 1024
                print(f"✓ Completed ({size_kb:.1f} KB written)")

        except KeyboardInterrupt:
            sys.stderr.write("\n\n⚠️  Interrupted by user\n")
            return 130

        except Exception as e:
            sys.stderr.write(f"\n⚠️  Error processing {path}: {e}\n")
            failed.append((path, str(e)))

    # Summary
    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {total - len(failed)}/{total} jobs succeeded")
    print(f"{'=' * 80}")
    print(f"\nOutput files saved in: {output_dir.resolve()}")

    if failed:
        print("\nFailed jobs:")
        for path, code in failed:
            print(f"  - {path}: {code}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
