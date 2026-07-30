#!/usr/bin/env python3
"""Промінь-2: read the hole matrix from the flat 200 dpi greyscale scans.

Unlike `extract_card.py` (which rectifies a slanted colour photograph of a
copper card on the machine's grid), this script works on the flatbed scans from
the forum archive `Перфокарты_Проминь-2.rar`. There:

* each sheet holds several cards side by side, sheet 3400x2336 px,
* the cards are bright, the background (open scanner lid) is black,
* a hole shows the black background -> holes are dark circles on a bright
  ground, unpunched positions show the printed digit,
* every card carries a column scale at the top and the fields «КАРТА N» /
  «ВСЕГО КАРТ».

Output per card: hole coordinates, the matrix rounded onto a grid
(rows x columns, 1 = punched) and a control image with the grid drawn in.

Usage:
    python3 extract_flat_scan.py <scan.jpg> [output_folder]
    python3 extract_flat_scan.py <folder_with_scans> output/ --recursive

Dependencies: opencv-python(-headless), numpy
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np

# Expected values from the scans (200 dpi). Deliberately generous - they only
# serve to tell cards apart from dust specks and sheet edges.
MIN_CARD_AREA = 200_000     # px^2
MIN_CARD_SIDE = 400         # px
MIN_ASPECT_RATIO = 2.0      # cards are clearly wider than tall
EXPECTED_ROWS = 5


def load_grey(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise SystemExit(f"image not readable: {path}")
    return image


def find_cards(grey: np.ndarray) -> list[np.ndarray]:
    """Find the bright card rectangles against the black background.

    Returns the four corner points per card (clockwise from top left).
    """
    # Otsu separates reliably here: card bright, background black.
    _, mask = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Only remove speckle. The holes are deliberately NOT closed: they sit
    # inside the card and do not disturb an outer contour anyway. A kernel big
    # enough to fill them (hole diameter ~55 px) would at the same time bridge
    # the gap between neighbouring cards - two or three cards would then merge
    # into one blob, which fails the aspect ratio test and is lost entirely.
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,
                            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cards = []
    for contour in contours:
        if cv2.contourArea(contour) < MIN_CARD_AREA:
            continue
        rectangle = cv2.minAreaRect(contour)
        (width, height) = rectangle[1]
        if min(width, height) < MIN_CARD_SIDE:
            continue
        if max(width, height) / max(min(width, height), 1) < MIN_ASPECT_RATIO:
            continue
        cards.append(sort_corners(cv2.boxPoints(rectangle)))

    # top to bottom, then left to right - reading order on the sheet
    cards.sort(key=lambda corners: (round(corners[:, 1].min() / 100), corners[:, 0].min()))
    return cards


def sort_corners(points: np.ndarray) -> np.ndarray:
    """Order the corners as top left, top right, bottom right, bottom left."""
    points = np.array(points, dtype=np.float32)
    total = points.sum(axis=1)
    difference = points[:, 0] - points[:, 1]
    return np.array([
        points[np.argmin(total)],       # top left
        points[np.argmax(difference)],  # top right
        points[np.argmax(total)],       # bottom right
        points[np.argmin(difference)],  # bottom left
    ], dtype=np.float32)


def rectify(grey: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Align the card with the axes; the edge lengths are preserved."""
    width = int(round(max(np.linalg.norm(corners[1] - corners[0]),
                          np.linalg.norm(corners[2] - corners[3]))))
    height = int(round(max(np.linalg.norm(corners[3] - corners[0]),
                           np.linalg.norm(corners[2] - corners[1]))))
    target = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(corners, target)
    return cv2.warpPerspective(grey, matrix, (width, height))


