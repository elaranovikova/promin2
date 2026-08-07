# Handoff v3: sources complete, card format read

**Date:** 2026-08-07 · **Status:** the gap in the material that v2 described as
a hard limit is closed. The complete card set is available as a flat 200 dpi
greyscale scan, and with a second, independent source the field format of the
cards has become readable.

---

## 0. What changed since v2

v2 ended at three problems, all of which hung on the one slanted museum
photograph: ambiguous row assignment, no clean column comb, covered holes. All
three are moot now that the flat scans are here.

On top of that came a source not yet known in v2: a photograph of the same card
in its **unpunched** state. On it the printed coding legend is fully readable;
on a punched card every hole covers exactly the information one needs.

## 1. Sources obtained

**`07_forum/`**: tools and the archived state from the forum *Полигон
призраков*:

| | |
|---|---|
| Topic 43656 "ЭВМ Проминь" | 91 posts, 9 pages, 55 files, 124.6 MB |
| Topic 13404 (documentation/hardware) | 6 posts |
| `Перфокарты_Проминь-2.rar` | 73.6 MB, **85 scans, 27 decks** |
| Textbook scan (PDF) | 14.9 MB, identical to the one in `02_manual/` |

The scans are 3400×2336 px greyscale, three cards per sheet, 200 dpi, exactly
what v2 named as the precondition.

From the uploader's `readme.txt` (Radon, November 2022): the cards arrived as a
shuffled stack and were sorted by him; the assignment to decks is therefore not
guaranteed. Three decks are demonstrably complete and marked `!_полная` (АУ,
РК, симпсон). Folder names come from the captions on the cards; numbers in
parentheses repeat the field «ВСЕГО КАРТ». He notes himself that the cards
carry only the algorithm; the operator types in every numeric value by hand.

**`08_tangible_media/`**: the unpunched aluminium card (2358×618 px),
cataloged as aluminum, 1963, Institute of Cybernetics Kiev.

## 2. The card format

The 30 columns of a card are organized in **groups of three**, one instruction
per group, so **10 instructions per card**. The weights are printed on the
unpunched card at every single position:

| Column of the group | Weights (row 1→5) | Meaning |
|---|---|---|
| 1 | 16 · 8 · 4 · 2 · 1 | operation code 0-31 |
| 2 | 5 · 2 · 1 · 1 · **1** | address digit tens (rows 1-4), **row 5 = hundreds** |
| 3 | 5 · 2 · 1 · 1 | address digit, units |

An instruction is therefore **operation + three-digit decimal address
(000-199)**. The textbook confirms every detail of that:

- p. 15: "Набор команды осуществляется тремя штеккерами (на перфокарте ей
  соответствует три столбца)": an instruction occupies three columns on the
  punched card.
- p. 16: for the plug matrix the same hundreds distinction is described as a
  digit *with or without a bar*: a two-digit address means hundreds 0.
- p. 17: the numeric code comes out as the sum of the digits that **remain** in
  each column after punching. That makes the polarity no longer an inference
  but established (see below).
- Table 5 (pp. 18-20) and table 6: the complete operation table with codes
  01-31, built into `06_scripts/decode_card.py`.

An **unused** instruction slot is not punched at all, so it leaves every
position standing and reads arithmetically as "Ост 199".

Also on the card: an upright column scale 1-30, a row of boxes 7-30 rotated by
180°, the hand-filled fields «КАРТА №» and «ВСЕГО КАРТ», and "+" marks at row 5
of columns 3 and 27, probably sign positions, but not yet resolved.

### On polarity, resolved

What is scored is the **unpunched** position: metal left standing carries its
weight, a hole clears it. At first that was only inferred statistically, and it
is now established by the textbook itself (p. 17, see above). Physically it
fits the metal card as a mask over contact pins: metal closes the contact, the
hole breaks it.

A first test on densely punched cards alone would almost have led to false
confidence here: both readings produce invalid digits, only in different places
(a uniform column always yields 10). Only the distribution across all 202 cards,
and then the sentence in the textbook, settled it.

### Three cross-checks, all of which work out

