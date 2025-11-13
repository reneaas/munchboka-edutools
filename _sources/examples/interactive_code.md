# Interactive Code Examples

This page demonstrates the interactive code directive with various features.

## Basic Example

:::{interactive-code}
# Try running this code
print("Hello, World!")
x = 5
y = 10
print(f"The sum is {x + y}")
:::

## Original Example

:::{interactive-code}
def f(x):
    return x**2 - 3*x + 2

for x in range(-10, 11):
    if f(x) < 0:
        print(f"{f(x) = } at {x = }")
:::

## Example with Prediction Mode

:::{interactive-code}
:predict:

# What will this print?
for i in range(3):
    print(i * 2)
:::

## Example with Math (NumPy)

:::{interactive-code}
import numpy as np

# Create array and compute mean
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {arr.mean()}")
:::

## Example with Plotting

:::{interactive-code}
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 2*np.pi, 100)
y = np.sin(x)

plt.plot(x, y)
plt.xlabel('x')
plt.ylabel('sin(x)')
plt.title('Sine Wave')
plt.grid(True)
plt.show()
:::