def find_holes(card: np.ndarray, opening: int = 15) -> list[dict]:
    """Holes = large, dark, round blobs on the bright card.

    The printing (column scale, digits in the unpunched positions, separator
    lines) is dark as well, but consists of thin strokes. A morphological
    opening with a circle wider than any stroke and smaller than a hole removes
    it completely - after that only holes are left, and only their median
    carries the size scale.
    """
    blurred = cv2.medianBlur(card, 5)
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (opening, opening))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    count, _, statistics, centroids = cv2.connectedComponentsWithStats(mask, 8)
    candidates = []
    for i in range(1, count):
        area = int(statistics[i, cv2.CC_STAT_AREA])
        width = int(statistics[i, cv2.CC_STAT_WIDTH])
        height = int(statistics[i, cv2.CC_STAT_HEIGHT])
        if max(width, height) / max(min(width, height), 1) > 1.5:   # round, not elongated
            continue
        if area / max(width * height, 1) < 0.6:                     # a circle fills ~pi/4
            continue
        x, y = centroids[i]
        candidates.append({"x": float(x), "y": float(y), "area": area,
                           "radius": float(np.sqrt(area / np.pi))})
    if not candidates:
        return []

    # All holes on a card are the same size - drop outliers on both ends.
    median = float(np.median([c["area"] for c in candidates]))
    return [c for c in candidates if 0.5 * median <= c["area"] <= 2.0 * median]


def cluster(values: list[float], tolerance: float) -> list[float]:
    """One-dimensional clustering: sort, split at gaps larger than tolerance."""
    if not values:
        return []
    values = sorted(values)
    groups, current = [], [values[0]]
    for value in values[1:]:
        if value - current[-1] > tolerance:
            groups.append(current)
            current = []
        current.append(value)
    groups.append(current)
    return [float(np.mean(g)) for g in groups]


# Grid geometry, measured on 56 cards where all 30 columns carry holes. The
# spread is tiny (step: 0.03320 +- 0.00006 of the card width), so the grid is a
# property of the card, not an assumption about its content.
EXPECTED_COLUMNS = 30
REL_COLUMN1 = 0.0206      # centre of the first column, as a fraction of the card width
REL_STEP = 0.03320        # column spacing, as a fraction of the card width


def column_grid(detected: list[float], card_width: int) -> tuple[list[float], float]:
    """Fit a complete 30-column grid and report how well it sits.

    Columns in which all five positions are punched leave no holes behind and
    cannot be found by clustering - plain clustering therefore yields between
    24 and 30 columns depending on the card, and shifts every field. But the
    grid is regular, so a comb of fixed pitch is fitted and only its phase is
    taken from the detected columns.

    Returns: the 30 column centres and the largest deviation of a detected
    column from the grid in pixels (a control measure - a few pixels when it
    sits cleanly).
    """
    step = REL_STEP * card_width
    start = REL_COLUMN1 * card_width
    if detected:
        # Fine-tune the phase: median residual offset of the detected columns.
        residuals = [(x - start) - round((x - start) / step) * step for x in detected]
        start += float(np.median(residuals))
    grid = [start + i * step for i in range(EXPECTED_COLUMNS)]
    deviation = max((min(abs(x - g) for g in grid) for x in detected), default=0.0)
    return grid, float(deviation)


def build_matrix(holes: list[dict], card_width: int) -> dict:
    """Lay the holes onto the row/column grid of the card.

    Rows come from clustering the hole positions (five rows are in use on every
    card), columns from the fitted comb.
    """
    if not holes:
        return {"rows": [], "columns": [], "matrix": [], "assignments": [],
                "grid_deviation": 0.0}

    radius = float(np.median([h["radius"] for h in holes]))
    rows = cluster([h["y"] for h in holes], tolerance=radius * 1.6)
    detected = cluster([h["x"] for h in holes], tolerance=radius * 1.6)
    columns, deviation = column_grid(detected, card_width)

    matrix = [[0] * len(columns) for _ in rows]
    assignments = []
    for hole in holes:
        r = int(np.argmin([abs(hole["y"] - y) for y in rows]))
        c = int(np.argmin([abs(hole["x"] - x) for x in columns]))
        matrix[r][c] += 1
        assignments.append({"row": r, "column": c, **hole})

    return {"rows": rows, "columns": columns, "matrix": matrix,
            "assignments": assignments, "grid_deviation": deviation,
            "columns_detected": len(detected)}


