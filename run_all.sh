#!/usr/bin/env bash
# Run all cat_folder.py commands and pipe combined output to project.txt

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$SCRIPT_DIR/project.txt"

{
  python3 cat_folder.py backend-service \
    --root . \
    --max-bytes 0 \
    --tree \
    --exclude-dir .gradle \
    --exclude-dir bin \
    --exclude-dir logs \
    --exclude-artifacts

  python3 cat_folder.py frontend \
    --root . \
    --tree \
    --max-bytes 0 \
    --exclude-artifacts \
    --exclude-dir node_modules \
    --exclude-dir dist \
    --exclude-dir dist-ssr \
    --exclude-dir .vscode \
    --exclude-dir extra

  python3 cat_folder.py infrastructure \
    --root . \
    --max-bytes 0 \
    --tree

  python3 cat_folder.py ml-service \
    --root . \
    --tree \
    --max-bytes 0 \
    --exclude-artifacts \
    --exclude "ml-service/models" \
    --prune-dir venv

} > "$OUTPUT"

echo "Done. Output written to: $OUTPUT"
