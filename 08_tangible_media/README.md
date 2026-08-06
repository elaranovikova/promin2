# 08_tangible_media: source tangiblemediacollection.com

Retrieved on **2026-08-07**, all requests HTTP 200.

## What is the source?

*Tangible Media: A Historical Collection* (John Wallace,
tangiblemediacollection.com) is a private collection and online exhibition of
removable data media (punched cards, punched tape, piano rolls, magnetic media
...). The artifact page
<https://tangiblemediacollection.com/artifacts/promin-2> shows an **unpunched
aluminium program card for the Промінь / Промінь-2**.

License of the source: Creative Commons **BY-NC 4.0**, © John Wallace.

## Contents of this folder

| File | Contents |
| --- | --- |
| `promin-2.md` | running text + catalog fields of the artifact page, cleanly as Markdown |
| `manifest.csv` | url, local_file, bytes, sha256, content_type |
| `raw/promin-2.html` | raw HTML of the artifact page (5,397 B) |
| `raw/holes.html` | raw HTML of the category page "Holes" (523,004 B), contains the index entry with the differing date "c. 1963 – c. 1967" |
| `images/promin-2-1.jpg` | **the central photograph**: unpunched card, 2358 × 618 px, 1.41 MiB |
| `images/promin-2-tn.jpg` | thumbnail, 51 KiB (for completeness) |
| `documents/` | **empty**, the page links no PDF/ZIP/RAR or anything similar |

**4 files, 2,060,753 bytes ≈ 1.97 MiB.**

The photograph is available at the maximum resolution there is: the server
directory listing `/_images/punch-card/promin-2/` is open and holds exactly two
files (`promin-2-1.jpg` 1.4 M, `promin-2-tn.jpg` 51 K). There are no CDN size
parameters, no `srcset`, no `data-full`, no lightbox variant; the 2358 × 618 px
are the original.

---

## Relevance for reconstructing the card format

The page itself gives almost nothing in text (one paragraph of running text).
**The whole value sits in the photograph** `images/promin-2-1.jpg`: it shows an
*unused, unpunched* card, which means the complete printed **hole position
legend** is readable and uncovered. That is effectively a coding table.

### Evaluation of the photograph (own measurement, not from the website's text)

The following figures come from a pixel-accurate measurement of the photograph
(tick detection, column grid, ink density per position). They are a **finding
on the image**, not a statement of the website.

**Card geometry**
- A very elongated format, aspect ratio ≈ **3.82 : 1** (W : H).
- **30 hole columns**, a grid across the full width; the column pitch is ≈ 1/30
  of the width, the card height ≈ 7.8 column pitches.
- No scale in the image -> absolute measurements in mm cannot be derived.

**Column grouping**
The measured column spacings are *not* uniform but periodic with period 3 (in
pixels: 82 / 66 / 81 ...). Columns 2+3, 5+6, 8+9 ... sit closer together than
the rest. The grid therefore falls into **10 groups of three**:

    [ column 3k+1 ] [ column 3k+2  column 3k+3 ]
      (wider)         (tight pair)

**Hole positions (5 rows, weights from top to bottom)**

| Column type | Columns | Row 1 | Row 2 | Row 3 | Row 4 | Row 5 | Range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A (binary) | 1, 4, 7, 10, ... 28 | **16** | **8** | **4** | **2** | **1** | 0-31, pure binary weights |
| B (decimal) | 2, 5, 8, ... 29 | **5** | **2** | **1** | **1** | **1** | 5-2-1-1-1 |
| C (decimal) | 3, 6, 9, ... 30 | **5** | **2** | **1** | **1** | n/a | 5-2-1-1 (only 4 positions) |

- Rows 1-4 are occupied in **all 30 columns**.
- Row 5 is missing in exactly the columns ≡ 0 mod 3 (3, 6, 9 ... 30).
- **Special mark:** in the place of row 5, **column 3** and **column 27** carry
  a printed "**+**" (not a circle), very probably a **sign position**. The
  remaining C columns (6, 9, 12, 15, 18, 21, 24, 30) are empty there.
