; π by Machin's formula: π = 16·atan(1/5) − 4·atan(1/239)
; Basic arithmetic and СчП loops only - the machine's atan hardware
; instructions are deliberately NOT used. At the end the program checks itself
; against the built-in π constant in cell 081.
;
; Cells: 001 x · 002 −x² · 003 power · 004 sum · 005 k · 006 building 239
;        007 atan(1/5) · 008 atan(1/239) · 009 intermediate value
; Counter words (input): 010 = raw:-00095 (5 extra terms), 011 = raw:-00099 (1)
;
; Usage: python3 promin2_emu.py --program examples/pi_machin.asm \
;             --set-raw 10=-00095 --set-raw 11=-00099

; build x = 1/5 from constants: 2/10
000 Чт 087
001 Дел 091
002 Зп 001
; atan series for x: sum = x, k = 1, power = x, factor −x²
003 Зп 003
004 Зп 004
005 Чт 086
006 Зп 005
007 Чт 001
008 Умн 001
009 Выч2 000      ; S := 0 − S  →  −x²
010 Зп 002
; loop A: k += 2, power *= −x², sum += power/k
011 Чт 005
012 Сл 087
013 Зп 005
014 Чт 003
015 Умн 002
016 Зп 003
017 Дел 005
018 Сл 004
019 Зп 004
020 СчП 010
021 УП2 011
022 Чт 004
023 Зп 007        ; atan(1/5)
; x = 1/239; build the 239 from constants: 10·10·2 + (2·2·10 − 1)
024 Чт 091
025 Умн 091
026 Умн 087
027 Зп 006
028 Чт 087
029 Умн 087
030 Умн 091
031 Выч1 086
032 Сл 006
033 Зп 006
034 Чт 086
035 Дел 006
036 Зп 001
; atan series for 1/239 (identical block)
037 Зп 003
038 Зп 004
039 Чт 086
040 Зп 005
041 Чт 001
042 Умн 001
043 Выч2 000
044 Зп 002
; loop B
045 Чт 005
046 Сл 087
047 Зп 005
048 Чт 003
049 Умн 002
050 Зп 003
051 Дел 005
052 Сл 004
053 Зп 004
054 СчП 011
055 УП2 045
056 Чт 004
057 Зп 008        ; atan(1/239)
; π = 16·A − 4·B  (16 and 4 by doubling with the constant 2)
058 Чт 007
059 Умн 087
060 Умн 087
061 Умн 087
062 Умн 087
063 Зп 009        ; 16·A
064 Чт 008
065 Умн 087
066 Умн 087       ; 4·B
067 Выч2 009      ; S := 16A − 4B = π
068 Ост 001       ; halt 1: computed π
; self-check against the machine constant
069 Выч1 081      ; π_computed − π_constant (3.1416)
070 Ост 002       ; halt 2: deviation
