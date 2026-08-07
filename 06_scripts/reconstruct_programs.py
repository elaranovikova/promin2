#!/usr/bin/env python3
"""Промінь-2: assemble card decks into programs and evaluate them.

A deck is one folder of the scan archive. Every card carries 10 instructions,
and the cards of a deck fill the instruction memory (cells 000-159) in order.
That order follows the scan order and the position of the cards on the sheet
(top -> bottom).

This assumption is not taken on faith but tested: jump instructions name
instruction numbers, and those have to fall inside the deck's own range. How
well that works out is reported as a hit rate for every deck - with the wrong
order, jumps point into nothing.

Usage:
    python3 reconstruct_programs.py <extraction-folder> [output]
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decode_card import decode, read_matrix, CardFormatError  # noqa: E402

INSTRUCTION_MEMORY = 160       # cells 000..159
CONSTANTS = set(range(80, 100)) | set(range(180, 200))
FUNCTIONS = {16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27}

# Only for these jumps does the address part hold the instruction number
# directly. БПII (13) jumps through a second-rank address: there the address
# part names the cell that holds the target - a value that cannot be read off
# the card and must not be checked as an instruction number.
DIRECT_JUMPS = {8, 9, 10}
INDIRECT = {11, 12, 13}


def collect_decks(root: Path) -> dict[str, list[Path]]:
    """Collect the matrix files per deck, in card order.

    The file name carries the scan and the card number on the sheet
    (`<scan>_cardNN_matrix.csv`), so sorting by name sorts both correctly.
    """
    decks: dict[str, list[Path]] = collections.defaultdict(list)
    for path in sorted(root.rglob("*_matrix.csv")):
        deck = path.parent.name if path.parent != root else "(no deck)"
        decks[deck].append(path)
    return dict(decks)


def load_program(files: list[Path]) -> tuple[list[dict], list[str]]:
    """Assemble the cards into one numbered instruction band."""
    program, errors = [], []
    for card_no, path in enumerate(files):
        try:
            matrix = read_matrix(path)
        except CardFormatError as exception:
            errors.append(str(exception))
            # Placeholders, so the numbering of the following cards stays right.
            program.extend({"number": card_no * 10 + i, "missing": True}
                           for i in range(10))
            continue
        for instruction in decode(matrix):
            program.append({
                "number": card_no * 10 + instruction["slot"] - 1,
                "card": card_no + 1,
                "source": path.name,
                "missing": False,
                **instruction,
            })
    return program, errors


def evaluate(deck: str, program: list[dict], errors: list[str]) -> dict:
    real = [i for i in program if not i["missing"] and not i["empty"]]
    jumps = [i for i in real if i["operation"] in DIRECT_JUMPS]
    indirect = [i for i in real if i["operation"] in INDIRECT]
    reach = len(program)

    within_deck = [i for i in jumps if i["address"] < reach]
    within_memory = [i for i in jumps if i["address"] < INSTRUCTION_MEMORY]
    backward = [i for i in within_deck if i["address"] < i["number"]]

    cells = [i["address"] for i in real if i["operation"] not in DIRECT_JUMPS]
    constants = [a for a in cells if a in CONSTANTS]
    functions = collections.Counter(i["name"] for i in real
                                    if i["operation"] in FUNCTIONS)

    return {
        "deck": deck,
        "cards": max((i["card"] for i in program if not i["missing"]), default=0),
        "instruction_slots": len(program),
        "instructions": len(real),
        "empty": sum(1 for i in program if not i["missing"] and i["empty"]),
        "unreadable": len(errors),
        "jumps_direct": len(jumps),
        "jumps_indirect": len(indirect),
        "jumps_within_deck": len(within_deck),
        "jumps_within_instruction_memory": len(within_memory),
        "backward_jumps": len(backward),
        "hit_rate_within_deck": round(100 * len(within_deck) / len(jumps), 1) if jumps else None,
        "highest_jump_target": max((i["address"] for i in jumps), default=None),
        "halts": sum(1 for i in real if i["operation"] == 31),
        "cell_accesses": len(cells),
        "constant_accesses": len(constants),
        "distinct_cells": len(set(cells)),
        "highest_cell": max(cells, default=None),
        "functions": dict(functions),
        "operation_profile": dict(collections.Counter(i["name"] for i in real).most_common()),
        "errors": errors,
    }


def write_listing(deck: str, program: list[dict], report: dict, target: Path) -> None:
    lines = [
        f"# {deck}",
        "",
        f"{report['cards']} cards, {report['instructions']} instructions, "
        f"{report['empty']} empty slots",
    ]
    if report["jumps_direct"]:
        lines.append(
            f"{report['jumps_direct']} direct jumps, {report['jumps_within_deck']} of them "
            f"inside the deck ({report['hit_rate_within_deck']} %), "
            f"{report['backward_jumps']} backwards (loops); "
            f"{report['jumps_indirect']} indirect accesses (ЧтII/ЗпII/БПII)")
    lines += ["", "No   Card   Instruction   Meaning", "-" * 72]

    targets = {i["address"] for i in program
               if not i["missing"] and not i["empty"] and i["operation"] in DIRECT_JUMPS}
    for instruction in program:
        if instruction["missing"]:
            lines.append(f"{instruction['number']:03d}    ?      (card not readable)")
            continue
        mark = "→" if instruction["number"] in targets else " "
        if instruction["empty"]:
            lines.append(f"{instruction['number']:03d} {mark}  {instruction['card']:2d}     ---")
            continue
        kind = "instruction" if instruction["operation"] in DIRECT_JUMPS else "cell"
        lines.append(f"{instruction['number']:03d} {mark}  {instruction['card']:2d}     "
                     f"{instruction['name']:>5} {instruction['address']:03d}   "
                     f"{kind} {instruction['address']:03d} - {instruction['meaning']}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble card decks into programs and evaluate them.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("input", type=Path, help="output folder of extract_flat_scan.py")
    parser.add_argument("output", type=Path, nargs="?", default=Path("programs"),
                        help="target folder (default: ./programs)")
    args = parser.parse_args(argv)

    decks = collect_decks(args.input)
    if not decks:
        print("no matrix CSVs found", file=sys.stderr)
        return 1
    args.output.mkdir(parents=True, exist_ok=True)

    reports = []
    for deck, files in sorted(decks.items()):
        program, errors = load_program(files)
        report = evaluate(deck, program, errors)
        reports.append(report)
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in deck)
        write_listing(deck, program, report, args.output / f"{safe}.txt")
        rate = (f"{report['hit_rate_within_deck']:5.1f} %"
                if report["hit_rate_within_deck"] is not None else "    -")
        print(f"{deck:42s} {report['cards']:3d} cards  {report['instructions']:4d} instructions  "
              f"{report['jumps_direct']:3d} jumps  inside deck {rate}")

    (args.output / "overview.json").write_text(
        json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.output / "overview.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [k for k in reports[0] if k not in ("functions", "operation_profile", "errors")]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(reports)

    total_jumps = sum(r["jumps_direct"] for r in reports)
    total_hits = sum(r["jumps_within_deck"] for r in reports)
    within_memory = sum(r["jumps_within_instruction_memory"] for r in reports)
    print(f"\n{len(reports)} decks, {sum(r['instructions'] for r in reports)} instructions")
    print(f"{total_jumps} jumps in total: {total_hits} inside their own deck "
          f"({100 * total_hits / total_jumps:.1f} %), "
          f"{within_memory} inside instruction memory 000-159 "
          f"({100 * within_memory / total_jumps:.1f} %)")
    print(f"-> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
