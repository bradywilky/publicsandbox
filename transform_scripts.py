from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

# =========================
# SET THESE VARIABLES
# =========================
ROOT_DIR = r"C:\Users\your_name\your_project"
OUTPUT_FILE = r"C:\Users\your_name\project_scroll_output.txt"

IGNORED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".next",
}

IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".class",
    ".jar",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
}

TEXT_EXTENSIONS_TO_SUMMARIZE = {
    ".json",
    ".csv",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".md",
    ".rst",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".sql",
    ".sh",
    ".bat",
    ".ps1",
}

MAX_PREVIEW_LINES = 20
MAX_TEXT_CHARS = 5000
MAX_JSON_ITEMS = 10
MAX_CSV_SAMPLE_ROWS = 5
MAX_CSV_DISTINCT_VALUES = 10

# Optional libraries
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

try:
    import tomllib  # Python 3.11+
except Exception:
    tomllib = None


def is_likely_binary(path: Path, sample_size: int = 2048) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(sample_size)
        if not chunk:
            return False
        return b"\x00" in chunk
    except Exception:
        return True


def safe_read_text(path: Path) -> str | None:
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            pass
    return None


def count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def shorten(value: Any, max_len: int = 120) -> str:
    s = repr(value)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def summarize_json_obj(obj: Any, indent: str = "") -> list[str]:
    lines: list[str] = []
    lines.append(f"{indent}Top-level type: {type(obj).__name__}")

    if isinstance(obj, dict):
        keys = list(obj.keys())
        lines.append(f"{indent}Key count: {len(keys)}")
        lines.append(f"{indent}Keys: {keys[:MAX_JSON_ITEMS]}")
        for key in keys[:MAX_JSON_ITEMS]:
            val = obj[key]
            extra = ""
            if isinstance(val, (list, dict, str)):
                extra = f", length={len(val)}"
            lines.append(f"{indent}- {key}: {type(val).__name__}{extra}")

    elif isinstance(obj, list):
        lines.append(f"{indent}List length: {len(obj)}")
        if obj:
            sample_types = {}
            for item in obj[:MAX_JSON_ITEMS]:
                t = type(item).__name__
                sample_types[t] = sample_types.get(t, 0) + 1
            lines.append(f"{indent}Sample item types: {sample_types}")

            first = obj[0]
            if isinstance(first, dict):
                lines.append(f"{indent}First item keys: {list(first.keys())[:MAX_JSON_ITEMS]}")
            else:
                lines.append(f"{indent}First item example: {shorten(first)}")
    else:
        lines.append(f"{indent}Value preview: {shorten(obj)}")

    return lines


def summarize_json(path: Path) -> str:
    text = safe_read_text(path)
    if text is None:
        return "Could not decode JSON file as text."

    try:
        data = json.loads(text)
    except Exception as e:
        return f"Invalid JSON or parse error: {e}"

    lines = [
        "File type: JSON",
        f"Characters: {len(text)}",
        *summarize_json_obj(data),
    ]
    return "\n".join(lines)


def summarize_yaml(path: Path) -> str:
    text = safe_read_text(path)
    if text is None:
        return "Could not decode YAML file as text."

    lines = [
        "File type: YAML",
        f"Characters: {len(text)}",
    ]

    if yaml is None:
        lines.append("PyYAML not installed, so only raw text metadata is available.")
        preview = "\n".join(text.splitlines()[:MAX_PREVIEW_LINES])
        lines.append("Preview:")
        lines.append(preview)
        return "\n".join(lines)

    try:
        data = yaml.safe_load(text)
    except Exception as e:
        lines.append(f"Parse error: {e}")
        preview = "\n".join(text.splitlines()[:MAX_PREVIEW_LINES])
        lines.append("Preview:")
        lines.append(preview)
        return "\n".join(lines)

    lines.extend(summarize_json_obj(data))
    return "\n".join(lines)


def summarize_toml(path: Path) -> str:
    text = safe_read_text(path)
    if text is None:
        return "Could not decode TOML file as text."

    lines = [
        "File type: TOML",
        f"Characters: {len(text)}",
    ]

    if tomllib is None:
        lines.append("tomllib unavailable in this Python version, so only raw text metadata is available.")
        preview = "\n".join(text.splitlines()[:MAX_PREVIEW_LINES])
        lines.append("Preview:")
        lines.append(preview)
        return "\n".join(lines)

    try:
        data = tomllib.loads(text)
    except Exception as e:
        lines.append(f"Parse error: {e}")
        preview = "\n".join(text.splitlines()[:MAX_PREVIEW_LINES])
        lines.append("Preview:")
        lines.append(preview)
        return "\n".join(lines)

    lines.extend(summarize_json_obj(data))
    return "\n".join(lines)


