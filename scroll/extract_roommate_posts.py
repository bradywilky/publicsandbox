import argparse
import base64
import csv
import hashlib
import json
import mimetypes
import os
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

from openai import OpenAI
from PIL import Image, ImageStat


DEFAULT_MODEL = "gpt-4.1-mini"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["screenshot_file", "screen_status", "posts"],
    "properties": {
        "screenshot_file": {"type": "string"},
        "screen_status": {
            "type": "string",
            "enum": ["readable", "blank_or_unreadable", "not_facebook_posts"],
        },
        "posts": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "author_name",
                    "post_kind",
                    "post_text",
                    "location",
                    "price_or_budget",
                    "availability_or_move_in",
                    "room_type",
                    "contact_info",
                    "date_or_time_posted",
                    "constraints_or_preferences",
                    "engagement",
                    "visible_top_cut_off",
                    "visible_bottom_cut_off",
                    "confidence",
                ],
                "properties": {
                    "author_name": {"type": ["string", "null"]},
                    "post_kind": {
                        "type": "string",
                        "enum": [
                            "offering_room",
                            "looking_for_room",
                            "looking_for_roommate",
                            "sublet",
                            "other",
                            "unknown",
                        ],
                    },
                    "post_text": {"type": "string"},
                    "location": {"type": ["string", "null"]},
                    "price_or_budget": {"type": ["string", "null"]},
                    "availability_or_move_in": {"type": ["string", "null"]},
                    "room_type": {"type": ["string", "null"]},
                    "contact_info": {"type": ["string", "null"]},
                    "date_or_time_posted": {"type": ["string", "null"]},
                    "constraints_or_preferences": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "engagement": {"type": ["string", "null"]},
                    "visible_top_cut_off": {"type": "boolean"},
                    "visible_bottom_cut_off": {"type": "boolean"},
                    "confidence": {"type": "number"},
                },
            },
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract and deduplicate roommate-finder Facebook posts from screenshots."
    )
    parser.add_argument("--input", default="screenshots", help="Folder containing screenshots.")
    parser.add_argument("--output", default="extracted", help="Folder for JSONL/CSV outputs.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI vision-capable model.")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N screenshots.")
    parser.add_argument("--force", action="store_true", help="Reprocess screenshots with cached JSON.")
    parser.add_argument(
        "--dedupe-threshold",
        type=float,
        default=0.72,
        help="Similarity threshold for merging overlapping posts.",
    )
    parser.add_argument(
        "--include-blank",
        action="store_true",
        help="Send blank-looking screenshots to OpenAI anyway.",
    )
    return parser.parse_args()


def image_paths(input_dir: Path, limit: int | None) -> list[Path]:
    paths = sorted(p for p in input_dir.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    return paths[:limit] if limit else paths


def is_probably_blank(path: Path) -> bool:
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        mean = sum(stat.mean) / 3
        variance = sum(stat.var) / 3
        return mean < 4 and variance < 4


def data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def extract_screenshot(client: OpenAI, model: str, path: Path) -> dict:
    prompt = f"""
You are extracting roommate-finder leads from a screenshot of a Facebook group feed.

Screenshot filename: {path.name}

Extract every visible roommate, housing, sublet, room available, or room wanted post.
Screenshots may overlap with neighboring screenshots. Some posts may be cut off at the
top or bottom. Preserve exact wording where possible, especially price, neighborhood,
move-in date, lease length, roommates, pets, gender preferences, and contact instructions.

Ignore unrelated Facebook navigation, comments unless they contain contact/details, ads,
sidebars, reaction labels, and browser UI.
"""

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url(path)},
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "roommate_post_extraction",
                "strict": True,
                "schema": EXTRACTION_SCHEMA,
            }
        },
    )

    return json.loads(response.output_text)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower()
    value = re.sub(r"https?://\S+", "", value)
    value = re.sub(r"[^a-z0-9$@.+#\s-]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def post_fingerprint(post: dict) -> str:
    parts = [
        post.get("author_name") or "",
        post.get("location") or "",
        post.get("price_or_budget") or "",
        post.get("post_text") or "",
    ]
    normalized = normalize_text(" ".join(parts))
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:12]


def post_similarity(left: dict, right: dict) -> float:
    left_author = normalize_text(left.get("author_name"))
    right_author = normalize_text(right.get("author_name"))
    left_text = normalize_text(left.get("post_text"))
    right_text = normalize_text(right.get("post_text"))

    text_score = SequenceMatcher(None, left_text, right_text).ratio()
    author_score = 1.0 if left_author and left_author == right_author else 0.0

    price_match = bool(
        normalize_text(left.get("price_or_budget"))
        and normalize_text(left.get("price_or_budget")) == normalize_text(right.get("price_or_budget"))
    )
    location_match = bool(
        normalize_text(left.get("location"))
        and normalize_text(left.get("location")) == normalize_text(right.get("location"))
    )

    return max(text_score, (text_score * 0.72) + (author_score * 0.18) + (price_match * 0.05) + (location_match * 0.05))


def better_value(current, candidate):
    if current in (None, "", []):
        return candidate
    if candidate in (None, "", []):
        return current
    if isinstance(current, str) and isinstance(candidate, str):
        return candidate if len(candidate) > len(current) else current
    if isinstance(current, list) and isinstance(candidate, list):
        merged = []
        for item in current + candidate:
            if item and item not in merged:
                merged.append(item)
        return merged
    return current


