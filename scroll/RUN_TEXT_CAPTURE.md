# Scroll And Copy Text

Use this when screenshots are unreliable and the page lets you select/copy text.

The script mimics:

1. `Ctrl+A`
2. `Ctrl+C`
3. append clipboard text to a running `.txt` file
4. scroll down
5. repeat

## Run

```powershell
cd C:\Users\bwbit\publicsandbox\scroll
powershell -ExecutionPolicy Bypass -File .\scroll-copy-text.ps1 -Count 30 -ScrollAmount -700 -ClearOutput
```

After pressing Enter, you have 3 seconds to click the Facebook page.

The output file is:

```text
facebook-scroll-text.txt
```

## Options

Capture 100 scroll positions:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-copy-text.ps1 -Count 100 -ScrollAmount -700 -ClearOutput
```

Use a custom output file:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-copy-text.ps1 -Count 100 -OutputFile .\roommate-posts-raw.txt -ClearOutput
```

Skip exact duplicate clipboard blocks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-copy-text.ps1 -Count 100 -DeduplicateExactBlocks -ClearOutput
```

Scroll less each time for more overlap:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-copy-text.ps1 -Count 100 -ScrollAmount -400 -ClearOutput
```

Wait longer after scrolling for lazy-loading:

```powershell
powershell -ExecutionPolicy Bypass -File .\scroll-copy-text.ps1 -Count 100 -DelaySeconds 1.5 -ClearOutput
```

## Notes

Facebook may not copy every visible post cleanly. This still often works better than screenshots because it captures actual text.

If the output only contains the browser address or a small amount of text, click inside the feed before the 3-second countdown ends and try again.

## Extract Leads From The Copied Text

After `facebook-scroll-text.txt` has content, convert it into deduped roommate leads:

```powershell
pip install -r requirements.txt
$env:OPENAI_API_KEY="your_api_key_here"
python .\extract_roommate_posts_from_text.py --input .\facebook-scroll-text.txt
```

Outputs:

```text
extracted_text\roommate_leads.csv
extracted_text\roommate_leads.json
extracted_text\all_candidate_posts.json
```