- In total 10 × (5 + 5 + 4) = **140 hole positions** + 2 sign positions.

**The most important conclusion:** the card mixes **two codes**. Columns 3k+1
carry a pure **5-bit binary field (0-31)**, columns 3k+2 / 3k+3 a
**5-2-1-1 decimal field (digit 0-9)** of the usual Soviet kind, grouped in
pairs. The obvious reading of a group of three is therefore:

> **operation code (0-31, binary) + two-digit decimal address/operand (00-99)**
> -> **10 such groups per card.**

(That fits the program capacity of 100 instructions often quoted for the
Промінь: 10 cards × 10 instructions. A **hypothesis**, not established.)

### Printing in the head and foot areas

| Element | Position | Orientation | Text |
| --- | --- | --- | --- |
| Column scale | top edge, columns 1-30 | **upright** | `1 ... 30` |
| Row of boxes | above columns **1-24**, one box per column | **rotated 180°** | `7, 8, 9, ... 30` |
| Field beside it | above columns **25-30** | **upright** | `КАРТА №` ("card no.") |
| Below that | above columns ~25-30 | **upright** | `ВСЕГО КАРТ` ("cards in total") |
| Bracket + scale | below row 5, columns **10-16** | **rotated 180°** | `1, 2, 3, 4, 5, 6, 7` |

Verified: `КАРТА №` and `ВСЕГО КАРТ` are **upright** in the photographed state
(rotating the crop by 180° gives nonsense). The box numbers, by contrast, are
clearly rotated: "10" appears as a mirrored "0I" and "30" as "0E", but the
reading order of the boxes stays left to right, ascending.

**Open points / lines of interpretation** (deliberately marked as questions):

1. **Why does the row of boxes start at 7?** There are 24 numbered boxes
   (7-30) above columns 1-24, while columns 25-30 are taken by the field
   `КАРТА № / ВСЕГО КАРТ`. The obvious idea: the machine addresses 30
   "positions", of which 1-6 are the card identification (physically columns
   25-30) and 7-30 the payload (physically columns 1-24). But the direction of
   that mapping does not work out cleanly; original documentation is needed
   here.
2. **The meaning of the 1-7 scale under columns 10-16.** Seven positions, tied
   together by a bracket line at the height of row 5. Candidates: the position
   of the decimal point / the exponent (порядок) of a number, the number of
   mantissa digits, or a selection of one of 7 modes. Unresolved.
3. **Why "+" only in columns 3 and 27?** If it is a sign: there would be
   exactly two signed fields per card: group 1 (columns 1-3) and group 9
   (columns 25-27). That contradicts the "10 instructions of the same kind"
   reading and argues rather for a mixed card structure (data field +
   identification field).
4. **Card identification in plain text or punched?** Under `КАРТА №` /
   `ВСЕГО КАРТ` sit the same hole circles as everywhere else; whether they are
   punched there or filled in by hand cannot be decided on the unpunched
   specimen.

### What the source does **not** provide

- No console photographs, no machine photographs, no manual pages.
- No dimensions (length/width/thickness, hole diameter, hole spacing in mm).
- No information on the reading principle (mechanical/contact pins/optical).
- No reverse side of the card, no second specimen, no punched card.
- No sources or literature, no note on provenance.

## Notes on crawling

- Crawled politely, few requests with pauses, an ordinary browser user agent.
- The site's `robots.txt` restricts only `Googlebot-Image` and does **not**
  cover `/_images/punch-card/`.
- `sitemap.xml` does not exist (HTTP 404).
- Checked and **not** taken over: `artifacts/soviet-signal-card.html`; despite
  the name it has nothing to do with computers (the Soviet tube tester Kalibr
  L1-3/L3-3). No further Soviet or Ukrainian artifacts are present in the
  collection (the whole "Holes" category and the image directory
  `/_images/punch-card/` were searched).
