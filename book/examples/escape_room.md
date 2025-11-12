# Escape Room Examples

The `escape-room` directive creates interactive sequential puzzles where students must enter codes to unlock the next room.

## Basic Math Puzzle

A simple three-room escape room with math problems:

:::{escaperoom}
Puzzle: Rom 1 - Addisjon
Code: 42
Q: Hva er $20 + 22$?

Puzzle: Rom 2 - Multiplikasjon  
Code: 144
Q: Hva er $12 \times 12$?

Puzzle: Rom 3 - Potenser
Code: 256
Q: Hva er $2^8$?
:::

## Multiple Correct Codes

You can specify multiple acceptable codes separated by commas:

:::{escaperoom}
:case_insensitive:

Puzzle: Rom 1 - Synonymer
Code: fire, 4, IV
Q: Hvilket tall kommer etter tre?

Puzzle: Rom 2 - Fakta
Code: Norge, norway, NO
Q: Hvilket land er Oslo hovedstaden i?
:::

## With LaTeX Math

Complex mathematical expressions using LaTeX:

:::{escaperoom}
Puzzle: Rom 1 - Algebra
Code: x=2
Q: Løs likningen: $x^2 - 4 = 0$ (positiv løsning)

Puzzle: Rom 2 - Trigonometri
Code: 1
Q: Hva er verdien av $\sin^2(\theta) + \cos^2(\theta)$?

Puzzle: Rom 3 - Derivasjon
Code: 2x
Q: Hva er den deriverte av $f(x) = x^2$?
:::

## Progress Tracking

The escape room automatically saves progress to localStorage:

- If you refresh the page, you'll be asked if you want to resume
- Progress is cleared when you complete all rooms
- Each escape room has its own independent progress

## Features

- **Sequential unlocking**: Must solve each room in order
- **Multiple codes**: Accept multiple correct answers per room
- **Case insensitive**: Optional flag to ignore case in codes
- **LaTeX support**: Full KaTeX math rendering
- **Progress saving**: Automatically saves progress to localStorage
- **Theme aware**: Adapts to light/dark mode automatically
- **Visual progress**: Progress bar shows completion status

## How It Works

1. Read the question in the current room
2. Type the code into the input field
3. Click "Sjekk" or press Enter
4. If correct, you advance to the next room
5. If incorrect, you see an error message
6. Complete all rooms to finish the escape room!
