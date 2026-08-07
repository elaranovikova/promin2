; Circumference U = 2*pi*r - the smallest Промінь program that does anything.
; Usage: python3 promin2_emu.py --program examples/circumference.asm --set 51=1.5
000 Чт 051      ; S := r (entered into cell 051 by the operator)
001 Умн 082     ; S := S * 2pi   (constant cell 082)
002 Ост 001     ; halt, result in the accumulator
