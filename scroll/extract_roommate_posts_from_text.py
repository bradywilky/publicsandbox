import argparse
import csv
import json
import os
import re
import sys
import time
from difflib import SequenceMatcher
from pathlib import Path

from openai import OpenAI


DEFAULT_MODEL = "gpt-4.1-mini"


TEXT_EXTRACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["posts"],
    "properties": {
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
                    "confidence": {"type": "number"},
                },
            },
        }
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract roommate leads from copied Facebook feed text.")
    parser.add_argument("--input", default="facebook-scroll-text.txt", help="Raw copied text file.")
    parser.add_argument("--output", default="extracted_text", help="Output folder.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI model.")
    parser.add_argument("--chunk-chars", type=int, default=14000, help="Approximate input chars per API call.")
    parser.add_argument("--dedupe-threshold", type=float, default=0.78, help="Similarity threshold for merging posts.")
    return parser.parse_args()


def split_capture_blocks(text: str) -> list[str]:
    blocks = re.split(r"\n=+\nCAPTURE \d+ .+?\n=+\n", text)
    return [block.strip() for block in blocks if block.strip()]


def make_chunks(blocks: list[str], chunk_chars: int) -> list[str]:
    chunks = []
    current = []
    current_len = 0

    for block in blocks:
        block_len = len(block)
        if current and current_len + block_len > chunk_chars:
            chunks.append("\n\n--- NEXT COPIED SCROLL BLOCK ---\n\n".join(current))
            current = []
            current_len = 0

        current.append(block)
        current_len += block_len

    if current:
        chunks.append("\n\n--- NEXT COPIED SCROLL BLOCK ---\n\n".join(current))

    return chunks


def extract_chunk(client: OpenAI, model: str, chunk: str, index: int, total: int) -> dict:
    prompt = f"""
The text below was copied from overlapping scroll positions in a Facebook roommate finder group.
Extract only roommate/housing/sublet posts or comments that contain useful housing lead details.

Chunk {index} of {total}.

Rules:
- Ignore Facebook navigation, buttons, reaction labels, repeated UI text, and unrelated chatter.
- Reconstruct posts as best as possible from copied feed text.
- Preserve exact wording in post_text where possible.
- Include prices, neighborhoods, move-in dates, lease length, pet rules, gender preferences, and contact instructions.
- If text is duplicated across scroll positions, still extract the candidate posts; another step will deduplicate.
- Use null when a field is unknown.

Copied text:
{chunk}
"""

    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": prompt}],
        text={
            "format": {
                "type": "json_schema",
                "name": "roommate_posts_from_text",
                "strict": True,
                "schema": TEXT_EXTRACTION_SCHEMA,
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


def similarity(left: dict, right: dict) -> float:
    text_score = SequenceMatcher(None, normalize_text(left.get("post_text")), normalize_text(right.get("post_text"))).ratio()
    author_match = bool(
        normalize_text(left.get("author_name"))
        and normalize_text(left.get("author_name")) == normalize_text(right.get("author_name"))
    )
    price_match = bool(
        normalize_text(left.get("price_or_budget"))
        and normalize_text(left.get("price_or_budget")) == normalize_text(right.get("price_or_budget"))
    )
    return max(text_score, (text_score * 0.80) + (author_match * 0.15) + (price_match * 0.05))


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


def dedupe(posts: list[dict], threshold: float) -> list[dict]:
    leads = []
    for post in posts:
        if not normalize_text(post.get("post_text")):
            continue

        best_index = None
        best_score = 0.0
        for index, lead in enumerate(leads):
            score = similarity(lead, post)
            if score > best_score:
                best_index = index
                best_score = score

        if best_index is None or best_score < threshold:
            lead = dict(post)
            lead["lead_id"] = f"lead-{len(leads) + 1:04d}"
            leads.append(lead)
            continue

        lead = leads[best_index]
        lead["confidence"] = max(lead.get("confidence", 0), post.get("confidence", 0))
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
        ]:
            lead[key] = better_value(lead.get(key), post.get(key))

    return leads


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
        "confidence",
        "post_text",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for lead in leads:
            row = {field: lead.get(field) for field in fields}
            row["constraints_or_preferences"] = "; ".join(lead.get("constraints_or_preferences") or [])
            writer.writerow(row)


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    raw_dir = output_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    if not os.environ.get("OPENAI_API_KEY"):
        print("Missing OPENAI_API_KEY. Set it before running extraction.", file=sys.stderr)
        return 2

    text = input_path.read_text(encoding="utf-8")
    blocks = split_capture_blocks(text)
    chunks = make_chunks(blocks, args.chunk_chars)

    if not chunks:
        print("No copied text found to process.", file=sys.stderr)
        return 1

    client = OpenAI()
    posts = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"[{index}/{len(chunks)}] Extracting chunk with {len(chunk)} chars")
        result = extract_chunk(client, args.model, chunk, index, len(chunks))
        posts.extend(result.get("posts", []))
        (raw_dir / f"chunk-{index:03d}.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        time.sleep(0.2)

    leads = dedupe(posts, args.dedupe_threshold)

    all_posts_path = output_dir / "all_candidate_posts.json"
    leads_json_path = output_dir / "roommate_leads.json"
    leads_csv_path = output_dir / "roommate_leads.csv"

    all_posts_path.write_text(json.dumps(posts, indent=2, ensure_ascii=False), encoding="utf-8")
    leads_json_path.write_text(json.dumps(leads, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(leads_csv_path, leads)

    print()
    print(f"Candidate posts: {len(posts)}")
    print(f"Deduped leads: {len(leads)}")
    print(f"Wrote: {leads_csv_path}")
    print(f"Wrote: {leads_json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
