param(
    [int]$Count = 5,
    [int]$ScrollAmount = -700,
    [double]$DelaySeconds = 0.8,
    [string]$OutputDir = ".\screenshots",
    [switch]$CaptureBeforeScroll
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

Add-Type @"
using System;
using System.Runtime.InteropServices;

public static class MouseTools {
    [DllImport("user32.dll", CharSet = CharSet.Auto, CallingConvention = CallingConvention.StdCall)]
    public static extern void mouse_event(uint dwFlags, uint dx, uint dy, int dwData, UIntPtr dwExtraInfo);
}

public static class ScreenCaptureTools {
    [DllImport("user32.dll")]
    public static extern IntPtr GetDC(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern int ReleaseDC(IntPtr hWnd, IntPtr hDC);

    [DllImport("gdi32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BitBlt(
        IntPtr hdcDest,
        int nXDest,
        int nYDest,
        int nWidth,
        int nHeight,
        IntPtr hdcSrc,
        int nXSrc,
        int nYSrc,
        int dwRop
    );
}
"@

function Invoke-MouseWheel {
    param([int]$Amount)

    $MOUSEEVENTF_WHEEL = 0x0800
    [MouseTools]::mouse_event($MOUSEEVENTF_WHEEL, 0, 0, $Amount, [UIntPtr]::Zero)
}

function Save-Screenshot {
    param(
        [string]$Path
    )

    $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $destHdc = [IntPtr]::Zero
    $sourceHdc = [IntPtr]::Zero

    try {
        $SRCCOPY = 0x00CC0020
        $destHdc = $graphics.GetHdc()
        $sourceHdc = [ScreenCaptureTools]::GetDC([IntPtr]::Zero)

        if ($sourceHdc -eq [IntPtr]::Zero) {
            throw "Could not get a screen device context."
        }

        $success = [ScreenCaptureTools]::BitBlt(
            $destHdc,
            0,
            0,
            $bounds.Width,
            $bounds.Height,
            $sourceHdc,
            $bounds.X,
            $bounds.Y,
            $SRCCOPY
        )

        if (-not $success) {
            throw "Screen capture failed. Run this from a normal interactive PowerShell window, and make sure screen capture is allowed for your terminal."
        }

        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        if ($destHdc -ne [IntPtr]::Zero) {
            $graphics.ReleaseHdc($destHdc)
        }

        if ($sourceHdc -ne [IntPtr]::Zero) {
            [ScreenCaptureTools]::ReleaseDC([IntPtr]::Zero, $sourceHdc) | Out-Null
        }

        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

if ($Count -lt 1) {
    throw "Count must be at least 1."
}

$resolvedOutputDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputDir)
New-Item -ItemType Directory -Force -Path $resolvedOutputDir | Out-Null

Write-Host "Starting in 3 seconds. Click the window you want to scroll."
Start-Sleep -Seconds 3

for ($i = 1; $i -le $Count; $i++) {
    if (-not $CaptureBeforeScroll) {
        Invoke-MouseWheel -Amount $ScrollAmount
        Start-Sleep -Seconds $DelaySeconds
    }

    $fileName = "screenshot-{0:D3}.png" -f $i
    $path = Join-Path $resolvedOutputDir $fileName
    Save-Screenshot -Path $path
    Write-Host "Saved $path"

    if ($CaptureBeforeScroll -and $i -lt $Count) {
        Invoke-MouseWheel -Amount $ScrollAmount
        Start-Sleep -Seconds $DelaySeconds
    }
}

Write-Host "Done."
