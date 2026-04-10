# Generate SSH key with GitHub
$keyPath = "$env:USERPROFILE\.ssh\id_ed25519"

# Check if key already exists
if (Test-Path $keyPath) {
    Write-Host "SSH key already exists at $keyPath"
} else {
    # Generate key - use -t ed25519 with empty passphrase
    $content = " 
`n" | ssh-keygen -t ed25519 -C "gauravspam@gmail.com" -N "" -f $keyPath 2>&1
    Write-Host "Key generation output: $content"
}

# Display public key
$pubKeyPath = "$keyPath.pub"
if (Test-Path $pubKeyPath) {
    Write-Host "`n=== Public Key (add to GitHub) ==="
    Get-Content $pubKeyPath
}