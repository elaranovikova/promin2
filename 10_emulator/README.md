# 10_emulator: emulator of the ЭВМ Промінь-2

As far as this project can tell, the first emulator of this machine at all (in
2022 the uploader of the card scans confirms in the forum that none exists). It
runs both the reconstructed card decks and your own programs in a simple
assembler format.

## Web interface (`web/`)

Open `web/index.html` in a browser. No installation, no server, no external
dependencies. It contains:

- **Punch card view**: every card of the selected deck as an aluminium card
  with its hole pattern, the printed weight digits (16/8/4/2/1 and 5/2/1/1),
  the column scale and «КАРТА №»; the instruction currently executing (three
  columns) is highlighted.
- **Operator console** in the style of the machine: АДРЕС · ЗНАК ПОР ·
  ПОРЯДОК · ЗНАК МАНТ · МАНТИССА, plus the accumulator in decimal.
- **Instruction band** (disassembler with jump target marks and a PC line),
  **number memory** 000-199 (constants yellow, changed cells green, clicking a
  cell shows the machine word with its address field and counter) and a
  **halt/message log**.
- Controls: start/pause, single step, speed (default: 1 instruction per 2.5 s,
  slow enough to follow every instruction; up to ~12,000 instructions/s),
  "pause on Ост", code 19 switch, inputs as at the console
  (`51=3.5` or `10=raw:-00095`).
- **The holes of the active instruction flash** briefly at every step, and you
  watch the machine scanning the card.
- **Progress band**: one segment per instruction slot, grouped by card.
  Executed slots take on color (green = once, yellow = several times, red =
  loop hotspot), the current instruction glows, and the coverage is given as a
  percentage. Coverage rather than a bar filling from the left, deliberately:
  for programs with loops, "how much of the program has run" is the honest
  measure of progress.
- **Two languages** (EN default · RU) and **three color schemes**: dark,
  Soviet red (with copper colored cards like the original of КАРТА N4) and
  light. Language and scheme are remembered in the browser.
- Embedded are **all 27 reconstructed decks** (222 cards) plus the example
  programs, which are drawn as synthetic punch cards as well.

The JavaScript core is a direct port of `promin2_emu.py` (the same
digit-faithful arithmetic, the same assumptions). `web/decks.js` is generated
by `web/build_data.py` from an extraction folder.

```bash
# run a reconstructed deck (folder with *_matrix.csv from extract_flat_scan.py)
python3 promin2_emu.py --deck <folder> --set 51=3.5

# your own program
python3 promin2_emu.py --program examples/circumference.asm --set 51=1.5
python3 promin2_emu.py --program examples/sum_loop.asm --set-raw 10=-00095

# tests (23 checks against the documented machine behavior)
python3 test_emu.py
```

## What is reproduced digit by digit

The emulator does not compute with the host machine's floating point numbers,
it reproduces the decimal arithmetic of the machine digit by digit: mantissa 5
decimal digits, exponent 1 decimal digit, one sign each; adding means
**align to the larger exponent -> add -> truncate -> normalize**. That makes
the documented quirks come out exactly right too:

- **The Сл-080 trick** (textbook p. 21): adding the constant 0.00000·10^5
  forces exponent 5 and yields the integer part. It works only because a zero
  takes part in the alignment with its own exponent; the flip side is the
  machine zero described on p. 8.
- **Fixed-point address arithmetic** (pp. 22-23): Слф/Вычф add mantissas
  unaligned and unnormalized; the address unit 1A = +0.00100 raises the address
  field (digits V, IV, III) by 1.
- **Indirect addressing** (codes 11-13): the address comes from mantissa
  digits V, IV, III of the named cell.
- **СчП loops** (table 6): a counter word with a minus sign and the counter
  100−N in digits II, I; the carry on reaching 100 sets the sign to + and so
  ends the backward «УП2» loop.
- **Range halts** (table 5, column «Аварийный останов»): division by 0,
  exponent overflow ≥10^9, √ of a negative, ln(≤0), |argument|≥22 for
  exp/sh/ch, |argument|>1 for asin/acos.
- **Constant cells** (tables 3+4, loaded in full: 080-099 and 180-199) are
  write protected; attempts to write are logged and ignored (p. 13: «не могут
  быть использованы для записи»).
- **An unpunched instruction slot** (= Ост 199) ends the run, and that is how
  the real machine stopped when it ran into unprogrammed territory.
- **A slot punched out completely** (op 0, every hole of the three columns):
  that is how an instruction was deleted from the card after the fact: no
  metal, no contact. It is skipped as a NOP and counted. (46 such slots in the
  archive, 28 of them with address 000, in clusters, so the cards were edited.)

## Deliberate assumptions (not handed down)

1. **Rounding = truncation.** The machine's rounding rule is described
   nowhere; truncation is the most likely choice for the period.
   Multiplication normalizes from the full 10-digit product register before
   truncating.
2. **Code 19 = СчП** (argued in `09_programs/README.md`); with `--code19 sh`
   it computes the hyperbolic sine as in table 5.
3. **СчП also leaves its result in the accumulator**: the cards consistently
   show the pattern «СчП, conditional jump directly after», which works only
   that way.
4. **Ост** logs the halt and the accumulator and carries on (like an operator
   pressing start again); `--stop-after-halts N` stops earlier.
5. **Keyboard input** («Чт 5Ж», p. 21) is not emulated, because its hole
   encoding is unknown, so inputs are placed into cells beforehand, as at the
   console: `--set cell=value` (normalized) or `--set-raw cell=-00095` (a raw
   digit pattern for address and counter words).
6. Constant cell **182**: the scan is ambiguous (0.00200/0.00300); it is set to
   3A = 0.00300, as the column caption «тройка в адресной форме» requires.

## Validation

- `test_emu.py`: 23 checks, each against a specific passage of the textbook
  (normalization, truncation of 1/3, Сл-080, 1A arithmetic, ЧтII through the
  address field, УП1/УП2, a СчП loop with exactly N passes, Фр, range halts,
  write protection, end of program, the code 19 switch).
- **Smoke run over all 27 reconstructed decks**: not a single internal error;
  every deck ends in a way the machine makes sense of. Without operator inputs
  many runs end in the аварийный останов as expected (ln(0), division by 0,
  uninitialized pointer cells), which is exactly what the real machine would
  do.
- The АУ test deck (arithmetic unit test) passes several of its checkpoints
  with S = 0 ("passed") on empty input cells, and halts per check with the
  documented error halt pattern Ост 099.

## Limits

- The semantics of the input and printing peripherals are only partly handed
  down; halts print the accumulator, and there is no more peripheral than that.
- Two cards in the archive each contain one misread instruction (codes 28/30);
  the emulator correctly stops there with "unknown operation code".
- The запрещённые cells (function cells, marked with ″ in the textbook) are not
  addressable, just as they are not through normal addresses on the real
  machine.
