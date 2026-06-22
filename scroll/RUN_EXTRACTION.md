# Extract Roommate Posts From Screenshots

This workflow is for screenshots of overlapping Facebook roommate-finder posts.

The script:

1. Reads images from `screenshots`.
2. Skips blank/failed captures.
3. Sends each readable screenshot to OpenAI as an image input.
4. Extracts roommate post details as structured JSON.
5. Merges likely duplicate posts caused by overlapping scroll screenshots.
6. Writes a CSV you can sort/filter.

## Setup

```powershell
cd C:\Users\bwbit\publicsandbox\scroll
pip install -r requirements.txt
$env:OPENAI_API_KEY="your_api_key_here"
```

## Run

```powershell
python .\extract_roommate_posts.py
```

Outputs:

```text
extracted\roommate_leads.csv
extracted\roommate_leads.json
extracted\screenshots.jsonl
extracted\raw\screenshot-001.json
```

## First Test

Before spending API credits on all screenshots, test a few:

```powershell
python .\extract_roommate_posts.py --limit 5
```

If that looks good, run all 100:

```powershell
python .\extract_roommate_posts.py --force
```

## Useful Options

Use a different model:

```powershell
python .\extract_roommate_posts.py --model gpt-4.1-mini
```

Make duplicate merging stricter:

```powershell
python .\extract_roommate_posts.py --dedupe-threshold 0.82
```

Make duplicate merging looser:

```powershell
python .\extract_roommate_posts.py --dedupe-threshold 0.62
```

Force processing blank-looking screenshots anyway:

```powershell
python .\extract_roommate_posts.py --include-blank
```

## Important

The current `screenshots` folder appears to contain black images, which usually means the capture step failed or the target window was protected/minimized/not visible. Open one screenshot before running the extractor. If it is black, recapture first.