def draw_control(card: np.ndarray, grid: dict) -> np.ndarray:
    image = cv2.cvtColor(card, cv2.COLOR_GRAY2BGR)
    for y in grid["rows"]:
        cv2.line(image, (0, int(y)), (image.shape[1], int(y)), (0, 180, 255), 1)
    for x in grid["columns"]:
        cv2.line(image, (int(x), 0), (int(x), image.shape[0]), (255, 140, 0), 1)
    for entry in grid["assignments"]:
        cv2.circle(image, (int(entry["x"]), int(entry["y"])),
                   max(int(entry["radius"]), 3), (0, 0, 255), 2)
    return image


def process_scan(path: Path, output: Path, control_images: bool = True) -> dict:
    grey = load_grey(path)
    output.mkdir(parents=True, exist_ok=True)
    result = {"scan": path.name, "size": [int(grey.shape[1]), int(grey.shape[0])],
              "cards": []}

    for number, corners in enumerate(find_cards(grey), start=1):
        card = rectify(grey, corners)
        holes = find_holes(card)
        grid = build_matrix(holes, card.shape[1])
        stem = f"{path.stem}_card{number:02d}"

        multiple = sum(1 for row in grid["matrix"] for value in row if value > 1)
        entry = {
            "card": number,
            "size": [int(card.shape[1]), int(card.shape[0])],
            "holes": len(holes),
            "rows": len(grid["rows"]),
            "columns": len(grid["columns"]),
            "columns_with_holes": grid.get("columns_detected", 0),
            "grid_deviation_px": round(grid.get("grid_deviation", 0.0), 1),
            "multiple_assignments": multiple,
            "files": {},
        }

        matrix_path = output / f"{stem}_matrix.csv"
        with matrix_path.open("w", newline="", encoding="utf-8") as handle:
            csv.writer(handle).writerows(grid["matrix"])
        entry["files"]["matrix"] = matrix_path.name

        coordinate_path = output / f"{stem}_holes.csv"
        with coordinate_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["row", "column", "x", "y",
                                                        "radius", "area"])
            writer.writeheader()
            for assignment in grid["assignments"]:
                writer.writerow({k: assignment[k] for k in writer.fieldnames})
        entry["files"]["holes"] = coordinate_path.name

        if control_images:
            image_path = output / f"{stem}_control.png"
            cv2.imwrite(str(image_path), draw_control(card, grid))
            entry["files"]["control"] = image_path.name

        result["cards"].append(entry)

    (output / f"{path.stem}_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read the hole matrix from flat Промінь-2 card scans.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("input", type=Path, help="scan file or folder with scans")
    parser.add_argument("output", type=Path, nargs="?", default=Path("extraction_flat"),
                        help="output folder (default: ./extraction_flat)")
    parser.add_argument("--recursive", action="store_true",
                        help="search folders recursively")
    parser.add_argument("--no-control-images", action="store_true",
                        help="do not write PNG control images (faster)")
    args = parser.parse_args(argv)

    if args.input.is_dir():
        pattern = "**/*.jpg" if args.recursive else "*.jpg"
        scans = sorted(args.input.glob(pattern))
    else:
        scans = [args.input]
    if not scans:
        print("no scans found", file=sys.stderr)
        return 1

    total_cards = total_holes = 0
    for scan in scans:
        relative = scan.relative_to(args.input) if args.input.is_dir() else Path(scan.name)
        target = args.output / relative.parent
        report = process_scan(scan, target, not args.no_control_images)
        for card in report["cards"]:
            total_cards += 1
            total_holes += card["holes"]
            warnings = []
            if card["multiple_assignments"]:
                warnings.append("multiple assignment")
            if card["grid_deviation_px"] > 12:
                warnings.append(f"grid sits badly ({card['grid_deviation_px']} px)")
            if card["rows"] != EXPECTED_ROWS:
                warnings.append(f"{card['rows']} rows instead of {EXPECTED_ROWS}")
            warning = ("  <- " + ", ".join(warnings)) if warnings else ""
            print(f"{scan.name}  card {card['card']}: {card['holes']:4d} holes, "
                  f"{card['rows']} rows x {card['columns']} columns "
                  f"({card['columns_with_holes']} with holes){warning}")
        if not report["cards"]:
            print(f"{scan.name}: no card detected")

    print(f"\n{len(scans)} scans, {total_cards} cards, {total_holes} holes "
          f"-> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
