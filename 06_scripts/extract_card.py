#!/usr/bin/env python3
"""
Промінь-2 punched card extraction
=================================
Perspective rectification of the copper metal card, hole detection, output of
the hole coordinates.

Status: proof of concept on ONE slanted museum photograph.
Limit: the row assignment sits at the resolution limit of that photograph
(hole diameter ~= row spacing). A dependable bit/cell matrix needs the FLAT
200 dpi greyscale scans of the complete card set (Phantom thread t=43656). On
flat scans the same pipeline runs through cleanly.

Usage:
    python3 extract_card.py  <input_image.jpg>  [output_folder]

Dependencies: opencv-python-headless, numpy, scipy (optional)
"""
import sys, os
import cv2
import numpy as np

def find_plate_corners(img):
    """Find the copper plate by HSV segmentation, return its 4 corner points."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    copper = ((h < 25) & (s > 60) & (v > 40)).astype(np.uint8) * 255
    copper = cv2.morphologyEx(copper, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    copper = cv2.morphologyEx(copper, cv2.MORPH_OPEN,  np.ones((25, 25), np.uint8))
    cnts, _ = cv2.findContours(copper, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cnts, key=cv2.contourArea)
    pts = c.reshape(-1, 2).astype(float)
    # extreme points as rectangle corners
    ssum = pts.sum(1); diff = pts[:, 0] - pts[:, 1]
    tl = pts[np.argmin(ssum)]; br = pts[np.argmax(ssum)]
    tr = pts[np.argmax(diff)]; bl = pts[np.argmin(diff)]
    return np.array([tl, tr, br, bl], np.float32)

def rectify(img, src, W=2760, H=800):
    dst = np.array([[0, 0], [W, 0], [W, H], [0, H]], np.float32)
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (W, H))

def detect_holes(card, ymax=640):
    """Detect bright round holes on the card. Returns (x, y, radius)."""
    card = card[:ymax, :]
    gray = cv2.cvtColor(card, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    b = card[:, :, 0]
    # hole = bright in grey OR high blue channel (metal underneath); copper is reddish (blue low)
    mask = ((gray > 140) | (b > 112)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  np.ones((7, 7), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    H = []
    for c in cnts:
        a = cv2.contourArea(c)
        if a < 300:
            continue
        (x, y), rad = cv2.minEnclosingCircle(c)
        circ = a / (np.pi * rad * rad + 1e-6)   # 1.0 = perfect circle
        if circ < 0.42 or rad < 20 or rad > 45:  # allow partly covered ones, bound the size
            continue
        H.append([x, y, rad])
    # merge duplicates (<45 px apart)
    H = np.array(H) if H else np.zeros((0, 3))
    keep = []
    for p in H:
        if all(np.hypot(p[0]-q[0], p[1]-q[1]) > 45 for q in keep):
            keep.append(p)
    return np.array(keep)

def annotate(card, holes, rows_y=(219, 292, 355, 430, 494, 564)):
    vis = card[:640, :].copy()
    for x, y, rad in holes:
        cv2.circle(vis, (int(x), int(y)), int(rad), (0, 255, 0), 3)
        cv2.circle(vis, (int(x), int(y)), 2, (0, 0, 255), -1)
    for yc in rows_y:
        cv2.line(vis, (0, yc), (vis.shape[1], yc), (255, 120, 0), 1)
    return vis

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src_path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "out"
    os.makedirs(out, exist_ok=True)

    img = cv2.imread(src_path)
    if img is None:
        print("image not readable:", src_path); sys.exit(1)
    print("input:", img.shape)

    corners = find_plate_corners(img)
    print("plate corners (TL,TR,BR,BL):\n", corners.astype(int))

    rect = rectify(img, corners)
    cv2.imwrite(os.path.join(out, "01_plate_rectified.png"), rect)

    holes = detect_holes(rect)
    print("holes detected:", len(holes),
          "| median radius:", int(np.median(holes[:, 2])) if len(holes) else "-")

    vis = annotate(rect, holes)
    cv2.imwrite(os.path.join(out, "02_holes_annotated.png"), vis)
    np.savetxt(os.path.join(out, "03_hole_coordinates.csv"), holes,
               delimiter=",", header="x,y,radius", comments="", fmt="%.1f")

    # --- Next step (on flat scans): map onto the 00-89 contact grid ---
    # Rows = tens digit, columns = units digit. With a clean separation:
    #   ri = row-cluster(y);  ci = round((x-off)/pitch)
    #   cell = 10*ri + ci   -> list of activated cells per card
    # Deliberately NOT forced here, because the rows are ambiguous at this
    # resolution.
    print("\nDone. Results in:", out)
    print("NOTE: a cell/bit matrix is only dependable on flat 200 dpi scans.")

if __name__ == "__main__":
    main()
