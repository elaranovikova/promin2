# Handoff v2: decoding the Проминь-2, material reviewed

**Date:** 2026-07-15 · **Status:** the files are here and have been gone through. The number format, the memory layout and part of the operation set have already been read out of the textbook. From here on: digitize the cards + reconstruct the format, locally in VS Code.

---

## 0. What changed since v1

I opened the uploaded files. Two important corrections and several solid facts
have been added:

- **It is the Проминь-2, and it has 32 operations** (not 29; that was a figure
  for an older model). Textbook p. 4, literally: *«отличается от неё большей
  числовой и программной памятью. Кроме того, выполняет 32 операции»*.
- **The textbook is first rate and fully legible**: Asnina / Bibikova /
  Zlatomreva, *«Учебное пособие по программированию на ЭВМ "Проминь"»*,
  University of Voronezh 1973, a 53-page scan. That is the Rosetta stone.
- The number format and the memory structure are in it **already** (see §3), so
  you no longer have to guess those.
- Part of the image uploads is NOT relevant to the cards (a typewriter manual,
  photographs of the internal mechanics, wide museum shots). The usable files
  are named individually below.

## 1. Goal (unchanged)

Turn the metallized punched cards of the Проминь-2 into bits and reconstruct
the **undocumented card format / the microprogram and instruction encoding**.
No emulator exists, no format documentation exists (the uploader confirms that
himself). The result would be the first public description.

## 2. The usable files (in the folder `packages/`)

- **`karte_kupfer_KARTA-N4.jpg`** (3840×2160), THE key file. A real punched
  **copper metal card** lies on the plug/read grid of the machine, sharp, with
  the caption "КАРТА N 4". The rows of holes are clearly visible. The grid
  underneath is numbered 00-89 (cell addresses), and next to it lie a reference
  reading plate with circled digits and a ruler. **That is enough for a first
  digitizer prototype.**
- **`operationstasten_1.jpg` / `operationstasten_2.jpg`** (4000×2000), the
  complete **operation key registers** of the machine with Cyrillic mnemonics:
  among them Сл (сложение), Дел (деление), Умн (умножение), Чт (чтение?), БП
  (безусловный переход), Зп (запись), Фр, СчП, Дсп, Вык2, plus digit keys 0-9
  and special characters (*). That is the visual list of the ~32 operations, and
  their codes are in the textbook (ch. 1).
- **`pult_museum.jpg`** (1900×1267), the operator console of a real Проминь in
  a museum. It confirms the number format physically: labeled display windows
  **АДРЕС · ЗНАК ПОР · ПОРЯДОК · ЗНАК МАНТ · МАНТИССА**, and on the right the
  slanted card slots.
- **`Uchebnoe_posobie_po_programmirovaniyu_EVM_Promin.pdf`** (53 pp., a scan,
  no text layer), the textbook. It has to be OCRed or rendered page by page
  (PyMuPDF, matrix 2.2-2.4 gives nicely legible PNGs).

NOT relevant (ignore): `IMG_20230726_152611/152722/152844` (that is a
*typewriter* manual, "Машины пишущие электроуправляемые", the wrong apparatus),
`IMG-0594`, `IMG_20230724_*` (internal mechanics, casing), `smg_5665`,
`Промінь-М общ вид/шильд` (wide museum shots, the type plate), `Promin-2.jpg`
(a small press photograph). The LiveJournal PDF is popular background text.

## 3. What the textbook already delivers (read from the rendered pages)

**Number format (ch. 1, §3 "Представление числовой информации"):**
- A semi-logarithmic, normalized **decimal floating point number**: N = M·10^P.
- Storage: **1 decimal digit for the exponent P**, **5 decimal digits for the
  mantissa M**, plus **2 binary positions for the signs** of exponent and
  mantissa. The mantissa sign is the sign of the number.
- Normalized means 0.1 ≤ |M| < 1. Examples from the text: +0.20111·10² is
  normalized; 0.000114·10^5 is not.
- The input field = **8 vertical columns**: columns 1 and 3 = sign keys (±) for
  the exponent and the mantissa; column 2 = the 10 digits of the exponent;
  columns 4-8 = 10 digits each for the five mantissa positions. The illuminated
  panel has the same structure.
- **IMPORTANT for extracting bits:** this is a **decimal machine**. Digits are
  probably punched as a "1 of 10" / positional code, not as a binary word. The
  double page on p. 6 already shows digit bit patterns (7, 8, 9 with columns of
  0/1); the concrete digit→hole encoding is there. Render that table in full
  and read it off first.

