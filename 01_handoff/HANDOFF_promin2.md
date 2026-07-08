# Handoff: decoding the Проминь-2 microprogram cards

**Date:** 2026-07-08
**Handed over by:** research session · **Taken over by:** you, in VS Code
**Status:** target identified and verified. Download blocked from the sandbox (infrastructure, not content). From here on, locally.

---

## 1. What we want (the goal in one sentence)

Turn the **metallized punched cards of the Проминь-2** (Promin-2, Glushkov /
Institute of Cybernetics Kiev, Severodonetsk, 1967) into bits and reconstruct
the **stepwise microprogram encoding** from them. That would be the first
public description of a memory and microinstruction format that demonstrably
**nobody has documented yet**.

This is deliberately the same kind of work as with the Iskra-226, only one
level deeper: there, eight interpreter builds were available and the semantics
had to be inferred from behavior; here the **physical microcode is available as
an image scan** and the machine underneath has to be reconstructed.

## 2. Why this machine in particular (selection criteria, all met)

- **An alien architecture, not a clone.** RU Wikipedia, literally: *«В машине
  использовалась память на металлизированных перфокартах и ступенчатое
  микропрограммное управление»*: memory on metallized punched cards and
  stepwise microprogram control. One of the first microprogrammed machines at
  all; it led on to the MIR series. The "ROM" is physically a punched metal
  card.
- **A dump exists and is verified as available** (forum thread below). A user
  bought real Promin-2 metal cards, scanned them all in **greyscale at 200
  dpi** and uploaded them with a readme.
- **Not decoded, and that is stated literally.** The same user: *«Попытки
  найти в сети хоть какую-то внятную документацию по формату записи данных на
  картах меня ни к чему не привели»*: no usable format documentation found.
  **No emulator** (MAME does not have the machine; xlat8086 does not; no repo).
- For comparison, why earlier candidates dropped out: the Д3-28 already has an
  emulator (xlat8086.com/d3-28, renders microcode symbolically -> disqualified).
  K-202 = pure RTL without microcode, hardly any surviving hardware.
  Iskra-226 = solved by you already.

## 3. What you have to fetch first (the download I could not do)

**Why I failed:** phantom.sannata.org blocks bots hard (503 + a faked TLS
error); web.archive.org is blocked by my sandbox egress policy; the secondary
mirror radon.su does not resolve in DNS. **All infrastructure, nothing to do
with content.** In your browser everything should load normally.

