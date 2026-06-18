# Scroll Screenshot Runner

This folder contains a Windows PowerShell script that scrolls the currently active window, takes a screenshot, and repeats a fixed number of times.

## Run

Open PowerShell in this folder, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-shot.ps1 -Count 10 -ScrollAmount -700 -DelaySeconds 0.8
```

After you press Enter, you have 3 seconds to click the browser, app, or document you want captured.

Screenshots are saved to `.\screenshots` by default:

```text
screenshots\screenshot-001.png
screenshots\screenshot-002.png
screenshots\screenshot-003.png
```

## Options

```powershell
-Count 10
```

How many screenshots to take.

```powershell
-ScrollAmount -700
```

How far to scroll each time. Negative values scroll down. Positive values scroll up.

```powershell
-DelaySeconds 0.8
```

How long to wait after each scroll before taking the screenshot.

```powershell
-OutputDir ".\captures"
```

Where to save the PNG files.

```powershell
-CaptureBeforeScroll
```

Take the first screenshot before scrolling. Without this flag, the script scrolls first, then captures.

## Examples

Capture the current view first, then scroll down and capture 7 more:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-shot.ps1 -Count 8 -ScrollAmount -650 -CaptureBeforeScroll
```

Scroll more slowly for pages that lazy-load images:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-shot.ps1 -Count 12 -ScrollAmount -500 -DelaySeconds 1.5
```
