# Turtle Graphics Examples

This page demonstrates the `{turtle}` directive for interactive Python turtle graphics.

## Example 1: Simple Square

```{turtle}
from turtle import *

for i in range(4):
    forward(100)
    right(90)
```

## Example 2: Colorful Spiral

```{turtle}
import turtle

colors = ['red', 'purple', 'blue', 'green', 'orange', 'yellow']
t = turtle.Turtle()
t.speed(0)

for i in range(180):
    t.pencolor(colors[i % 6])
    t.width(i / 100 + 1)
    t.forward(i)
    t.left(59)
```

## Example 3: Star Pattern

```{turtle}
import turtle

t = turtle.Turtle()
t.speed(0)
t.color('gold', 'yellow')
t.begin_fill()

for i in range(5):
    t.forward(200)
    t.right(144)

t.end_fill()
```

## Example 4: Circle Flower

```{turtle}
import turtle

t = turtle.Turtle()
t.speed(0)

colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']

for i in range(36):
    t.pencolor(colors[i % 6])
    t.circle(100)
    t.right(10)
```

## Example 5: Recursive Tree

```{turtle}
import turtle

def draw_tree(branch_length, t):
    if branch_length > 5:
        t.forward(branch_length)
        t.right(20)
        draw_tree(branch_length - 15, t)
        t.left(40)
        draw_tree(branch_length - 15, t)
        t.right(20)
        t.backward(branch_length)

t = turtle.Turtle()
t.left(90)
t.speed(0)
t.color('green')

draw_tree(75, t)
```

## Example 6: Hexagonal Pattern

```{turtle}
import turtle

t = turtle.Turtle()
t.speed(0)

colors = ['red', 'blue', 'green', 'yellow', 'orange', 'purple']

for i in range(36):
    t.pencolor(colors[i % 6])
    t.width(2)
    for j in range(6):
        t.forward(100)
        t.right(60)
    t.right(10)
```

## Testing Features

### Custom Identifier

You can provide a custom identifier as an argument:

```{turtle} my-custom-drawing
import turtle

t = turtle.Turtle()
t.shape('turtle')
t.color('darkgreen')

# Draw a simple house
t.penup()
t.goto(-50, -50)
t.pendown()

# House base
for i in range(4):
    t.forward(100)
    t.left(90)

# Roof
t.goto(0, 50)
t.goto(50, 0)
t.goto(-50, 0)
```

### Multiple Turtles

```{turtle}
import turtle

# Create two turtles
t1 = turtle.Turtle()
t2 = turtle.Turtle()

t1.color('red')
t2.color('blue')

t1.penup()
t1.goto(-100, 0)
t1.pendown()

t2.penup()
t2.goto(100, 0)
t2.pendown()

# Draw circles
t1.circle(50)
t2.circle(50)
```
