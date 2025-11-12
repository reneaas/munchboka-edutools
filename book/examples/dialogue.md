# Dialogue Directive Examples

This page demonstrates the dialogue directive for creating conversation-style content with chat-bubble styling.

## Example 1: Basic Dialogue

```{dialogue}
:name1: Alice
:name2: Bob
:speaker1: left
:speaker2: right

Alice: Hello! How are you today?
Bob: I'm doing great, thanks for asking!
Alice: That's wonderful to hear.
Bob: How about you?
Alice: I'm doing well too, thank you!
```

## Example 2: Math in Dialogue

The dialogue directive supports LaTeX math notation:

```{dialogue}
:name1: Teacher
:name2: Student
:speaker1: left
:speaker2: right

Teacher: Can you solve the equation $x^2 - 5x + 6 = 0$?
Student: Yes! I can factor it as $(x-2)(x-3) = 0$.
Teacher: Excellent! So what are the solutions?
Student: The solutions are $x = 2$ and $x = 3$.
Teacher: Perfect! Well done.
```

## Example 3: Right-Left Alignment

You can switch which speaker appears on which side:

```{dialogue}
:name1: Emma
:name2: Liam
:speaker1: right
:speaker2: left

Emma: Did you understand the homework?
Liam: Yes, I think so. The key was remembering the formula.
Emma: Which formula did you use?
Liam: I used the quadratic formula: $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$
Emma: Oh right! That makes sense now.
```

## Example 4: Discussion About Functions

```{dialogue}
:name1: Maria
:name2: Carlos
:speaker1: left
:speaker2: right

Maria: What is the derivative of $f(x) = x^3$?
Carlos: Using the power rule, it's $f'(x) = 3x^2$.
Maria: Great! Now what about $g(x) = \sin(x)$?
Carlos: That's $g'(x) = \cos(x)$.
Maria: Exactly! You've got this.
```

## Notes

- Each speaker must be assigned to either "left" or "right"
- Messages can contain math notation, which will be properly rendered
- The directive automatically styles the conversation with chat bubbles
- Colors adapt to light/dark mode themes
