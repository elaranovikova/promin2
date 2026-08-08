#!/usr/bin/env python3
"""Generates decks.js for the web interface from the extracted hole matrices.

Usage:
    python3 build_data.py <extraction-dir>    # e.g. the flat-scan output dir

Each card is embedded as 5 strings of 30 characters ('1' = hole). The web
interface decodes them itself, with the same logic as the CLI decoder.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

# The example programs are read from their .asm files (in ../examples/) and
# assembled into synthetic cards (inverse of the decoding), so that they too
# are rendered as punch cards.
EXAMPLES = [
    {
        "name": "Example: circumference 2·π·r",
        "hint": "Input: cell 051 = radius. Result at stop 001.",
        "file": "circumference.asm",
        "inputs": {"51": 1.5},
        "inputs_raw": {},
    },
    {
        "name": "Example: loop with СчП (5 × +1)",
        "hint": "Cell 010 is the counter word: sign −, counter 100−N. Result: 5.",
        "file": "sum_loop.asm",
        "inputs": {},
        "inputs_raw": {"10": "-00095"},
    },
    {
        "name": "Example: π by Machin's formula (self-check)",
        "hint": "Computes π with basic arithmetic only, then checks itself "
                "against the π constant in cell 081. Stop 1: π, stop 2: deviation.",
        "file": "pi_machin.asm",
        "inputs": {},
        "inputs_raw": {"10": "-00095", "11": "-00099"},
    },
]

OP_WEIGHTS = [16, 8, 4, 2, 1]
DIGIT_WEIGHTS = [5, 2, 1, 1]

# machine mnemonics -> operation codes (the machine language stays Cyrillic)
MNEMONICS = {
    "СЛ": 1, "ВЫЧ1": 2, "ВЫЧ2": 3, "УМН": 4, "ДЕЛ": 5, "ЧТ": 6, "ЗП": 7,
    "БП": 8, "УП1": 9, "УП2": 10, "ЧТII": 11, "ЗПII": 12, "БПII": 13,
    "СЛФ": 14, "ВЫЧФ": 15, "SIN": 16, "COS": 17, "TG": 18, "SH": 19,
    "СЧП": 19, "CH": 20, "TH": 21, "ASIN": 22, "ACOS": 23, "ATG": 24,
    "√": 25, "SQRT": 25, "EXP": 26, "LN": 27, "ФР": 29, "ОСТ": 31,
}


def parse_asm(path: Path) -> list[tuple[int, int]]:
    """Line format: [number] MNEMONIC address - or '---' for an empty slot."""
    commands = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split(";")[0].split("#")[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts and re.fullmatch(r"\d{1,3}", parts[0]):
            parts = parts[1:]                     # leading command number
        if not parts or parts[0] == "---":
            continue
        name = parts[0].upper()
        if name not in MNEMONICS:
            raise SystemExit(f"unknown mnemonic in {path.name}: {line!r}")
        commands.append((MNEMONICS[name], int(parts[1]) if len(parts) > 1 else 0))
    return commands


def _punch_column(value: int, weights: list[int]) -> list[int]:
    """Hole pattern of one column: a hole erases its weight (metal counts)."""
    rows = []
    remainder = value
    for weight in weights:
        if remainder >= weight:
            rows.append(0)            # metal stays - weight counts
            remainder -= weight
        else:
            rows.append(1)            # hole - weight erased
    if remainder:
        raise ValueError(f"{value} not representable with {weights}")
    return rows


def commands_to_cards(commands: list[tuple[int, int]]) -> list[list[str]]:
    cards = []
    for start in range(0, len(commands), 10):
        chunk = commands[start:start + 10]
        columns: list[list[int]] = []
        for op, addr in chunk:
            hundreds, tens, units = addr // 100, (addr // 10) % 10, addr % 10
            columns.append(_punch_column(op, OP_WEIGHTS))
            columns.append(_punch_column(tens, DIGIT_WEIGHTS) + [0 if hundreds else 1])
            columns.append(_punch_column(units, DIGIT_WEIGHTS) + [1])
        while len(columns) < 30:                  # unused remainder = solid metal
            columns.append([0, 0, 0, 0, 0])
        cards.append(["".join(str(columns[c][r]) for c in range(30))
                      for r in range(5)])
    return cards


def load_deck_matrices(folder: Path) -> list[list[str]]:
    cards = []
    for file in sorted(folder.glob("*_matrix.csv")):
        with file.open(newline="", encoding="utf-8") as handle:
            matrix = [[1 if int(v) > 0 else 0 for v in row]
                      for row in csv.reader(handle) if row]
        if len(matrix) != 5 or len(matrix[0]) != 30:
            continue
        cards.append(["".join(str(v) for v in row) for row in matrix])
    return cards


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    root = Path(sys.argv[1])
    decks = []

    example_dir = Path(__file__).resolve().parents[1] / "examples"
    for example in EXAMPLES:
        decks.append({
            "name": example["name"],
            "group": "Examples",
            "hint": example["hint"],
            "cards": commands_to_cards(parse_asm(example_dir / example["file"])),
            "inputs": example["inputs"],
            "inputs_raw": example["inputs_raw"],
        })

    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        cards = load_deck_matrices(folder)
        if cards:
            decks.append({
                "name": folder.name,
                "group": "Card archive (85 scans, Radon 2022)",
                "hint": "",
                "cards": cards,
                "inputs": {},
                "inputs_raw": {},
            })

    target = Path(__file__).parent / "decks.js"
    target.write_text("// generated by build_data.py - do not edit by hand\n"
                      "const DECKS = " + json.dumps(decks, ensure_ascii=False) + ";\n",
                      encoding="utf-8")
    total = sum(len(d["cards"]) for d in decks)
    print(f"{len(decks)} decks, {total} cards -> {target} "
          f"({target.stat().st_size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