**Memory structure of the Проминь-2 (ch. 1, §4 "Запоминающее устройство
чисел"):**
- **320 number cells: 200 permitted + 120 blocked (запрещённые, marked with
  ")**.
- Of those, **226 operational, 65 constant cells, 28 for elementary
  functions**.
- Constant cells with addresses (table 3), among them: 80 = the integer
  constant 0.00000·10^5; 81 = π (3.1416); 82 = 2π; 83 = 1/π; 84 = 1/2π;
  85 = π/2; 86 = 1; 87 = 2; 88 = ½; 89 = ¼; **90 = the address unit
  1A = +0.00100**; 92 = ln10; 94 = 180/π (degrees↔radians) and so on.
- Cell addresses are **two-digit decimal** (00-99 in the base group; the card
  grid in the photograph is numbered exactly that way, 00...89).

**Chapter structure (7 chapters, from the preface):**
1. The machine, the **instruction system, the constant system** ← the operation
   codes are here
2.-4. Programming basics, branches, loops
5. Matrix operations
6.-7. **«способы записи команд в ОЗУ и использования запрещённых ячеек»** ←
   this is where it says how instructions are encoded in memory = directly
   relevant to the cards

**To do on the textbook:** render chapter 1 in full and read off the
**operation table with the codes** (32 operations). Then chapters 6-7 for the
instruction-in-memory encoding. Those are your test vectors.

## 4. The technical plan

**Mile 1: card → bit matrix (image processing):**
- Start with `karte_kupfer_KARTA-N4.jpg`. Cut the card out, rectify it (the
  card lies slightly rotated on the grid).
- Determine the hole grid: count the rows/columns of holes from the
  photograph. Several rows of holes are visible along the length of the card,
  and that probably corresponds to the 8 field columns × digit positions per
  stored number, plus an address/instruction part. Validate against the
  description of the number format (§3).
- Classify hole / no hole (bright openings versus copper surface -> high
  contrast, a simple threshold + morphology).
- Output: one bit matrix per card + the stamped card number as a label.
- OpenCV/numpy. One script that treats every card identically (reproducible,
  not read by hand).
- **Careful:** at the moment only ONE sharp card is available. Real format
  reconstruction needs more cards. Ask the uploader (see §6) for the complete
  set of scans; he scanned "довольно большое количество" cards and put them up
  as a Yandex/radon package.

**Mile 2: bit matrix → semantics:**
- Think in decimal: the fields are probably organized in decimal digits
  (exponent 1, mantissa 5, signs 2), not in binary word widths.
- Apply the digit hole code from p. 6 of the textbook as a decoding table ->
  translate every card row into a number/address/operation.
- Field and position analysis across several cards (method template: the
  enclosed `entropy_analysis.py`/`field_hypotheses.py` from the Д3-28 analysis:
  entropy per position, constant versus variable fields, candidate fields for
  operation/address).
- **Test vector logic as in your Iskra project:** a program from the textbook
  (ch. 6-7 shows instructions in memory) + the expected behavior -> hold it
  against the card as read. Does the encoding hypothesis hold, if the card
  yields the documented program?
- Target artifact: a specification of the card format + an operation table (32)
  + optionally an interpreter that "executes" a card.

## 5. Enclosed method template (Д3-28)

`pel3_065_001__rom.txt` + `entropy_analysis.py` + `field_hypotheses.py` from the
previous session. NOT the target, but the template for how to take such a dump
apart by field/entropy analysis. Adapt it for mile 2.

## 6. Source / contact / what is still to be obtained

- Thread: `https://www.phantom.sannata.org/viewtopic.php?t=43656` ("ЭВМ
  Проминь", Polygon Prizrakov). It holds the complete card scans (Yandex +
  radon.su) and the textbook. **You have a part of it; fetch the complete card
  package**; the whole scanned card set is the basis for mile 2.
- The uploader is reachable by forum PM; he has an active VK group. He says
  himself that the card format is documented nowhere, which means your
  reconstruction would be the first.
- The documentation/hardware thread, with the tip to ask the Glushkov Institute
  (Kiev) and the Severodonetsk plant directly for circuit diagrams or a ТО:
  `https://www.phantom.sannata.org/viewtopic.php?t=13404`.

## 7. Honest reservations

- "Dumped" means **scanned**. Mile 1 (image → bits) is real work and comes
  before the semantics.
- Only **one** sharp card in the current upload -> format reconstruction needs
  the full set (§6).
- Decimal architecture: field widths in decimal digits, not bits. Keep that
  open during the analysis.
- I could not check from the sandbox that the Yandex/radon links are live
  (egress blocks web.archive.org and radon.su, and the forum blocks bots). In
  your browser everything should work.
- Whether the card set covers the **whole** program/constant ROM or only
  individual cards: clarify from the readme of the card package.

---

**Next step:** (1) render textbook ch. 1 → read off the operation table (32
codes); p. 6 → the digit hole encoding. (2) Cut out
`karte_kupfer_KARTA-N4.jpg`, detect the grid, produce a first bit matrix.
(3) Fetch the complete card set from the uploader. (4) Run the
`entropy_analysis.py`/`field_hypotheses.py` methodology on the matrices.
(5) Hold the textbook programs (ch. 6-7) against the cards as read, as test
vectors.
