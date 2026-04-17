$CAT_FOLDER_SCRIPT = "python cat_folder.py"
$OUTPUT_DIR = "cat_output"

if (-not (Test-Path $OUTPUT_DIR)) {
    New-Item -ItemType Directory -Path $OUTPUT_DIR | Out-Null
}

$jobs = @(
    @{
        path = "infrastructure"
        tree = $true
        ascii_tree = $true
    },
    @{
        path = "frontend"
        tree = $true
        ascii_tree = $true
        exclude_artifacts = $true
        exclude_ext = @("png")
        exclude = @("*/package-lock.json")
    },
    @{
        path = "backend-service"
        tree = $true
        ascii_tree = $true
        exclude_artifacts = $true
        exclude_dir = @("bin", "build", ".gradle", "logs")
    },
    @{
        path = "ml-service"
        tree = $true
        ascii_tree = $true
        exclude_artifacts = $true
        exclude_dir = @("data")
        prune_dir = @("logs", "tf_gpu", "venv", "plots")
    }
)

function Build-Command($job) {
    $cmd = @($env:PYTHON, $CAT_FOLDER_SCRIPT) -replace "^python ", ""
    $cmd[0] = "python"

    $cmd += $job.path

    if ($job.tree) { $cmd += "--tree" }
    if ($job.tree_only) { $cmd += "--tree-only" }
    if ($job.exclude_artifacts) { $cmd += "--exclude-artifacts" }
    if ($job.ascii_tree) { $cmd += "--ascii-tree" }

    if ($job.exclude_ext) {
        foreach ($ext in $job.exclude_ext) {
            $cmd += "--exclude-ext"
            $cmd += $ext
        }
    }

    if ($job.exclude) {
        foreach ($pattern in $job.exclude) {
            $cmd += "--exclude"
            $cmd += $pattern
        }
    }

    if ($job.exclude_dir) {
        foreach ($dir in $job.exclude_dir) {
            $cmd += "--exclude-dir"
            $cmd += $dir
        }
    }

    if ($job.prune_dir) {
        foreach ($dir in $job.prune_dir) {
            $cmd += "--prune-dir"
            $cmd += $dir
        }
    }

    if ($job.max_bytes) {
        $cmd += "--max-bytes"
        $cmd += $job.max_bytes
    }

    if ($job.header) {
        $cmd += "--header"
        $cmd += $job.header
    }

    if ($job.root) {
        $cmd += "--root"
        $cmd += $job.root
    }

    return $cmd
}

$total = $jobs.Count
$failed = @()

for ($i = 0; $i -lt $total; $i++) {
    $job = $jobs[$i]
    $path = $job.path

    Write-Host ""
    Write-Host ("=" * 80)
    Write-Host "[$($i + 1)/$total] Processing: $path"
    Write-Host ("=" * 80)
    Write-Host ""

    try {
        $cmd = Build-Command $job

        $safeName = $path -replace "[/\\]", "_"
        $outputFile = Join-Path $OUTPUT_DIR "$safeName.txt"

        $cmdStr = $cmd -join " "
        Write-Host "$ $cmdStr"
        Write-Host "-> Output: $outputFile"
        Write-Host ""

        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = ($cmd[1..($cmd.Length-1)] -join " ")
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $psi.CreateNoWindow = $true

        $process = [System.Diagnostics.Process]::Start($psi)
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()

        $stdout | Out-File -FilePath $outputFile -Encoding utf8

        if ($process.ExitCode -ne 0) {
            $failed += @{path=$path; code=$process.ExitCode}
            Write-Host "WARNING: Job failed with exit code $($process.ExitCode): $path" -ForegroundColor Yellow
            if ($stderr) {
                Write-Host "Error output:" -ForegroundColor Yellow
                Write-Host $stderr -ForegroundColor Yellow
            }
        } else {
            $sizeKB = (Get-Item $outputFile).Length / 1024
            Write-Host "Completed ($([math]::Round($sizeKB, 1)) KB written)" -ForegroundColor Green
        }

    } catch {
        Write-Host "Error processing $path : $_" -ForegroundColor Red
        $failed += @{path=$path; error=$_.Exception.Message}
    }
}

Write-Host ""
Write-Host ("=" * 80)
$successCount = $total - $failed.Count
Write-Host "SUMMARY: $successCount/$total jobs succeeded"
Write-Host ("=" * 80)
Write-Host ""
Write-Host "Output files saved in: $(Resolve-Path $OUTPUT_DIR)"

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "Failed jobs:" -ForegroundColor Red
    foreach ($f in $failed) {
        $errorMsg = if ($f.code) { $f.code } else { $f.error }
    Write-Host "  - $($f.path): $errorMsg" -ForegroundColor Red
    }
    exit 1
}

exit 0