# Horner Examples

This page demonstrates the `horner` directive for visualizing Horner's method (synthetic division).

## Basic Example

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1

Complete Horner scheme for evaluating the polynomial at x=1.
::::

## Different Values

### Evaluate at x = 2

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 2

Horner's method at x=2.
::::

### Evaluate at x = -1

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: -1

Horner's method at x=-1.
::::

## Stage-by-Stage (Tutor Mode)

### Stage 1

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 1
:tutor:

First step in tutor mode.
::::

### Stage 3

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 3
:tutor:

Third step in tutor mode.
::::

### Stage 6

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 6
:tutor:

Sixth step in tutor mode.
::::

### Complete (Stage 12)

::::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 12
:tutor:

Complete tutor mode (all steps shown).
::::

## Different Alignments

### Left Aligned

::::{horner}
:p: 2x^2 + 5x + 3
:x: -1
:align: left

Scheme aligned to the left.
::::

### Center Aligned (default)

::::{horner}
:p: 2x^2 + 5x + 3
:x: -1
:align: center

Scheme centered (this is the default).
::::

### Right Aligned

::::{horner}
:p: 2x^2 + 5x + 3
:x: -1
:align: right

Scheme aligned to the right.
::::

## Custom Width

### 50% Width

::::{horner}
:p: x^4 - 1
:x: 1
:width: 50%

Horner scheme with 50% width.
::::

### Fixed 400px Width

::::{horner}
:p: x^4 - 1
:x: 1
:width: 400

Horner scheme with fixed 400px width.
::::

## Different Polynomials

### Quadratic

::::{horner}
:p: x^2 + 3x + 2
:x: -1

Quadratic polynomial.
::::

### Higher Degree

::::{horner}
:p: x^5 - 2x^4 + x^3 - 3x^2 + 2x - 1
:x: 2

Fifth-degree polynomial.
::::
