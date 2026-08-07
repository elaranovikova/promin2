#!/usr/bin/env python3
"""Tests of the Промінь-2 emulator against the documented behavior.

Every test checks one behavior described in the textbook (page reference in the
comment). Usage: python3 test_emu.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from promin2_emu import (EmergencyStop, Emulator, Num, add, add_fixed, divide,
                         load_asm, multiply)

FAILURES = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global FAILURES
    status = "ok  " if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" - {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES += 1


def run(asm: str, preset: dict[int, float | Num] | None = None, code19: str = "schp",
        max_steps: int = 10_000):
    lines = [line for line in asm.strip().splitlines()]
    path = Path(__file__).parent / "_test_tmp.asm"
    path.write_text("\n".join(lines), encoding="utf-8")
    program = load_asm(path)
    path.unlink()
    emulator = Emulator(program, code19=code19)
    for cell, value in (preset or {}).items():
        number = value if isinstance(value, Num) else Num.from_float(value)
        emulator.memory.write(cell, number, allow_constants=True)
    result = emulator.run(max_steps=max_steps)
    return emulator, result


print("Number format (textbook ch. 1 §3)")
z = Num.from_float(20.111)
check("normalization +0.20111e+2", repr(z) == "+0.20111e+2", repr(z))
z = Num.from_float(-0.0005)
check("normalization -0.50000e-3", repr(z) == "-0.50000e-3", repr(z))
check("machine zero below 10^-10", Num.from_float(1e-11).is_zero())

print("Digit-faithful arithmetic")
a, b = Num.from_float(2.0), Num.from_float(2.0)
check("2+2=4", add(a, b).to_float() == 4.0)
check("1/3 = 0.33333 (truncated)",
      repr(divide(Num.from_float(1), Num.from_float(3))) == "+0.33333e+0")
# normalizing out of the full product register has to happen before the cut to
# five digits, otherwise the fifth one is lost whenever M1*M2 < 0.1
check("1/3 * 0.3 keeps the fifth digit",
      repr(multiply(Num.from_float(1 / 3), Num.from_float(0.3))) == "+0.99999e-1",
      repr(multiply(Num.from_float(1 / 3), Num.from_float(0.3))))
try:
    multiply(Num.raw(1, 99999, 9), Num.from_float(10.0))
    check("exponent overflow stops", False)
except EmergencyStop:
    check("exponent overflow stops", True)

print("The Сл-080 trick: integer part (textbook p. 21)")
# «после операции 'Сл 80' в сумматоре будет находиться целая часть числа»
emulator, _ = run("Чт 051\nСл 080\nОст 001", preset={51: 123.456})
check("integer(123.456) = 123", emulator.s.to_float() == 123.0,
      str(emulator.s.to_float()))
emulator, _ = run("Чт 051\nСл 080\nОст 001", preset={51: 0.999})
check("integer(0.999) = 0", emulator.s.is_zero(), str(emulator.s.to_float()))

print("Fixed-point address arithmetic (1A, textbook pp. 22-23)")
# 1A = +0.00100 raises the address field (digits V, IV, III) by 1
# feed the address word 0.05000 (address 050) unnormalized, as at the console
emulator, _ = run("Чт 051\nСлф 090\nОст 001", preset={51: Num.raw(1, 5000, 0)})
check("address word 050 + 1A = address word 051",
      emulator.s.address_field() == 51 and emulator.s.mant == 5100,
      repr(emulator.s))

print("Indirect addressing (ЧтII/ЗпII, table 5 codes 11-13)")
asm = """
Чт 051
ЧтII 010
Ост 001
"""
emulator, _ = run(asm, preset={10: Num.raw(1, 4200, 0), 42: 7.5, 51: 0.0})
check("ЧтII reads cell 042 through the address field of cell 010",
      emulator.s.to_float() == 7.5, str(emulator.s.to_float()))

print("Conditional jumps (УП1: S=0, УП2: S<0)")
emulator, _ = run("Чт 000\nУП1 004\nЧт 087\nОст 001\nЧт 086\nОст 002")
check("УП1 jumps when S=0", emulator.halts[0]["code"] == 2 and emulator.s.to_float() == 1.0)
emulator, _ = run("Чт 051\nУП2 004\nЧт 087\nОст 001\nЧт 086\nОст 002", preset={51: -3.0})
check("УП2 jumps when S<0", emulator.halts[0]["code"] == 2)

print("СчП loop (table 6): exactly N passes")
# cell 010: sign minus, counter = 100-5 = 95 -> 5 passes
asm = """
Чт 000
Зп 001
Чт 001      ; top of the loop (instruction 002)
Сл 086
Зп 001
СчП 010
УП2 002
Чт 001
Ост 001
"""
emulator, result = run(asm, preset={10: Num.raw(-1, 95, 0)})
check("the sum of five times +1 is 5", emulator.s.to_float() == 5.0,
      str(emulator.s.to_float()))
check("halt with code 001 reached", result["halts"][0]["code"] == 1)

print("Фр (code 29): S := |S| * sign a")
emulator, _ = run("Чт 051\nФр 052\nОст 001", preset={51: 3.0, 52: -1.0})
check("Фр turns 3 into -3", emulator.s.to_float() == -3.0)

print("Functions with range checks (table 5)")
emulator, _ = run("Чт 081\nsin 000\nОст 001")
check("sin(pi) close to 0", abs(emulator.s.to_float()) < 1e-3, str(emulator.s.to_float()))
_, result = run("Чт 051\n√ 000\nОст 001", preset={51: -4.0})
check("square root of a negative stops", "аварийный" in result["reason"])
_, result = run("Чт 051\nln 000\nОст 001", preset={51: 0.0})
check("ln(0) stops", "аварийный" in result["reason"])

print("Constant cells are write protected (textbook p. 13)")
emulator, result = run("Чт 086\nЗп 081\nЧт 081\nОст 001")
check("Зп 081 is ignored, pi stays", emulator.s.to_float() == 3.1416,
      str(emulator.s.to_float()))
check("warning logged", len(result["warnings"]) == 1)

print("An unpunched slot ends the run")
emulator, result = run("Чт 086\n---\nЧт 087\nОст 001")
check("end at the empty slot, S stays 1", result["reason"] == "end of program"
      and emulator.s.to_float() == 1.0)

print("Code 19 is switchable: sh instead of СчП")
emulator, _ = run("Чт 086\nsh 000\nОст 001", code19="sh")
check("sh(1) = 1.1752", abs(emulator.s.to_float() - math.sinh(1)) < 1e-3,
      str(emulator.s.to_float()))

print()
if FAILURES:
    print(f"{FAILURES} tests failed")
    raise SystemExit(1)
print("all tests passed")
