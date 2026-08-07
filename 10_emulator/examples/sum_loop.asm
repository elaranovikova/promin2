; Loop with СчП: adds the constant 1 five times -> 5.
; Cell 010 is the counter word: sign minus, counter = 100 - N.
; Usage: python3 promin2_emu.py --program examples/sum_loop.asm --set-raw 10=-00095
000 Чт 000      ; S := 0
001 Зп 001      ; accumulator into cell 001
002 Чт 001      ; top of the loop
003 Сл 086      ; S := S + 1
004 Зп 001
005 СчП 010     ; advance the counter word; at 100 the sign turns +
006 УП2 002     ; while negative: back to the top of the loop
007 Чт 001
008 Ост 001     ; result: 5