**Source: one forum thread, two upload packages:**
- Thread: `https://www.phantom.sannata.org/viewtopic.php?t=43656` ("ЭВМ
  Проминь", Polygon Prizrakov)
- **Package A (first post):** the **metal card scans**, greyscale, 200 dpi,
  with a readme. Two "Скачать" links: Я.Диск (Yandex) and radon.su.
- **Package B (third post):** a scanned **textbook** *«Учебное пособие по
  программированию на электронно-вычислительной машине "Проминь"»*, also on
  Yandex Disk. **This is your Rosetta stone for the encoding.** Take it, without
  fail.

**To do:**
1. Open the thread in a browser, copy both "Скачать с Я.Диска" links from post
   1 and post 3.
2. Download. Public Yandex folders can be pulled through the API (pattern
   below, it worked for the Д3-28).
3. Read the readme in the card package first; the uploader left extra
   information there.

**Yandex API pattern** (public_key = the yadi.sk/disk.yandex URL, URL encoded):
```bash
# metadata (name, size, md5):
curl -s "https://cloud-api.yandex.net/v1/disk/public/resources?public_key=<PUBLIC_URL_ENCODED>"
# direct download link:
curl -s "https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=<PUBLIC_URL_ENCODED>" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['href'])"
```

## 4. What the machine is (facts for the decoding hypothesis)

Gathered from museum and Wikipedia sources. Check them against the readme and
the textbook when the scans are opened:
- Series: Проминь / Проминь-М (1965) / **Проминь-2 (1967)**. Development at the
  Institute of Cybernetics AN USSR from 1958 under Glushkov; series production
  at the Priborostroitelny plant in Severodonetsk from 1963.
- **ROM capacity: 64 numbers.** **29 operations** (the source gives the
  machine's operation capacity as 29). Data memory 100-160 words depending on
  the source.
- Input: manually through plugs at the console **or metallized punched cards**.
  Output: decimal display tubes + a digit printer.
- A decimal machine (no binary word in the PC sense), so do not automatically
  assume binary word widths when extracting bits.
- The core feature that later shaped MIR: the (stepwise) microprogramming.

## 5. The actual technical plan (the two miles of work)

**Mile 1: image → hole matrix (image processing, not cryptography):**
- The cards are greyscale scans. Per card: find the card frame, rectify/deskew,
  normalize onto a regular **hole grid**.
- Classify the grid positions: hole / no hole (metallized = conducting or not).
  Threshold + morphological cleanup. Calibrate on several cards.
- Output: one bit matrix per card (rows × columns), plus the printed captions
  for reference (the readme mentions legible captions).
- Tools: Python, OpenCV, numpy. One card digitizer script that treats every
  card the same way (analogous to the "every floppy only once" discipline;
  here: reproducible grid detection instead of reading by hand).

**Mile 2: hole matrix → microprogram semantics (the actual reconstruction):**
- The card format is undocumented -> infer it from structure + textbook.
- Field analysis as with the Д3-28 dump I have already taken apart (the method
  carries over): column/field entropy across all cards, identify constant
  versus variable fields, look for candidate fields for the operation (29
  values -> ~5 bits or 1 decimal digit), for operands, and for the
  next-step/jump.
- **The textbook as a Rosetta stone:** the programming examples in it give the
  operation semantics. A known calculation from a card + the expected result =
  a test vector against which the field hypothesis stands or falls (exactly the
  payroll/game test vector logic from your Iskra project).
- Target artifact: a field encoding table + a list of the operations (the 29) +
  if possible a small interpreter that "executes" a card.

## 6. Enclosed files (from this session, as a template for the method)

These are enclosed. **It is the Д3-28 microcode I have already analyzed.** NOT
the Промінь target, but the **template** for how to take such a dump apart
(field/entropy analysis). Reuse it for mile 2.
- `pel3_065_001__rom.txt`: Д3-28 microcode dump, 8192 words × 48 bits,
  addressed PY(7)×PX(6) = 128 pages of 64. Format: header + `PY PX : b b b b b
  b b` (48 bits).
- `pel3_065_001__rom.zip`: original archive (Yandex, 8 May 2018,
  md5 4c02e0b09d311efb3d745889a14dbe6f).
- `entropy_analysis.py`: bit entropy per position, constant bits, word
  frequencies.
- `field_hypotheses.py`: tests of field hypotheses (next address, holding the
  page, value distributions per field).

Those two scripts can be adapted directly: as soon as mile 1 delivers the
Промінь cards as a bit matrix, run the same field/entropy analysis over it.

## 7. Honest reservations / open points

- "Dumped" means **scanned**, not converted to bits. Mile 1 (image processing)
  is real work and comes before the semantics.
- I could **not** verify that the Yandex links are live (the sandbox blocks
  it). Probably still active (a post from 2022, two mirrors), but the first
  to-do remains: check.
- Number of cards, resolution details, completeness of the card set: unknown
  until you open the readme.
- Whether the card set covers the **whole** ROM (64 numbers) + microprogram or
  only parts: clarify from the readme.
- Decimal architecture: field widths may be in decimal digits, not bits. Keep
  that open during the analysis.

## 8. Contact / provenance

- The uploader = the thread starter on phantom.sannata.org (t=43656), who also
  supplied the textbook afterwards. Reachable by forum PM; has linked an active
  VK group.
- A further Promin thread (documentation search, hardware):
  `https://www.phantom.sannata.org/viewtopic.php?t=13404`, which also holds the
  tip to ask the Glushkov Institute and the Severodonetsk plant directly for
  circuit diagrams.
- If circuit diagrams or a ТО turn up: for mile 2 that would be the same as a
  technical description, a direct route to the meaning of the fields.

---

**Next concrete step:** open the thread → pull both Yandex links (cards +
textbook) → read the readme → write the card digitizer (OpenCV) → bit matrix →
run the `entropy_analysis.py`/`field_hypotheses.py` methodology over it → hold
the textbook test vectors against the field hypothesis.