def summarize_csv(path: Path) -> str:
    text = safe_read_text(path)
    if text is None:
        return "Could not decode CSV file as text."

    try:
        rows = list(csv.reader(text.splitlines()))
    except Exception as e:
        return f"CSV parse error: {e}"

    if not rows:
        return "File type: CSV\nRows: 0 (empty file)"

    header = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []

    lines = [
        "File type: CSV",
        f"Total rows (including header if present): {len(rows)}",
        f"Column count: {len(header)}",
        f"Column names: {header}",
    ]

    if data_rows:
        lines.append(f"Data row count: {len(data_rows)}")

        distinct_samples: dict[str, set[str]] = {col: set() for col in header}
        for row in data_rows[: min(len(data_rows), 100)]:
            for i, col in enumerate(header):
                if i < len(row) and len(distinct_samples[col]) < MAX_CSV_DISTINCT_VALUES:
                    distinct_samples[col].add(row[i])

        lines.append("Sample distinct values by column:")
        for col in header[:MAX_JSON_ITEMS]:
            lines.append(f"- {col}: {sorted(distinct_samples.get(col, set()))}")

        lines.append("Sample rows:")
        for row in data_rows[:MAX_CSV_SAMPLE_ROWS]:
            row_map = {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
            lines.append(shorten(row_map, max_len=300))
    else:
        lines.append("No data rows found beyond header.")

    return "\n".join(lines)


def summarize_generic_text(path: Path) -> str:
    text = safe_read_text(path)
    if text is None:
        return "Could not decode file as text."

    lines = text.splitlines()
    preview = "\n".join(lines[:MAX_PREVIEW_LINES])

    return "\n".join([
        "File type: Generic text-like file",
        f"Characters: {len(text)}",
        f"Approx lines: {count_lines(text)}",
        "Preview:",
        preview[:MAX_TEXT_CHARS],
    ])


def summarize_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".json":
        return summarize_json(path)
    if suffix == ".csv":
        return summarize_csv(path)
    if suffix in {".yaml", ".yml"}:
        return summarize_yaml(path)
    if suffix == ".toml":
        return summarize_toml(path)

    if suffix in TEXT_EXTENSIONS_TO_SUMMARIZE:
        return summarize_generic_text(path)

    if is_likely_binary(path):
        return "Binary or unsupported file type. Content not included."

    return summarize_generic_text(path)


def write_section_header(out, title: str) -> None:
    out.write("\n" + "=" * 100 + "\n")
    out.write(title + "\n")
    out.write("=" * 100 + "\n\n")


def should_skip_file(path: Path) -> bool:
    return path.suffix.lower() in IGNORED_SUFFIXES


def collect_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for current_root, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for filename in filenames:
            path = Path(current_root) / filename
            if should_skip_file(path):
                continue
            files.append(path)

    files.sort(key=lambda p: str(p.relative_to(root)).lower())
    return files


def generate_output(root_dir: str, output_file: str) -> None:
    root = Path(root_dir).expanduser().resolve()
    out_path = Path(output_file).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {root}")

    files = collect_files(root)
    py_files = [p for p in files if p.suffix.lower() == ".py"]
    other_files = [p for p in files if p.suffix.lower() != ".py"]

    with out_path.open("w", encoding="utf-8") as out:
        out.write("CODEBASE EXPORT\n")
        out.write(f"Root directory: {root}\n")
        out.write(f"Total files included: {len(files)}\n")
        out.write(f"Python files (full content): {len(py_files)}\n")
        out.write(f"Non-Python files (summarized): {len(other_files)}\n")

        write_section_header(out, "TABLE OF CONTENTS")
        for p in files:
            rel = p.relative_to(root)
            mode = "FULL PYTHON CONTENT" if p.suffix.lower() == ".py" else "SUMMARY ONLY"
            out.write(f"- {rel} [{mode}]\n")

        if py_files:
            write_section_header(out, "PYTHON FILES - FULL CONTENT")
            for path in py_files:
                rel = path.relative_to(root)
                write_section_header(out, f"FILE: {rel}")

                text = safe_read_text(path)
                if text is None:
                    out.write("Could not decode Python file.\n")
                else:
                    out.write(text)
                    if not text.endswith("\n"):
                        out.write("\n")

        if other_files:
            write_section_header(out, "NON-PYTHON FILES - SUMMARIES")
            for path in other_files:
                rel = path.relative_to(root)
                write_section_header(out, f"FILE: {rel}")
                out.write(summarize_file(path))
                out.write("\n")

    print(f"Done. Wrote output to:\n{out_path}")


# =========================
# RUN
# =========================
generate_output(ROOT_DIR, OUTPUT_FILE)