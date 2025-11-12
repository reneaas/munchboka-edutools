# Parsons Puzzle Examples

This page demonstrates the Parsons puzzle directive for creating code-reordering exercises.

## What is a Parsons Puzzle?

A Parsons puzzle is an educational tool where students must arrange shuffled lines of code into the correct order. This helps learners understand program structure and logic flow without writing code from scratch.

## Example 1: Simple Fibonacci Function

Try to arrange these lines of code to create a correct Fibonacci function:

```{parsons-puzzle}
def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)
```

## Example 2: Loop Example

Arrange these lines to create a function that sums numbers from 1 to n:

```{parsons-puzzle} sum-loop
:lang: python

def sum_to_n(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total
```

## Example 3: Conditional Logic

Put these lines in the correct order to check if a number is even or odd:

```{parsons-puzzle} even-odd
:lang: python

def check_even_odd(number):
    if number % 2 == 0:
        return "Even"
    else:
        return "Odd"
```

## Example 4: List Comprehension

Arrange these lines to create a function that filters even numbers:

```{parsons-puzzle} filter-evens
:lang: python

def filter_even_numbers(numbers):
    even_numbers = [num for num in numbers if num % 2 == 0]
    return even_numbers
```

## Example 5: More Complex Example

This one is a bit more challenging - a recursive factorial function:

```{parsons-puzzle} factorial
:lang: python

def factorial(n):
    if n == 0 or n == 1:
        return 1
    else:
        return n * factorial(n - 1)
```

## How to Use

1. **Drag** code lines from the top area
2. **Drop** them in the bottom area in the correct order
3. Click **"Sjekk løsning"** (Check solution) to verify
4. Get instant feedback with toast notifications
5. Click **"Reset puslespill"** (Reset puzzle) to try again

## Features

- 🎯 **Drag-and-drop interface**: Intuitive interaction
- ✅ **Instant feedback**: Toast notifications show success/error
- 🔄 **Reset and retry**: Shuffle and try as many times as needed
- 📋 **Copy solution**: Copy the correct code when solved
- 🎨 **Syntax highlighting**: Code is highlighted with highlight.js
- 🌓 **Theme support**: Works in both light and dark modes
