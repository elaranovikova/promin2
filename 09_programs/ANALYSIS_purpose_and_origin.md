# Purpose of the programs and estimated origin of the card set

As of 2026-08-07. Based on: the 27 reconstructed decks in this folder, the
captions on the cards (= the uploader's folder names), the constant cells in
use, the halt addresses and the control flow structure.

Confidence levels: **[established]** unambiguous from name and structure ·
**[likely]** several independent indications · **[guess]** named, but thinly
supported.

Noise floor first: at ~1 misreading per 250 instructions, the archive (2138
instructions) is expected to contain **8-9 wrongly read instructions**.
Exotic functions that appear on their own (a `cos` in a cost calculation, an
`acos` in the Simpson deck) sit exactly in that noise, or they are further
Промінь-2 specific codes like 19; they are not over-interpreted here.

---

## A. Economic and planning programs

**`Сеть_(25)`: network planning [established].** "Сеть" = network (plan). The
most demanding deck technically: table driven through three pointer cells
(016, 021, 050), computed jumps (`БПII`), eight loops, 16 print points: it
walks the predecessor/successor lists of a network graph and prints a series of
results (scheduling / critical path). After 1965 (the Kosygin reform) network
plans were a standard tool of Soviet plant planning. Only 13 of 25 cards
survive.

**`Рассчёт_себестоимости_(7)`: cost accounting [established].** The name says
it literally. 4 of 7 cards; five `СчП` counters point to loops over cost items.
An `ln`/`acos` in the remainder is either noise or an interest factor.

**`Срок_службы_оборудования_(16)`: service life of equipment [established].**
`ln` ×5 and `exp` ×3 fit depreciation/wear calculations with an exponential
model exactly. 11 of 16 cards.

**`(16)`: a second copy of that one [likely].** Shares two cards word for word
with `Срок_службы_оборудования_(16)`, same size marking (16).

**`Программа_многофакторного_анализа_(16)`: multifactor analysis
[established].** The name says it literally (regression / variance
decomposition). At 150 instructions the longest program, with 16 indirect
accesses and 8 `СчП`, summation over factor tables; `√` and `sin` for variance
and transformation calculations.

**`АСУ`: a skeleton for an automated management system [guess].** Only 20
instructions on 8 cards, almost everything unpunched, nothing but jumps and
halts: a frame, an exercise, or an abandoned start.

## B. Statistics and numerics (textbook exercises)

**`!_полная_симпсон`: numerical integration by Simpson's rule
[established].** Complete. Step width = interval/n, a three-way branch for the
weights 1/4/2, accumulator in cell 048, a loop back.

**`Определение_средне_квадратичного_(4)`: root mean square deviation
[established].** The name says it literally; `√` present, one loop counter.

**`о.ч.х.с.в._(10)`: characteristics of a random variable [likely].** The
abbreviation matches «определение числовых характеристик случайной величины»
letter for letter, a standard chapter of every Soviet probability textbook
(Wentzel). The output fits: **ten** print/halt points, a series of
characteristics (expected value, moments, variance ...), `√` ×4.

**`о.ч.х.с.д.с.в._(8)`: characteristics of a system of two random variables
[likely].** «... системы двух случайных величин»: covariance and correlation
coefficient; `√` ×6 (two variances + normalization).

**`!_полная_РК`: a general purpose computing core, reading open [guess].**
Complete, but the name cannot be resolved. The structure is notable: the first
four slots are a **jump table** (`БП 040/004/045/047`): four selectable entry
points, so four functions in one deck. Behind them, dot-product loops (`ЧтII` +
`Умн` + `Сл` over pointers). In a statistical setting «расчёт корреляции» would
suggest itself; «расчёт коэффициентов» is just as possible. Not decidable.

## C. Maintenance and test programs for the machine itself

**`!_полная_АУ`, `АУ_1-8`, `АУ_нет_3-5`: test program for the arithmetic unit
[likely].** АУ is the standard abbreviation for «арифметическое устройство».
Three indications: (1) **all 27 halts across all three copies are `Ост 099`**,
one uniform error halt, whereas application decks end with `Ост 001`; the
pattern is consistently "compute a test case, subtract the expected value,
`УП1` skips the error halt at 0". (2) Heavy use of the constant cells 91-99
(ln10, 2π, √ values) as built-in expected values. (3) Exactly one `sin`, `cos`
and `tg` each, a check of the function unit. That this deck of all decks
exists in **three copies** fits a maintenance deck in daily use.

**`ЗУ`: test program for the memory unit [likely].** ЗУ = «запоминающее
устройство» (as in the textbook). It works with address arithmetic (`Слф 090` =
+1 address unit), writes through computed addresses (`ЗпII`) and counts with
`СчП`: it walks memory cells systematically.

**`МПМ`: reading open [guess].** Builds pointers with `Слф` chains and halts
with the error halt `Ост 099`, a test or helper deck rather than an
application.

## D. Helper decks

**`Вариант`: parameter set switch [established].** Copies cells 022-027 word
by word into the working cells 006-010 ff.; it switches the input data of
another program over to a different "variant".

**`Закл`: the closing part of a larger program [guess].** «Закл(ючение)» =
conclusion. It reads intermediate results it never writes itself, computes with
π and with dense `СчП` loops over arrays (`ЧтII` + address advance).

**`Прочее`** is "miscellaneous", the uploader's box of leftovers for unlabeled
cards, not a program of its own (its jump target hit rate is correspondingly
poor).

## E. The unnamed numbered decks 1-5

The captions give only a deck number and a card range (`2_1-14` = deck 2, cards
1-14). Two findings:

- **`1_(13)`, `2_1-15(16)` and `3_(7)` read exactly the same input cells
  (000, 002, 051, 053)** and end with a result + `Ост 001`: three stages or
  variants of *one* task. All three compute with `exp`/`ln`: a growth, interest
  or depreciation calculation [likely].
- `2_1-14` (reads table 021-031) and `5_1-14` (reads 012-020) are series/table
  processing; with 29 jumps, `5_1-14` is the most branch-heavy deck of all.
  `3_1-9`, `3_1-11-15` and `4_1-13` break off in mid flow; the names say
  themselves that cards are missing.

---

## Estimated origin of the set

**In short: a Промінь-2 workplace with an engineering-economics profile in the
Voronezh area, late 1960s to early 1970s, most likely the computing room of a
college or technical school with a chair of economics, or the planning /
scientific-organization-of-labor lab of a plant. This is an estimate, not
proof.**

The chain of indications:

1. **The mix of applications is plant economics**: network planning, cost
   accounting, service life/depreciation, multifactor analysis, plus an АСУ
   skeleton. That is exactly the toolkit of Soviet plant planning after the
   1965 reform, and *not* a single classic technical engineering task (no
   strength of materials, no electrics, no geometry), even though the machine
   was built for those.
2. **Alongside them stand pure statistics exercises from the textbook**
   (characteristics of random variables at two levels, root mean square
   deviation, Simpson integration). That combination of exercises next to
   applied calculations argues for a teaching context, or a lab that also
   trained people.
3. **The maintenance decks belong to the machine**: the АУ test deck in three
   copies and the ЗУ test show that the set reflects the complete holdings of
   one machine site (applications + exercises + maintenance), not the
   collection of a single programmer.
4. **Voronezh as a location indication**: the uploader (from Voronezh) bought
   the cards as one lot; the only programming textbook for the machine that can
   be found comes from the University of Voronezh (1973) and was in the city
   library there; the Промінь was demonstrably present in teaching and
   operation in Voronezh. A local origin of the lot is plausible but not
   certain.
5. **Time window**: the machine was built from 1967, network planning was in
   vogue from the mid-sixties, the textbook is from 1973 -> use from the late
   sixties to the mid seventies.

What could overturn or confirm this estimate: the handwritten fields «КАРТА №»
/ «ВСЕГО КАРТ» (comparing the handwriting: one person or many?), the notes on
the reverse sides that the uploader mentions in passing, or a word from the
uploader on where exactly he acquired the lot.
