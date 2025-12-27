# Escape Room 2 Example

The `escape-room-2` directive provides a modular way to create escape rooms with nested `room` directives.

## Basic Example

::::::{escape-room-2}

::::{room}
---
code: 144
title: First Room
---
What is $12 \times 12$?

Hint: Think about perfect squares!
::::

::::{room}
---
code: abc123
title: Second Room
---
You've made it to the second room! 

The next code is hidden in the math: $$\text{Code} = 256$$
::::

::::{room}
---
code: 256
title: Final Room
---
Congratulations! You solved the escape room! 🎉
::::

::::::

## Example with Nested Directives

::::::{escape-room-2}

::::{room}
---
code: 42
title: Math Plot Room
---
Look at this plot to find the answer:

:::{plot}
:function: x**2 - 2*x + 2
:xmin: -2
:xmax: 5
:ymin: -1
:ymax: 10
:::

The code is the minimum value of the function (rounded).
::::

::::{room}
---
code: hello
title: List Room
---
Find the code in this list:

1. First item
2. Second item has **bold text**
3. The code is: `hello`
::::

::::{room}
---
code: success
---
You win! Well done! ✨
::::

::::::

## Example with Multiple Codes

Each room can accept multiple codes (comma or semicolon separated):

::::::{escape-room-2}

::::{room}
---
code: 100, one hundred, 100.0
title: Flexible Answer
---
What is $10^2$?

This room accepts multiple equivalent answers.
::::

::::{room}
---
code: done
---
Perfect! 🎯
::::

::::::

## Case Insensitive Mode

Add the `:case_insensitive:` flag to ignore case when checking codes:

::::::{escape-room-2}
:case_insensitive:

::::{room}
---
code: HELLO
---
Type "hello", "HELLO", or "HeLLo" - they all work!
::::

::::{room}
---
code: success
---
Great job! 🌟
::::

::::::
