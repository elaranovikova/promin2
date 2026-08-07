#!/usr/bin/env python3
"""Emulator of the ЭВМ Промінь-2 (Kyiv/Severodonetsk, 1967).

Sources:
* Instruction set: Asnina/Bibikova/Zlatomreva, textbook Voronezh 1973,
  table 5 (pp. 18-20) and table 6; number format ch. 1 §3; memory §4-5;
  constants tables 3 and 4 (pp. 9-11); operation notes pp. 21-23.
* Programs: the reconstructed card decks in `09_programs/`
  (for the format see `06_scripts/decode_card.py`).

Machine model:
* One accumulator S. Numbers are decimal: mantissa 5 decimal digits, exponent
  1 decimal digit, one sign each; normalized 0.1 <= |M| < 1.
* Number memory 000-199 (080-099 and 180-199 are constants, write protected),
  instruction memory 000-159.
* The arithmetic is reproduced digit by digit (align -> add -> truncate ->
  normalize), so that the documented trick "Сл 080" (integer part by adding
  0.00000·10^5) comes out exactly right.

Deliberate assumptions (argued in the README):
* Rounding: truncation - the machine's rounding rule has not come down to us.
* Code 19 is СчП by default (readdressing/loop counting, table 6); with
  --code19 sh it computes the hyperbolic sine instead (table 5, Промінь-М).
* СчП also leaves its result in the accumulator (the cards consistently show
  СчП followed directly by a conditional jump).
* Ост halts; the emulator logs the halt and the accumulator and carries on
  (like an operator pressing start again). A halt on an unpunched slot
  (Ост 199, empty) ends the run.

Usage:
    python3 promin2_emu.py --deck <folder with *_matrix.csv> [--set 51=3.5 ...]
    python3 promin2_emu.py --program examples/sum_loop.asm --trace
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "06_scripts"))


# ---------------------------------------------------------------------------
# Number format
# ---------------------------------------------------------------------------

class EmergencyStop(Exception):
    """Аварийный останов - the machine comes to a stop with an error."""


class Num:
    """Промінь number: sign · 0.mmmmm · 10^(±p)."""

    __slots__ = ("sm", "mant", "e")

    def __init__(self, sm: int = 1, mant: int = 0, e: int = 0):
        self.sm = 1 if mant == 0 and sm >= 0 else (1 if sm >= 0 else -1)
        self.mant = mant          # 0..99999, value = mant/100000
        self.e = e                # exponent, -9..+9

    # -- construction -------------------------------------------------------

    @classmethod
    def from_float(cls, x: float) -> "Num":
        if x == 0:
            return cls()
        sm = 1 if x > 0 else -1
        x = abs(x)
        e = math.floor(math.log10(x)) + 1
        mant = int(x / (10.0 ** e) * 100000 + 1e-9)   # truncate
        if mant >= 100000:                            # log10 edge case
            mant //= 10
            e += 1
        z = cls(sm, mant, e)
        z._normalize()
        if z.e > 9:
            raise EmergencyStop(f"|x| >= 10^9 for constant {x}")
        return z

    @classmethod
    def raw(cls, sm: int, mant: int, e: int) -> "Num":
        """Take the digits unnormalized (e.g. 0.00000·10^5 or address words)."""
        return cls(sm, mant, e)

    # -- properties ---------------------------------------------------------

    def is_zero(self) -> bool:
        return self.mant == 0

    def to_float(self) -> float:
        return self.sm * (self.mant / 100000.0) * (10.0 ** self.e)

    def address_field(self) -> int:
        """Address field: mantissa digits V, IV, III (hundreds, tens, units).

        Textbook pp. 22-23: the Промінь-2 keeps addresses in digits III-V; the
        address unit 1A = +0.00100 raises digit III by 1.
        """
        return self.mant // 100

    def cycles(self) -> int:
        """Counter field for СчП: digits II, I."""
        return self.mant % 100

    def _normalize(self) -> None:
        if self.mant == 0:
            self.e = 0
            self.sm = 1
            return
        while self.mant < 10000:
            self.mant *= 10
            self.e -= 1
        if self.e < -9:           # machine zero
            self.mant = 0
            self.e = 0
            self.sm = 1

    def clone(self) -> "Num":
        return Num(self.sm, self.mant, self.e)

    def __repr__(self) -> str:
        v = "+" if self.sm > 0 else "-"
        return f"{v}0.{self.mant:05d}e{self.e:+d}"


# -- digit-faithful arithmetic ----------------------------------------------

def _align(z: Num, target_e: int) -> int:
    """Signed mantissa of z, aligned to exponent target_e."""
    shift = target_e - z.e
    m = z.mant
    if shift > 0:
        m = m // (10 ** shift) if shift <= 5 else 0
    elif shift < 0:
        # only happens when target_e is not the maximum - not used
        m = m * (10 ** (-shift))
    return z.sm * m


def add(a: Num, b: Num, subtract_b: bool = False) -> Num:
    """Сл/Выч: align to the larger exponent, add, truncate.

    A zero takes part in the alignment with its own exponent too - the
    documented trick "Сл 080" rests on that: the constant 0.00000·10^5 forces
    the sum to exponent 5, and the fractional digits fall out of the mantissa
    (textbook p. 21). The flip side is the machine zero described on p. 8,
    which appears when adding numbers of very different magnitude.
    """
    if a.is_zero() and b.is_zero():
        return Num()
    e = max(a.e, b.e)
    mb = -_align(b, e) if subtract_b else _align(b, e)
    total = _align(a, e) + mb
    sm = 1 if total >= 0 else -1
    total = abs(total)
    if total >= 100000:
        total //= 10
        e += 1
    if total != 0 and e > 9:
        raise EmergencyStop("|S| >= 10^9 (addition)")
    z = Num(sm, total, e)
    z._normalize()
    return z


def multiply(a: Num, b: Num) -> Num:
    if a.is_zero() or b.is_zero():
        return Num()
    # Normalize from the full (10-digit) product register first, then truncate
    # to 5 digits - otherwise a digit is lost when M1*M2 < 0.1.
    product = a.mant * b.mant
    e = a.e + b.e
    while product < 10 ** 9:
        product *= 10
        e -= 1
    mant = product // 100000
    z = Num(a.sm * b.sm, mant, e)
    z._normalize()
    if not z.is_zero() and z.e > 9:
        raise EmergencyStop("|S| >= 10^9 (multiplication)")
    return z


def divide(a: Num, b: Num) -> Num:
    if b.is_zero():
        raise EmergencyStop("division by 0")
    if a.is_zero():
        return Num()
    mant = (a.mant * 100000) // b.mant
    e = a.e - b.e
    while mant >= 100000:
        mant //= 10
        e += 1
    z = Num(a.sm * b.sm, mant, e)
    z._normalize()
    if not z.is_zero() and z.e > 9:
        raise EmergencyStop("|S| >= 10^9 (division)")
    return z


def add_fixed(a: Num, b: Num, subtract_b: bool = False) -> Num:
    """Слф/Вычф: mantissas as fixed-point numbers, no aligning or normalizing.

    The result is not normalized; a carry beyond the 5th digit is dropped. For
    a result of 0 the machine produces +0 (textbook p. 22).
    """
    mb = -b.sm * b.mant if subtract_b else b.sm * b.mant
    total = a.sm * a.mant + mb
    sm = 1 if total >= 0 else -1
    return Num.raw(sm, abs(total) % 100000, a.e)


# ---------------------------------------------------------------------------
# Memory with constants
# ---------------------------------------------------------------------------

def _constants() -> dict[int, Num]:
    """Tables 3+4 of the textbook (only the regularly addressable cells)."""
    f = Num.from_float
    k = {
        0: Num(),                                   # cell 000 holds 0
        80: Num.raw(1, 0, 5),                       # 0.00000·10^5 - integer trick
        81: f(3.1416), 82: f(6.2832), 83: f(0.31831), 84: f(0.15915),
        85: f(1.5708), 86: f(1.0), 87: f(2.0), 88: f(0.5), 89: f(0.25),
        90: Num.raw(1, 100, 0),                     # 1A = +0.00100
        91: f(10.0), 92: f(2.3026), 93: f(0.43429),
        94: f(57.296), 95: f(3437.7), 96: f(206260.0),
        97: f(0.017453), 98: f(0.00029089), 99: f(0.0000048481),
        180: f(3.0), 181: f(9.0),
        182: Num.raw(1, 300, 0),                    # 3A (scan ambiguous, see README)
        183: f(0.57721),                            # Euler-Mascheroni
        184: f(2.1544), 185: f(0.79788), 186: f(4.6415), 187: f(1.7725),
        188: f(1.4646), 189: f(24.0), 190: f(0.10100), 191: f(720.0),
        192: f(5040.0), 193: f(3628800.0), 194: f(2.7183), 195: f(7.3891),
        196: f(1.6487), 197: f(0.36790), 198: f(0.60650), 199: f(0.10000),
    }
    return k


PROTECTED = {0} | set(range(80, 100)) | set(range(180, 200))


class Memory:
    def __init__(self):
        self.cells: dict[int, Num] = {i: Num() for i in range(200)}
        self.cells.update(_constants())
        self.warnings: list[str] = []

    def read(self, address: int) -> Num:
        if not 0 <= address <= 199:
            raise EmergencyStop(f"cell address {address} outside 000-199")
        return self.cells[address].clone()

    def write(self, address: int, value: Num, allow_constants: bool = False) -> None:
        if not 0 <= address <= 199:
            raise EmergencyStop(f"cell address {address} outside 000-199")
        if address in PROTECTED and not allow_constants:
            self.warnings.append(f"write to constant cell {address:03d} ignored")
            return
        self.cells[address] = value.clone()


# ---------------------------------------------------------------------------
# Processor
# ---------------------------------------------------------------------------

def _function(name: str, fn, s: Num, limit: float | None = None,
              limit_kind: str = "") -> Num:
    x = s.to_float()
    if limit is not None:
        if limit_kind == "abs>=" and abs(x) >= limit:
            raise EmergencyStop(f"{name}: |S| >= {limit}")
        if limit_kind == "abs>" and abs(x) > limit:
            raise EmergencyStop(f"{name}: |S| > {limit}")
        if limit_kind == "<" and x < limit:
            raise EmergencyStop(f"{name}: S < {limit}")
        if limit_kind == "<=" and x <= limit:
            raise EmergencyStop(f"{name}: S <= {limit}")
    return Num.from_float(fn(x))


class Emulator:
    def __init__(self, program: list[tuple[int, int, bool]], code19: str = "schp",
                 allow_constants: bool = False):
        """program: list of (operation, address, empty) per instruction slot."""
        if len(program) > 160:
            raise ValueError("instruction memory holds only 160 instructions (000-159)")
        self.program = program
        self.memory = Memory()
        self.s = Num()
        self.pc = 0
        self.code19 = code19
        self.allow_constants = allow_constants
        self.steps = 0
        self.nops = 0
        self.halts: list[dict] = []
        self.trace: list[str] = []

    # -- execution ----------------------------------------------------------

    def _indirect(self, address: int) -> int:
        return self.memory.read(address).address_field()

    def step(self) -> str:
        """Execute one instruction. Returns '' | 'halt' | 'end'."""
        if not 0 <= self.pc < len(self.program):
            return "end"
        op, adr, empty = self.program[self.pc]
        self.steps += 1
        pc_old = self.pc
        self.pc += 1
        mem = self.memory
        result = ""

        if empty:                                  # unpunched slot
            self.halts.append({"pc": pc_old, "code": 199, "s": self.s.clone(),
                               "kind": "end of program (unpunched slot)"})
            result = "end"
        elif op == 0:
            # A slot punched out completely (every hole of the three columns):
            # that is how an instruction was deleted from the card after the
            # fact - no metal, no contact. Skipped as a NOP.
            self.nops += 1
        elif op == 1:
            self.s = add(self.s, mem.read(adr))
        elif op == 2:
            self.s = add(self.s, mem.read(adr), subtract_b=True)
        elif op == 3:
            self.s = add(mem.read(adr), self.s, subtract_b=True)
        elif op == 4:
            self.s = multiply(self.s, mem.read(adr))
        elif op == 5:
            self.s = divide(self.s, mem.read(adr))
        elif op == 6:
            self.s = mem.read(adr)
        elif op == 7:
            mem.write(adr, self.s, self.allow_constants)
        elif op == 8:
            self.pc = adr
        elif op == 9:
            if self.s.is_zero():
                self.pc = adr
        elif op == 10:
            if self.s.sm < 0 and not self.s.is_zero():
                self.pc = adr
        elif op == 11:
            self.s = mem.read(self._indirect(adr))
        elif op == 12:
            mem.write(self._indirect(adr), self.s, self.allow_constants)
        elif op == 13:
            self.pc = self._indirect(adr)
        elif op == 14:
            self.s = add_fixed(self.s, mem.read(adr))
        elif op == 15:
            self.s = add_fixed(self.s, mem.read(adr), subtract_b=True)
        elif op == 16:
            self.s = _function("sin", math.sin, self.s)
        elif op == 17:
            self.s = _function("cos", math.cos, self.s)
        elif op == 18:
            self.s = _function("tg", math.tan, self.s)
        elif op == 19:
            if self.code19 == "sh":
                self.s = _function("sh", math.sinh, self.s, 22, "abs>=")
            else:
                self.s = self._schp(adr)
        elif op == 20:
            self.s = _function("ch", math.cosh, self.s, 22, "abs>=")
        elif op == 21:
            self.s = _function("th", math.tanh, self.s, 22, "abs>=")
        elif op == 22:
            self.s = _function("asin", math.asin, self.s, 1, "abs>")
        elif op == 23:
            self.s = _function("acos", math.acos, self.s, 1, "abs>")
        elif op == 24:
            self.s = _function("atg", math.atan, self.s)
        elif op == 25:
            self.s = _function("sqrt", math.sqrt, self.s, 0, "<")
        elif op == 26:
            self.s = _function("exp", math.exp, self.s, 22, "abs>=")
        elif op == 27:
            self.s = _function("ln", math.log, self.s, 0, "<=")
        elif op == 29:
            a = mem.read(adr)
            sign = a.sm if not a.is_zero() else 1
            self.s = Num(sign, self.s.mant, self.s.e)
        elif op == 31:
            self.halts.append({"pc": pc_old, "code": adr, "s": self.s.clone(),
                               "kind": "Ост"})
            result = "halt"
        else:
            raise EmergencyStop(f"unknown operation code {op} at {pc_old:03d}")

        return result

    def _schp(self, address: int) -> Num:
        """СчП (table 6): address part +1, cycle counter +1, sign + at 100.

        Cell layout: digits V, IV, III = address, II, I = cycle count. The
        counter runs 00..99; the carry on reaching 100 sets the mantissa sign
        to + (which is how a backward "УП2" ends the loop).
        """
        cell = self.memory.read(address)
        address_part = (cell.address_field() + 1) % 1000
        cycles = cell.cycles() + 1
        sm = cell.sm
        if cycles >= 100:
            cycles = 0
            sm = 1
        new = Num.raw(sm, address_part * 100 + cycles, cell.e)
        self.memory.write(address, new, allow_constants=self.allow_constants)
        return new

    def run(self, max_steps: int = 200_000, trace: bool = False,
            stop_after_halts: int | None = None) -> dict:
        reason = "step limit"
        try:
            while self.steps < max_steps:
                if trace and 0 <= self.pc < len(self.program):
                    op, adr, empty = self.program[self.pc]
                    self.trace.append(f"{self.pc:03d}: op={op:2d} adr={adr:03d} S={self.s!r}")
                state = self.step()
                if state == "end":
                    reason = "end of program"
                    break
                if state == "halt" and stop_after_halts is not None \
                        and len(self.halts) >= stop_after_halts:
                    reason = "halt"
                    break
        except EmergencyStop as error:
            reason = f"аварийный останов: {error}"
        warnings = list(self.memory.warnings)
        if self.nops:
            warnings.append(f"{self.nops} punched-out instruction slots (op 0) skipped")
        return {
            "reason": reason,
            "steps": self.steps,
            "s": self.s,
            "halts": self.halts,
            "warnings": warnings,
        }


# ---------------------------------------------------------------------------
# Loading programs
# ---------------------------------------------------------------------------

_NAME_TO_CODE = {
    "СЛ": 1, "ВЫЧ1": 2, "ВЫЧ2": 3, "УМН": 4, "ДЕЛ": 5, "ЧТ": 6, "ЗП": 7,
    "БП": 8, "УП1": 9, "УП2": 10, "ЧТII": 11, "ЗПII": 12, "БПII": 13,
    "СЛФ": 14, "ВЫЧФ": 15, "SIN": 16, "COS": 17, "TG": 18, "SH": 19,
    "СЧП": 19, "CH": 20, "TH": 21, "ASIN": 22, "ACOS": 23, "ATG": 24,
    "√": 25, "SQRT": 25, "EXP": 26, "LN": 27, "ФР": 29, "ОСТ": 31,
}


def load_deck(folder: Path) -> list[tuple[int, int, bool]]:
    from decode_card import decode, read_matrix
    program = []
    files = sorted(folder.glob("*_matrix.csv"))
    if not files:
        raise SystemExit(f"no *_matrix.csv in {folder}")
    for file in files:
        for instruction in decode(read_matrix(file)):
            program.append((instruction["operation"], instruction["address"],
                            instruction["empty"]))
    return program


def load_asm(file: Path) -> list[tuple[int, int, bool]]:
    """Line format: [number] NAME address - or '---' for an empty slot."""
    program = []
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.split(";")[0].split("#")[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts and re.fullmatch(r"\d{1,3}", parts[0]):
            parts = parts[1:]                      # leading instruction number
        if not parts:
            continue
        if parts[0] == "---":
            program.append((31, 199, True))
            continue
        name = parts[0].upper()
        if name not in _NAME_TO_CODE:
            raise SystemExit(f"unknown instruction: {line!r}")
        address = int(parts[1]) if len(parts) > 1 else 0
        program.append((_NAME_TO_CODE[name], address, False))
    return program


def num_from_raw(text: str) -> Num:
    """Take '[+-]DDDDD[eN]' as an unnormalized digit pattern.

    This is how address and counter words are entered, the way the operator did
    it at the console: digit by digit, without normalization. Example: '-00095'
    is the СчП counter word for five passes through a loop.
    """
    m = re.fullmatch(r"([+-]?)(\d{1,5})(?:[eE](-?\d))?", text.strip())
    if not m:
        raise SystemExit(f"raw digit pattern expected ([+-]DDDDD[eN]): {text!r}")
    sign, digits, exponent = m.groups()
    return Num.raw(-1 if sign == "-" else 1, int(digits.zfill(5)),
                   int(exponent) if exponent else 0)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Emulator of the ЭВМ Промінь-2.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--deck", type=Path,
                        help="folder with *_matrix.csv (one card = 10 instructions)")
    source.add_argument("--program", type=Path,
                        help="assembler text file (e.g. examples/sum_loop.asm)")
    parser.add_argument("--set", action="append", default=[], metavar="CELL=VALUE",
                        dest="set_values",
                        help="preload a number cell, e.g. --set 51=3.5 (repeatable)")
    parser.add_argument("--set-raw", action="append", default=[],
                        metavar="CELL=[+-]DDDDD[eN]", dest="set_raw",
                        help="load a cell with a raw digit pattern (unnormalized), "
                             "e.g. --set-raw 10=-00095 for a СчП counter word")
    parser.add_argument("--code19", choices=["schp", "sh"], default="schp",
                        help="reading of code 19 (default: СчП)")
    parser.add_argument("--max-steps", type=int, default=200_000)
    parser.add_argument("--stop-after-halts", type=int, default=None,
                        help="stop after N Ост halts (default: keep running)")
    parser.add_argument("--trace", action="store_true", help="print every step")
    parser.add_argument("--allow-constants", action="store_true",
                        help="permit writes to constant cells instead of ignoring them")
    args = parser.parse_args(argv)

    program = load_deck(args.deck) if args.deck else load_asm(args.program)
    emulator = Emulator(program[:160], code19=args.code19,
                        allow_constants=args.allow_constants)

    for setting in args.set_values:
        cell, _, value = setting.partition("=")
        emulator.memory.write(int(cell), Num.from_float(float(value)),
                              allow_constants=True)
    for setting in args.set_raw:
        cell, _, value = setting.partition("=")
        emulator.memory.write(int(cell), num_from_raw(value), allow_constants=True)

    result = emulator.run(max_steps=args.max_steps, trace=args.trace,
                          stop_after_halts=args.stop_after_halts)

    if args.trace:
        print("\n".join(emulator.trace))
    print(f"\nProgram: {len(program)} instruction slots | {result['steps']} steps "
          f"| end: {result['reason']}")
    for halt in result["halts"]:
        value = halt["s"].to_float()
        print(f"  halt at instruction {halt['pc']:03d}  code {halt['code']:03d}  "
              f"S = {value:.6g}   ({halt['kind']})")
    for warning in result["warnings"][:10]:
        print(f"  warning: {warning}")
    print(f"Accumulator at the end: {result['s'].to_float():.6g}  ({result['s']!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
