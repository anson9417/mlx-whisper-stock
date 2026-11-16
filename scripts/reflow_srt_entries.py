from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from opencc import OpenCC
except Exception:  # pragma: no cover - handled by fallback
    OpenCC = None  # type: ignore[assignment]


MAX_CHARS = 20
ASCII_TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.+#&%:/_-]*")
SPACE_RE = re.compile(r"\s+")
PUNCTUATION = set("，。！？；：、,.!?;:)]}")
WORDS_TO_DELETE = ["喔", "啊", "哇", "呢", "然後", "的話", "哦", "嗯", "這樣一個", "呀", "哎", "?", "的相關", "的部分", "的這樣"]
KEEP_NA_PREFIXES = (
    "那麼",
    "那個",
    "那些",
    "那一",
    "那邊",
    "那種",
    "那天",
    "那時候",
    "那片",
    "那張",
    "那檔",
    "那是",
    "那隻",
    "那次",
    "那篇",
    "那2次",
)

_OPENCC = OpenCC("s2t") if OpenCC else None


@dataclass
class Entry:
    index: int
    start_ms: int
    end_ms: int
    text: str


def parse_timestamp(value: str) -> int:
    hh, mm, rest = value.split(":")
    ss, ms = rest.split(",")
    return ((int(hh) * 60 + int(mm)) * 60 + int(ss)) * 1000 + int(ms)


def format_timestamp(value: int) -> str:
    value = max(0, value)
    ms = value % 1000
    total_seconds = value // 1000
    ss = total_seconds % 60
    total_minutes = total_seconds // 60
    mm = total_minutes % 60
    hh = total_minutes // 60
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def parse_srt(path: Path) -> list[Entry]:
    content = path.read_text(encoding="utf-8").strip()
    blocks = re.split(r"\n\s*\n", content)
    entries: list[Entry] = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3 or " --> " not in lines[1]:
            continue
        start, end = lines[1].split(" --> ", 1)
        entries.append(
            Entry(
                index=int(lines[0].strip()),
                start_ms=parse_timestamp(start.strip()),
                end_ms=parse_timestamp(end.strip()),
                text=" ".join(line.strip() for line in lines[2:] if line.strip()),
            )
        )
    return entries