- **Jump targets:** all 226 jump instructions (БП, УП1, УП2, БПII) point to
  instruction numbers ≤ 159, exactly the instruction memory of the Промінь-2
  (000-159). With a wrong decoding, roughly a fifth would lie above that.
- **Address range:** all 1748 remaining addresses lie in the number memory
  000-199, with clusters in the constant ranges 080-099 and 180-199.
- **Code repertoire:** of 2020 instruction slots exactly *one* uses a code that
  table 5 does not know, so a single misdetection.

Frequencies over 1939 real instructions: Зп 25.1 %, Чт 22.8 %, Сл 5.8 %,
Умн 5.5 %, Ост 5.4 %, БП 5.4 %. Reading and writing together make up almost
half, the picture to expect for a single-address machine with one accumulator.

## 3. Tools

| Script | Purpose |
|---|---|
| `07_forum/forum_dump.py` | archive forum topics completely (JSON, Markdown, files) |
| `07_forum/yadisk_get.py` | download public Yandex.Disk shares |
| `06_scripts/extract_flat_scan.py` | scan → cards → hole matrix (5 × 30) |
| `06_scripts/decode_card.py` | hole matrix → instructions (operation + address) |

`06_scripts/extract_card.py` stays where it is, but is **unusable** on the flat
scans: it segments the card by copper color in HSV space and finds no contour
at all on a greyscale scan (a crash in `find_plate_corners`). Its docstring
claims otherwise; the claim is disproved.

A pass over the whole archive: **85 scans → 202 cards → 16,464 holes → 2020
instruction slots**, 84 of them empty. All 202 cards have 5 rows × 30 columns.

## 4. What is on the cards

202 cards yield **1939 real instructions** (81 slots are unused). They are
computing programs for an engineering calculator: read values from cells into
the accumulator, compute, write back, branch. The first ten instructions of the
deck `!_полная_АУ`, for instance, read:

```
 1  Чт   051     S := cell 051
 2  Зп   010     cell 010 := S
 3  Чт   000     S := cell 000
 4  Выч1 092     S := S - cell 092
 5  УП1  006     if S = 0, continue at instruction 006
 6  Ост  099     halt / print
 7  Зп   002     cell 002 := S
 8  Чт   087     S := cell 087        (constant 2)
 9  Сл   088     S := S + cell 088    (constant ½)
10  Зп   001     cell 001 := S
```

The deck names come from the captions on the cards and name the task: network
planning (`Сеть`), cost accounting (`Рассчёт себестоимости`), service life of
equipment (`Срок службы оборудования`), multifactor analysis, root mean square
deviation. So business and statistical computing tasks, with no system
software and no data: the operator typed numeric values in by hand, and the
cards carry only the algorithm.

## 5. The programs

All 27 decks are assembled and evaluated: **222 cards, 2138 instructions**,
listings and figures in [`../09_programs/`](../09_programs/). The order of the
cards rests on the scan order and is checked through the jump targets: 252 of
252 lie inside the instruction memory 000-159, 218 of them inside their own
deck. The outliers are exactly the decks whose folder name announces gaps.

Of the program "АУ" there are three physically different stacks, scanned
separately; their cards agree on **249 of 250** instructions. The one deviation
sits on the card with the worst grid fit in the deck. That gives an error rate
of roughly one misreading per 250 instructions.

## 6. What comes next

1. **Read the handwritten card numbers** («КАРТА №», «ВСЕГО КАРТ»). They are
   legible on every scan and would secure the order independently of the jump
   target statistics, especially for the decks with gaps.
2. **Settle code 19** (sh or СчП, see `09_programs/README.md`). A circuit
   diagram or an operating manual for the Промінь-2 would decide it; the
   Glushkov Institute in Kiev and the Severodonetsk plant come into question
   for that.
3. **Improve the grid fit** of the 27 conspicuous cards (`grid_deviation_px`
   > 12); the card detection probably takes in a shadow there.
4. An **interpreter** that executes a deck; the operation table is complete
   and the number format known. With it the programs could be made to compute
   again for the first time.
