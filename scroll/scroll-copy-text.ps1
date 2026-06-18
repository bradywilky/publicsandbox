param(
    [int]$Count = 20,
    [int]$ScrollAmount = -700,
    [double]$DelaySeconds = 0.8,
    [double]$CopyDelaySeconds = 0.4,
    [string]$OutputFile = ".\facebook-scroll-text.txt",
    [switch]$ClearOutput,
    [switch]$DeduplicateExactBlocks
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms

Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class MouseTools {
    [DllImport("user32.dll", CharSet = CharSet.Auto, CallingConvention = CallingConvention.StdCall)]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, int dwData, UIntPtr dwExtraInfo);
}
"@

function Invoke-MouseWheel {
    param([int]$Amount)

    $MOUSEEVENTF_WHEEL = 0x0800
    [MouseTools]::mouse_event($MOUSEEVENTF_WHEEL, 0, 0, $Amount, [UIntPtr]::Zero)
}

function Send-CopyAll {
    [System.Windows.Forms.SendKeys]::SendWait("^a")
    Start-Sleep -Milliseconds 150
    [System.Windows.Forms.SendKeys]::SendWait("^c")
}

function Get-ClipboardText {
    try {
        return [System.Windows.Forms.Clipboard]::GetText()
    }
    catch {
        Start-Sleep -Milliseconds 250
        return [System.Windows.Forms.Clipboard]::GetText()
    }
}

function Get-TextHash {
    param([string]$Text)

    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text.Trim())
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return [Convert]::ToBase64String($sha.ComputeHash($bytes))
    }
    finally {
        $sha.Dispose()
    }
}

if ($Count -lt 1) {
    throw "Count must be at least 1."
}

$resolvedOutputFile = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputFile)
$outputDir = Split-Path -Parent $resolvedOutputFile
if ($outputDir) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}

if ($ClearOutput -and (Test-Path -LiteralPath $resolvedOutputFile)) {
    Clear-Content -LiteralPath $resolvedOutputFile
}

$seen = New-Object 'System.Collections.Generic.HashSet[string]'

Write-Host "Starting in 3 seconds. Click the Facebook page or browser tab you want copied."
Write-Host "Tip: make sure the feed itself is focused, not the address bar or a search box."
Start-Sleep -Seconds 3

for ($i = 1; $i -le $Count; $i++) {
    [System.Windows.Forms.Clipboard]::Clear()
    Send-CopyAll
    Start-Sleep -Seconds $CopyDelaySeconds

    $text = Get-ClipboardText
    $trimmed = $text.Trim()

    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        Write-Host ("[{0}/{1}] Clipboard was empty; nothing appended." -f $i, $Count)
    }
    else {
        $hash = Get-TextHash -Text $trimmed

        if ($DeduplicateExactBlocks -and $seen.Contains($hash)) {
            Write-Host ("[{0}/{1}] Same text block as an earlier capture; skipped." -f $i, $Count)
        }
        else {
            $seen.Add($hash) | Out-Null
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            $header = @"

================================================================================
CAPTURE $("{0:D3}" -f $i) | $timestamp | ScrollAmount=$ScrollAmount
================================================================================

"@
            Add-Content -LiteralPath $resolvedOutputFile -Value $header -Encoding UTF8
            Add-Content -LiteralPath $resolvedOutputFile -Value $trimmed -Encoding UTF8
            Add-Content -LiteralPath $resolvedOutputFile -Value "" -Encoding UTF8

            $lineCount = ($trimmed -split "`r?`n").Count
            Write-Host ("[{0}/{1}] Appended {2} lines to {3}" -f $i, $Count, $lineCount, $resolvedOutputFile)
        }
    }

    if ($i -lt $Count) {
        Invoke-MouseWheel -Amount $ScrollAmount
        Start-Sleep -Seconds $DelaySeconds
    }
}

Write-Host "Done."