def load_replacements(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 2:
                continue
            wrong = row[0].strip()
            correct = row[1].strip()
            if wrong and correct and wrong != correct:
                rows.append((wrong, correct))
    return rows


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    text = SPACE_RE.sub(" ", text).strip()
    i = 0
    while i < len(text):
        match = ASCII_TOKEN_RE.match(text, i)
        if match:
            tokens.append(match.group())
            i = match.end()
            continue
        char = text[i]
        if char.isspace():
            i += 1
            continue
        tokens.append(char)
        i += 1
    return tokens


def needs_space(prev: str, token: str) -> bool:
    return bool(prev and prev[-1].isascii() and token[0].isascii())


def split_long_token(token: str, max_chars: int) -> list[str]:
    if len(token) <= max_chars:
        return [token]
    return [token[i : i + max_chars] for i in range(0, len(token), max_chars)]


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    raw_tokens = tokenize(text)
    tokens: list[str] = []
    for token in raw_tokens:
        tokens.extend(split_long_token(token, max_chars))

    lines: list[str] = []
    current = ""

    for token in tokens:
        if not current and lines and token in PUNCTUATION:
            lines[-1] = f"{lines[-1]}{token}"
            continue
        sep = " " if current and needs_space(current, token) else ""
        candidate = f"{current}{sep}{token}" if current else token
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = token
        else:
            current = candidate

    if current:
        lines.append(current)
    return [normalize_spacing(line) for line in (lines or [""])]


def normalize_spacing(text: str) -> str:
    text = SPACE_RE.sub(" ", text).strip()
    chars: list[str] = []
    for i, char in enumerate(text):
        if char != " ":
            chars.append(char)
            continue
        prev_char = text[i - 1] if i > 0 else ""
        next_char = text[i + 1] if i + 1 < len(text) else ""
        if prev_char.isascii() and not prev_char.isspace() and next_char.isascii() and not next_char.isspace():
            chars.append(char)
    return "".join(chars)


def to_traditional(text: str) -> str:
    if not _OPENCC:
        return text
    return _OPENCC.convert(text)


def clean_text(text: str, replacements: list[tuple[str, str]], stats: dict[str, int]) -> str:
    text = to_traditional(text)
    for word in WORDS_TO_DELETE:
        count = text.count(word)
        if count:
            text = text.replace(word, "")
            stats[f"delete:{word}"] = stats.get(f"delete:{word}", 0) + count

    for wrong, correct in replacements:
        count = text.count(wrong)
        if count:
            text = text.replace(wrong, correct)
            stats[f"replace:{wrong}->{correct}"] = stats.get(f"replace:{wrong}->{correct}", 0) + count

    if text.startswith("那") and not text.startswith(KEEP_NA_PREFIXES):
        text = text[1:]
        stats["trim:leading_那"] = stats.get("trim:leading_那", 0) + 1

    text = SPACE_RE.sub(" ", text).strip()
    text = re.sub(r"？+", "？", text)
    text = re.sub(r"！+", "！", text)
    text = re.sub(r"，，+", "，", text)
    text = re.sub(r"。。+", "。", text)
    return normalize_spacing(text)


def split_entry(entry: Entry, replacements: list[tuple[str, str]], stats: dict[str, int]) -> list[Entry]:
    cleaned = clean_text(entry.text, replacements, stats)
    if not cleaned:
        stats["drop:empty"] = stats.get("drop:empty", 0) + 1
        return []
    chunks = split_text(cleaned, MAX_CHARS)
    chunks = [chunk for chunk in chunks if len(chunk.strip()) > 1]
    if not chunks:
        stats["drop:single_char"] = stats.get("drop:single_char", 0) + 1
        return []
    if len(chunks) == 1:
        return [Entry(index=0, start_ms=entry.start_ms, end_ms=entry.end_ms, text=chunks[0])]

    duration = max(entry.end_ms - entry.start_ms, len(chunks))
    total_chars = sum(max(len(chunk), 1) for chunk in chunks)
    results: list[Entry] = []
    cursor = entry.start_ms

    for i, chunk in enumerate(chunks):
        remaining_chunks = len(chunks) - i
        remaining_duration = entry.end_ms - cursor
        if i == len(chunks) - 1:
            end_ms = entry.end_ms
        else:
            weight = max(len(chunk), 1) / total_chars
            allocated = max(1, round(duration * weight))
            min_remaining = remaining_chunks - 1
            allocated = min(allocated, remaining_duration - min_remaining)
            end_ms = cursor + allocated
        results.append(Entry(index=0, start_ms=cursor, end_ms=end_ms, text=chunk))
        cursor = end_ms

    return results


def write_srt(path: Path, entries: list[Entry]) -> None:
    blocks = []
    for idx, entry in enumerate(entries, start=1):
        blocks.append(
            "\n".join(
                [
                    str(idx),
                    f"{format_timestamp(entry.start_ms)} --> {format_timestamp(entry.end_ms)}",
                    entry.text,
                ]
            )
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: reflow_srt_entries.py INPUT.srt WORDS.csv", file=sys.stderr)
        return 1

    path = Path(sys.argv[1]).resolve()
    words_path = Path(sys.argv[2]).resolve()
    entries = parse_srt(path)
    replacements = load_replacements(words_path)
    stats: dict[str, int] = {}
    new_entries: list[Entry] = []
    for entry in entries:
        new_entries.extend(split_entry(entry, replacements, stats))
    write_srt(path, new_entries)
    print(f"Updated: {path}")
    print(f"Entries: {len(entries)} -> {len(new_entries)}")
    print(f"Changes: {sum(stats.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
