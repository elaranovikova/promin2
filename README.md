# Промінь-2: reading the punched metal cards

Reconstruction of the undocumented card and instruction format of the Soviet
**ЭВМ Промінь-2** (Glushkov's Institute of Cybernetics, Kyiv; built in
Severodonetsk, 1967). One of the first microprogrammed computers ever made, and
one where the "ROM" is a physical punched metal card. There is no emulator and
no published description of the format.

The chain this project builds: punched metal cards → bits and cell addresses →
instruction and constant format. As far as I can tell it is the first public
description of any of it.

## Where the project stands

Authoritative document: `01_handoff/HANDOFF_promin2_v3.md`.

**Read and confirmed**

* **Card format.** 30 columns in groups of three, one instruction per group:
  an operation code with weights 16·8·4·2·1 (so 0–31) and a two-digit decimal
  address with weights 5·2·1·1·1 and 5·2·1·1. Ten instructions per card.
* **Number format.** Decimal floating point, N = M·10^P: one exponent digit,
  five mantissa digits, two sign bits, eight input columns.
* **The machine.** 32 operations, 320 cells, a constant table with addresses.
* **The run.** 85 scans → 222 cards → 18 085 holes → 2138 instructions across
  27 decks.
* **Cross-check.** All 252 jump targets land inside instruction memory 000–159.
  Of the program "АУ" three separately scanned stacks exist, and their cards
  agree on 249 of 250 instructions.

**Still open**

* **Polarity.** Whether metal or hole counts as the set bit is well supported
  but not proven. The argument and the counter-test are in handoff v3.
* **Code 19.** Table 5 covers the Промінь-М and lists it as sh. For the
  Промінь-2, table 6 names the extra instruction СчП but leaves its code column
  empty. The way the cards use it argues for СчП, see `09_programs/`.
* The "+" marks at row 5 of columns 3 and 27 are unexplained.
* Card order rests on scan order. The handwritten «КАРТА №» fields have not
  been read yet, and the uploader says himself that he sorted the stacks.

The earlier hard limit (ambiguous rows, no clean column comb) came entirely
from the one slanted museum photograph and disappeared with the flat scans.

## What is in here

| | |
|---|---|
| `01_handoff/` | three handoff documents; **v3 is the authoritative one** |
| `04_extraction/` | results from the single photograph: rectified plate, 64 detected holes annotated, hole coordinates as CSV |
| `05_method_d328/` | **a template, not the target.** The already dumped Д3-28 microcode with the field and entropy analysis that took it apart, as a pattern for doing the same here |
| `06_scripts/` | `extract_flat_scan.py` scan → cards → 5×30 hole matrix; `decode_card.py` matrix → instructions |
| `08_tangible_media/` | photograph of an **unpunched** aluminium card of the same build. Because no hole covers anything, the printed coding legend on it is fully readable. This is the key to the format |
| `09_programs/` | the reconstructed programs, one numbered instruction band per deck with jump targets marked. 27 decks, 222 cards, 2138 instructions |
| `10_emulator/` | faithful emulator: decimal five-digit accumulator arithmetic, СчП loops, indirect addressing, constant cells, range halts. Runs the reconstructed decks and hand-written programs, 23 tests against passages from the textbook |

`06_scripts/extract_card.py` is the old pipeline for the slanted colour
photograph and is **unusable** on the flat scans: it segments the card by copper
colour in HSV space and finds no contour at all on a greyscale scan. Its
docstring claims otherwise; the claim is disproved.

## Next steps

1. Render chapter 1 of the textbook in full and read off the **operation table**
   with all 32 codes. Only then do "op 7" and "op 6" become named instructions.
2. Hold a **test vector** from chapters 6–7 against a card that has been read.
   That settles the polarity question and checks the field layout as a whole.
3. Verify deck order against the handwritten «КАРТА №» and «ВСЕГО КАРТ» fields.
4. Field and entropy analysis using the template in `05_method_d328/`, now with
   2020 instructions to work from.

## Source material

The bulky sources are not in this repository, because they are other people's
scans and photographs and they run to 629 MB. What *is* here is what I decoded
out of them; see "Credits and rights" below. They sit next to it under
`../research/`:

* `02_manual/`: Asnina, Bibikova and Zlatomreva, *Textbook for programming the
  ЭВМ "Промінь"*, University of Voronezh 1973. A 53-page scan with no text
  layer, plus the key pages rendered legibly. This is the Rosetta stone.
* `03_photos_cards/`: the punched copper card on the machine's numbered
  contact grid, the operation key registers with their Cyrillic mnemonics, and
  the museum console, which confirms the number format physically.
* `07_forum/`: tools and the archived state of both threads.

Threads: `phantom.sannata.org/viewtopic.php?t=43656` for the card scans and the
textbook, `t=13404` for documentation and hardware. The unpunched card is at
`tangiblemediacollection.com/artifacts/promin-2`.

## Credits and rights

Almost none of this would exist without material other people made available.
Named in the order in which the project leans on them:

* **The card scans, from Radon.** He bought the punched metal cards, scanned
  all of them at 200 dpi in greyscale and posted them in November 2022 in the
  thread `phantom.sannata.org/viewtopic.php?t=43656`, as
  `Перфокарты_Проминь-2.rar` (73.6 MB, 85 scans, 27 decks) with a readme
  explaining how he sorted the stacks. **Everything this repository claims
  about the cards is derived from those scans**: the hole patterns of all 222
  cards in `10_emulator/web/decks.js` and the instruction bands in
  `09_programs/` are decoded from his files. The scans themselves are not
  redistributed here.
* **The textbook.** Asnina, Bibikova and Zlatomreva, *«Учебное пособие по
  программированию на ЭВМ "Проминь"»*, University of Voronezh 1973, 53 pages,
  scanned and posted in the same thread. Every instruction name and every
  constant in this repository is read out of it. Not redistributed here.
* **The unpunched card, from John Wallace**, *Tangible Media: A Historical
  Collection*, `tangiblemediacollection.com/artifacts/promin-2`. His photograph
  shows the printed coding legend uncovered and is the key to the whole format.
  `08_tangible_media/images/` and `08_tangible_media/raw/` are copies of that
  page, retrieved 2026-08-07 and used under **Creative Commons BY-NC 4.0**
  (© John Wallace): attribution required, no commercial use. This is the one
  piece of other people's material that this repository does carry.
* **The Д3-28 microcode dump** in `05_method_d328/` (`pel3_065_001__rom.txt`
  and `.zip`) comes from a public Yandex.Disk archive dated 8 May 2018
  (md5 `4c02e0b09d311efb3d745889a14dbe6f`); I do not know who dumped it. It is
  kept here only as a worked template for the field and entropy analysis, not
  as material about the Промінь.
* **The photographs** under `../research/03_photos_cards/` come from members of
  the two threads above: the copper card on the machine's contact grid, the
  operation key registers, the museum console. Not redistributed here.

The forum uploads carry no stated license. I use them for documentation and
research and name the source at every point where they matter. If you
contributed any of this material and want it taken out, write to
elara@elaranovikova.com and it goes.

The code, the extraction and decoding scripts, the reconstructed listings and
the emulator are my own work.

## The web emulator

`10_emulator/web/` is the browser build. The version published at
`elaranovikova.com/projects/promin-2/` has moved on from it and is the one to
look at for anything user-facing; this copy is the one the tests run against.
