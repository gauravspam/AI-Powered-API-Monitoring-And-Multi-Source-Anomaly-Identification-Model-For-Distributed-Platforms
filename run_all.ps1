# Run all cat_folder.py commands and pipe combined output to project.txt

$SCRIPT_DIR = $PSScriptRoot
if (-not $SCRIPT_DIR) {
    $SCRIPT_DIR = Get-Location
}
$OUTPUT = Join-Path $SCRIPT_DIR "project.txt"

{
  python cat_folder.py backend-service `
    --root . `
    --max-bytes 0 `
    --tree `
    --exclude-dir .gradle `
    --exclude-dir bin `
    --exclude-dir logs `
    --exclude-artifacts

  python cat_folder.py frontend `
    --root . `
    --tree `
    --max-bytes 0 `
    --exclude-artifacts `
    --exclude-dir node_modules `
    --exclude-dir dist `
    --exclude-dir dist-ssr `
    --exclude-dir .vscode `
    --exclude-dir extra

  python cat_folder.py infrastructure `
    --root . `
    --max-bytes 0 `
    --tree

  python cat_folder.py ml-service `
    --root . `
    --tree `
    --max-bytes 0 `
    --exclude-artifacts `
    --exclude "ml-service/models" `
    --prune-dir venv

} | Out-File -FilePath $OUTPUT -Encoding utf8

Write-Host "Done. Output written to: $OUTPUT"