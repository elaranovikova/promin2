#!/usr/bin/env python3
"""Промінь-2: translate the hole matrix of one card into instructions.

The basis is the legend printed on the **unpunched** aluminium card of the
Tangible Media Collection, where it is fully readable (see
`08_tangible_media/`). The 30 columns of a card are organized in groups of
three, one instruction per group:

    column 1 of the group   weights 16 8 4 2 1   -> operation code 0..31
    column 2 of the group   weights  5 2 1 1 1   -> address digit (tens)
    column 3 of the group   weights  5 2 1 1     -> address digit (units)

A card therefore carries 10 instructions of the form operation + two-digit
decimal address. Both match the textbook: 32 operations and two-digit cell
addresses.

**Polarity - the weakest point of this reconstruction.** What is scored here is
the *unpunched* position: the metal left standing carries its weight, a hole
clears it. The opposite reading (hole counts) is the exact mirror image and
cannot be ruled out by the argument that it produces invalid digits - both
readings do that, only in different places: a uniform column always yields 10,
under one reading for completely unpunched columns, under the other for
completely punched ones.

What speaks for the reading chosen here (4040 decimal digits from 202 cards):

* Address digits are distributed plausibly - 0 is the most frequent digit at
  20 %, and the frequency falls off from there. Under the opposite reading 9
  would be the most frequent digit and 0 a rare one, which is unnatural for
  memory addresses.
* Only 2.1 % of the columns are uniform (value 10) instead of 12.7 %. Those
  columns read as unused instruction slots on a card that was punched only in
  part; the output marks them as "empty" rather than emitting an address.
* Physically it fits a metal card acting as a mask over contact pins: metal
  closes the contact, the hole breaks it.

This is a well supported but unproven choice. It is settled only by a test
vector - a program from chapters 6-7 of the textbook held against a card that
has been read.

Usage:
    python3 decode_card.py <matrix.csv> [more.csv ...]
    python3 decode_card.py <folder> --recursive --csv instructions.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

OPERATION_WEIGHTS = [16, 8, 4, 2, 1]
DIGIT_WEIGHTS = [5, 2, 1, 1]           # rows 1-4 carry the digit 0..9
COLUMNS_PER_CARD = 30
ROWS = 5

# Operation table, textbook table 5 (pp. 18-20) and table 6 (Промінь-2).
OPERATIONS = {
    1: ("Сл", "addition, S := S + a"),
    2: ("Выч1", "subtraction, S := S - a"),
    3: ("Выч2", "reverse subtraction, S := a - S"),
    4: ("Умн", "multiplication, S := S * a"),
    5: ("Дел", "division, S := S / a"),
    6: ("Чт", "read the cell into the accumulator, S := a"),
    7: ("Зп", "write the accumulator to the cell, a := S"),
    8: ("БП", "unconditional jump to k"),
    9: ("УП1", "conditional jump to k if S = 0"),
    10: ("УП2", "conditional jump to k if S < 0"),
    11: ("ЧтII", "read through a second-rank address"),
    12: ("ЗпII", "write through a second-rank address"),
    13: ("БПII", "jump through a second-rank address"),
    14: ("Слф", "fixed-point addition"),
    15: ("Вычф", "fixed-point subtraction"),
    16: ("sin", "S := sin S"),
    17: ("cos", "S := cos S"),
    18: ("tg", "S := tg S"),
    # Table 5 covers the Промінь-М and lists 19 as sh. For the Промінь-2,
    # table 6 names an extra instruction СчП (readdressing and loop counting) -
    # but the code column of that row is empty in the book. The way the cards
    # use it argues that on the Промінь-2 code 19 is that extra instruction:
    # of 44 occurrences, 20 are followed directly by a conditional jump
    # (12 of them backwards, so a loop) and 15 by another 19 - chains of up to
    # four. A hyperbolic sine followed in 45 % of cases by "jump if S = 0"
    # makes no sense at all.
    19: ("sh/СчП", "table 5: sh - on the Промінь-2 probably СчП "
                   "(readdressing and loop counting), see comment"),
    20: ("ch", "S := ch S"),
    21: ("th", "S := th S"),
    22: ("asin", "S := arcsin S"),
    23: ("acos", "S := arccos S"),
    24: ("atg", "S := arctg S"),
    25: ("√", "S := square root of S"),
    26: ("exp", "S := e to the power of S"),
    27: ("ln", "S := ln S"),
    29: ("Фр", "sign transfer, S := |S| * sign a"),
    31: ("Ост", "halt (or print the accumulator)"),
}

# Instructions whose address part means an instruction number (0..159), not a cell.
JUMP_INSTRUCTIONS = {8, 9, 10, 13}


class CardFormatError(ValueError):
    pass


def read_matrix(path: Path) -> list[list[int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        matrix = [[int(value) for value in row] for row in csv.reader(handle) if row]
    if len(matrix) != ROWS:
        raise CardFormatError(f"{path.name}: {len(matrix)} rows instead of {ROWS}")
    if len(matrix[0]) != COLUMNS_PER_CARD:
        raise CardFormatError(
            f"{path.name}: {len(matrix[0])} columns instead of {COLUMNS_PER_CARD} - "
            "empty columns (without a single hole) cannot be determined from the "
            "hole positions alone")
    return matrix


def column_value(matrix: list[list[int]], column: int, weights: list[int]) -> int:
    """Value of a column: sum of the weights of all *unpunched* positions."""
    return sum(weight for row, weight in enumerate(weights)
               if matrix[row][column] == 0)


def decode(matrix: list[list[int]]) -> list[dict]:
    instructions = []
    for slot, start in enumerate(range(0, COLUMNS_PER_CARD, 3), start=1):
        operation = column_value(matrix, start, OPERATION_WEIGHTS)
        tens = column_value(matrix, start + 1, DIGIT_WEIGHTS)
        units = column_value(matrix, start + 2, DIGIT_WEIGHTS)
        # The tens column has a fifth position, the units column does not: it
        # carries the hundreds digit. The textbook describes the same
        # distinction for the plug matrix as "digit with or without a bar"
        # (p. 16) - a two-digit address means hundreds 0, a three-digit one 1.
        hundreds = 1 if matrix[4][start + 1] == 0 else 0
        address = hundreds * 100 + tens * 10 + units
        name, meaning = OPERATIONS.get(operation, (None, None))
        instructions.append({
            "slot": slot,
            "columns": f"{start + 1}-{start + 3}",
            "operation": operation,
            "name": name or "?",
            "meaning": meaning or "no entry in table 5",
            "address": address,
            "address_kind": "instruction" if operation in JUMP_INSTRUCTIONS else "cell",
            # A slot that was never punched leaves every position standing and
            # so evaluates to "Ост 199" - the signature of an unused
            # instruction slot. A real Ост carries a different address.
            "empty": operation == 31 and address == 199,
        })
    return instructions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Translate hole matrices into instructions (operation + address).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("input", nargs="+", type=Path,
                        help="matrix CSVs from extract_flat_scan.py, or a folder")
    parser.add_argument("--recursive", action="store_true", help="search folders recursively")
    parser.add_argument("--csv", type=Path, default=None,
                        help="also write all instructions into one collected CSV")
    args = parser.parse_args(argv)

    files: list[Path] = []
    for entry in args.input:
        if entry.is_dir():
            pattern = "**/*_matrix.csv" if args.recursive else "*_matrix.csv"
            files.extend(sorted(entry.glob(pattern)))
        else:
            files.append(entry)
    if not files:
        print("no matrix CSV found", file=sys.stderr)
        return 1

    all_rows = []
    skipped = 0
    for path in files:
        try:
            matrix = read_matrix(path)
        except CardFormatError as error:
            print(f"skipped - {error}", file=sys.stderr)
            skipped += 1
            continue

        instructions = decode(matrix)
        print(f"\n{path.name}")
        for instruction in instructions:
            if instruction["empty"]:
                print(f"  {instruction['slot']:2d}  ---")
                continue
            print(f"  {instruction['slot']:2d}  {instruction['name']:>5} "
                  f"{instruction['address']:03d}"
                  f"    (op {instruction['operation']:2d}, {instruction['address_kind']} "
                  f"{instruction['address']:03d})   {instruction['meaning']}")
        for instruction in instructions:
            all_rows.append({"file": str(path), **instruction})

    if args.csv and all_rows:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n{len(all_rows)} instructions -> {args.csv}")

    empty = sum(1 for row in all_rows if row["empty"])
    print(f"\n{len(files) - skipped} cards decoded, {skipped} skipped, "
          f"{len(all_rows)} instruction slots of which {empty} empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