def merge_posts(cluster: dict, post: dict, source_file: str) -> None:
    cluster["source_files"].append(source_file)
    cluster["fingerprints"].append(post_fingerprint(post))
    cluster["visible_top_cut_off"] = cluster["visible_top_cut_off"] and post.get("visible_top_cut_off", False)
    cluster["visible_bottom_cut_off"] = cluster["visible_bottom_cut_off"] and post.get("visible_bottom_cut_off", False)
    cluster["confidence"] = max(cluster["confidence"], post.get("confidence", 0))

    for key in [
        "author_name",
        "post_kind",
        "post_text",
        "location",
        "price_or_budget",
        "availability_or_move_in",
        "room_type",
        "contact_info",
        "date_or_time_posted",
        "constraints_or_preferences",
        "engagement",
    ]:
        cluster[key] = better_value(cluster.get(key), post.get(key))


def dedupe_posts(extractions: list[dict], threshold: float) -> list[dict]:
    clusters: list[dict] = []

    for extraction in extractions:
        source_file = extraction.get("screenshot_file", "")
        for post in extraction.get("posts", []):
            if not normalize_text(post.get("post_text")):
                continue

            best_index = None
            best_score = 0.0
            for index, cluster in enumerate(clusters):
                score = post_similarity(cluster, post)
                if score > best_score:
                    best_index = index
                    best_score = score

            if best_index is not None and best_score >= threshold:
                merge_posts(clusters[best_index], post, source_file)
            else:
                cluster = dict(post)
                cluster["lead_id"] = f"lead-{len(clusters) + 1:04d}"
                cluster["source_files"] = [source_file]
                cluster["fingerprints"] = [post_fingerprint(post)]
                clusters.append(cluster)

    return clusters


def write_csv(path: Path, leads: list[dict]) -> None:
    fields = [
        "lead_id",
        "author_name",
        "post_kind",
        "location",
        "price_or_budget",
        "availability_or_move_in",
        "room_type",
        "contact_info",
        "date_or_time_posted",
        "constraints_or_preferences",
        "engagement",
        "confidence",
        "visible_top_cut_off",
        "visible_bottom_cut_off",
        "source_files",
        "post_text",
    ]

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for lead in leads:
            row = {field: lead.get(field) for field in fields}
            row["constraints_or_preferences"] = "; ".join(lead.get("constraints_or_preferences") or [])
            row["source_files"] = "; ".join(lead.get("source_files") or [])
            writer.writerow(row)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    raw_dir = output_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    paths = image_paths(input_dir, args.limit)
    if not paths:
        print(f"No screenshots found in {input_dir}", file=sys.stderr)
        return 1

    client = None
    extractions: list[dict] = []

    for index, path in enumerate(paths, start=1):
        cache_path = raw_dir / f"{path.stem}.json"
        print(f"[{index}/{len(paths)}] {path.name}")

        if cache_path.exists() and not args.force:
            extractions.append(json.loads(cache_path.read_text(encoding="utf-8")))
            print("  cached")
            continue

        if is_probably_blank(path) and not args.include_blank:
            extraction = {
                "screenshot_file": path.name,
                "screen_status": "blank_or_unreadable",
                "posts": [],
            }
            cache_path.write_text(json.dumps(extraction, indent=2), encoding="utf-8")
            extractions.append(extraction)
            print("  skipped blank-looking image")
            continue

        if not os.environ.get("OPENAI_API_KEY"):
            print("Missing OPENAI_API_KEY. Set it before processing readable screenshots.", file=sys.stderr)
            return 2

        if client is None:
            client = OpenAI()

        try:
            extraction = extract_screenshot(client, args.model, path)
            extraction["screenshot_file"] = path.name
            cache_path.write_text(json.dumps(extraction, indent=2, ensure_ascii=False), encoding="utf-8")
            extractions.append(extraction)
            print(f"  extracted {len(extraction.get('posts', []))} posts")
            time.sleep(0.2)
        except Exception as exc:
            error = {
                "screenshot_file": path.name,
                "screen_status": "blank_or_unreadable",
                "posts": [],
                "error": str(exc),
            }
            cache_path.write_text(json.dumps(error, indent=2), encoding="utf-8")
            extractions.append(error)
            print(f"  error: {exc}")

    all_jsonl = output_dir / "screenshots.jsonl"
    with all_jsonl.open("w", encoding="utf-8") as handle:
        for extraction in extractions:
            handle.write(json.dumps(extraction, ensure_ascii=False) + "\n")

    leads = dedupe_posts(extractions, args.dedupe_threshold)
    leads_json = output_dir / "roommate_leads.json"
    leads_csv = output_dir / "roommate_leads.csv"
    leads_json.write_text(json.dumps(leads, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(leads_csv, leads)

    skipped = sum(1 for item in extractions if item.get("screen_status") == "blank_or_unreadable")
    print()
    print(f"Processed screenshots: {len(extractions)}")
    print(f"Skipped blank/unreadable: {skipped}")
    print(f"Deduped leads: {len(leads)}")
    print(f"Wrote: {leads_csv}")
    print(f"Wrote: {leads_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
