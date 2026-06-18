# Wikipedia Fish Corpus

This repo contains a small script for the "option 2" approach: crawl Wikipedia fish-related categories through the MediaWiki API and save article text as a local corpus.

## What it does

- Starts from one or more root categories such as `Category:Fish`
- Recursively walks subcategories up to a configurable depth
- Filters out obvious noise such as `List of ...`, stubs, redirects, and disambiguation-like pages
- Downloads plaintext article extracts
- Writes:
  - `corpus.jsonl` for RAG/training pipelines
  - one `.txt` file per article for quick inspection

## Run it

```powershell
python .\wikipedia_fish_corpus.py
```

Custom categories and output path:

```powershell
python .\wikipedia_fish_corpus.py `
  --category "Category:Fish" `
  --category "Category:Freshwater fish" `
  --category "Category:Marine fish" `
  --max-depth 2 `
  --output-dir ".\data\my_fish_corpus"
```

## Output

Default output folder:

```text
data/
  wikipedia_fish_corpus/
    corpus.jsonl
    articles/
      Bluegill.txt
      Great_white_shark.txt
      ...
```

Each JSONL row looks like:

```json
{
  "title": "Bluegill",
  "pageid": 12345,
  "source_category": "Category:Freshwater fish",
  "url": "https://en.wikipedia.org/wiki/Bluegill",
  "text": "..."
}
```

## Notes

- `--max-depth 2` is a reasonable starting point. Larger values can expand quickly.
- Wikipedia categories are messy, so you may still want a second filtering pass for your exact use case.
- If you want richer biology data later, combine this corpus with FishBase, NOAA Fisheries, or Wikidata.
