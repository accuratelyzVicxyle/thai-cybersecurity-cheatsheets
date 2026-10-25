#!/usr/bin/env python3
"""Translate selected public Markdown notes from Vietnamese to Thai.

Fenced code is preserved byte-for-byte except for full-line and trailing comments.
Inline code, URLs, and Markdown link targets are masked before translation.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thai"
FILES = [
    "Cheatsheet Crypto.md",
    "Cryptohack Libs cần dùng.md",
    "RSA - Sơ đồ nhận diện dạng bài.md",
    "Symmetric Cipher - Sơ đồ nhận diện dạng bài.md",
    "cheatsheet-asymmetric.md",
    "cheatsheet-casebook.md",
    "cheatsheet-openssl.md",
    "cheatsheet-symmetric.md",
    "tools.md",
]

ENDPOINT = "https://translate.googleapis.com/translate_a/single"
SEP_TEMPLATE = "ZXQSEP{index:04d}QXZ"
# Masking now happens in one pass, so these stable ASCII tokens cannot be nested.
KEEP_TEMPLATE = "ZXQKEEP{index:04d}QXZ"
MAX_QUERY_CHARS = 3600


def mask_fragments(text: str) -> tuple[str, list[str]]:
    kept: list[str] = []

    def keep(match: re.Match[str]) -> str:
        token = KEEP_TEMPLATE.format(index=len(kept))
        kept.append(match.group(0))
        return token

    # A single substitution pass is intentional: later protection rules must not
    # see and re-mask placeholders emitted by earlier rules.
    protected = re.compile(
        "|".join(
            [
                r"^\s*(?:#{1,6}|>|[-*+]|\d+\.)\s+",
                r"`[^`\n]*`",
                r"(?<=\])\([^\s)]+\)",
                r"https?://[^\s)>]+",
                r"</?[A-Za-z][^>]*>",
                r"\b[A-Za-z_][A-Za-z0-9_.]*\([^()\n]*\)",
                r"(?<!\S)\S*[=·^⊕≈√ΔφΠ⁻¹²³⁴⁵⁶⁷⁸⁹₀₁₂₃₄₅₆₇₈₉−]\S*(?!\S)",
            ]
        )
    )
    text = protected.sub(keep, text)
    return text, kept


def unmask_fragments(text: str, kept: list[str]) -> str:
    for _ in range(3):
        previous = text
        for index, original in enumerate(kept):
            token = KEEP_TEMPLATE.format(index=index)
            # Exact replacement preserves intentional spaces around inline code.
            text = text.replace(token, original)
        if text == previous:
            break
    return text


def translate_request(text: str) -> str:
    params = urllib.parse.urlencode(
        {"client": "gtx", "sl": "vi", "tl": "th", "dt": "t", "q": text}
    )
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": "Mozilla/5.0 cheatsheet-translation/1.0"},
    )
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                payload = json.load(response)
            return "".join(piece[0] for piece in payload[0] if piece[0])
        except Exception as error:  # transient endpoint/rate-limit errors
            last_error = error
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"translation request failed: {last_error}")


def translate_units(units: list[str]) -> list[str]:
    if not units:
        return []

    results: list[str] = []
    batch: list[tuple[str, list[str]]] = []
    batch_size = 0

    def flush() -> None:
        nonlocal batch, batch_size
        if not batch:
            return
        parts: list[str] = []
        for index, (masked, _) in enumerate(batch):
            if index:
                parts.append(SEP_TEMPLATE.format(index=index))
            parts.append(masked)
        translated = translate_request("\n".join(parts))
        pattern = r"\s*ZXQSEP\d{4}QXZ\s*"
        translated_parts = re.split(pattern, translated)
        if len(translated_parts) != len(batch):
            raise RuntimeError(
                f"separator mismatch: expected {len(batch)}, got {len(translated_parts)}"
            )
        for translated_part, (_, kept) in zip(translated_parts, batch):
            results.append(unmask_fragments(translated_part.strip(), kept))
        batch = []
        batch_size = 0
        time.sleep(0.12)

    for unit in units:
        masked, kept = mask_fragments(unit)
        extra = len(masked) + 24
        if batch and batch_size + extra > MAX_QUERY_CHARS:
            flush()
        batch.append((masked, kept))
        batch_size += extra
    flush()
    return results


def translatable_code_comment(line: str) -> tuple[str, str, str] | None:
    full = re.match(r"^(\s*#\s?)(.*?)(\r?\n?)$", line)
    if full and full.group(2).strip():
        return full.group(1), full.group(2), full.group(3)
    trailing = re.match(r"^(.*?\s+#\s?)([^#].*?)(\r?\n?)$", line)
    if trailing and trailing.group(2).strip():
        return trailing.group(1), trailing.group(2), trailing.group(3)
    return None


def translate_markdown(source: str) -> str:
    lines = source.splitlines(keepends=True)
    units: list[str] = []
    # (line index, start offset, end offset) replacements.
    positions: list[tuple[int, int, int]] = []
    fence_language: str | None = None

    for index, line in enumerate(lines):
        fence = re.match(r"^\s*```\s*([^\s`]*)", line)
        if fence:
            fence_language = None if fence_language is not None else fence.group(1).lower()
            continue

        if fence_language == "mermaid":
            # Mermaid syntax must stay exact, but all user-visible node/edge labels
            # in these guides are quoted strings.
            for match in re.finditer(r'"([^"\n]+)"', line):
                positions.append((index, match.start(1), match.end(1)))
                units.append(match.group(1))
            continue

        if fence_language is not None:
            comment = translatable_code_comment(line)
            if comment:
                prefix, body, ending = comment
                start = len(prefix)
                positions.append((index, start, start + len(body)))
                units.append(body)
            continue

        ending_match = re.search(r"(\r?\n)$", line)
        ending = ending_match.group(1) if ending_match else ""
        body = line[: -len(ending)] if ending else line
        if not body.strip() or re.match(r"^\s*[-:| ]+$", body):
            continue
        positions.append((index, 0, len(body)))
        units.append(body)

    translated = translate_units(units)
    if len(translated) != len(positions):
        raise RuntimeError("internal line count mismatch")
    replacements_by_line: dict[int, list[tuple[int, int, str]]] = {}
    for (index, start, end), new_body in zip(positions, translated):
        replacements_by_line.setdefault(index, []).append((start, end, new_body))
    for index, replacements in replacements_by_line.items():
        for start, end, new_body in sorted(replacements, reverse=True):
            lines[index] = lines[index][:start] + new_body + lines[index][end:]
    return "".join(lines)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for filename in FILES:
        source_path = ROOT / filename
        if not source_path.exists():
            print(f"missing source: {filename}", file=sys.stderr)
            return 2
        print(f"translating {filename}", flush=True)
        translated = translate_markdown(source_path.read_text(encoding="utf-8"))
        (OUT / filename).write_text(translated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
