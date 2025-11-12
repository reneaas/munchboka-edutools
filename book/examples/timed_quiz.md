# Timed Quiz Directive

The `timed-quiz` directive creates interactive quizzes where students race against the clock to answer as many questions as possible correctly.

## Basic Usage

```{timed-quiz}
Q: What is 2 + 2?
+ 4
- 3
- 5
- 6

Q: What is 3 × 7?
+ 21
- 18
- 24
- 28

Q: What is 10 - 4?
+ 6
- 4
- 8
- 5
```

## Features

### Countdown Timer

- **Visual progress bar**: Shows remaining time
- **Color coding**: Green → Yellow (50%) → Red (20%)
- **60-second default**: Complete as many questions as possible

### Question Management

- **Automatic shuffling**: Questions appear in random order
- **Answer shuffling**: Answer options randomized for each question
- **Instant feedback**: Visual confirmation of correct/incorrect answers
- **Score tracking**: See how many you got right

### Math Support

Questions and answers can include LaTeX math:

```{timed-quiz}
Q: Solve: $x^2 = 16$
+ $x = \pm 4$
- $x = 4$
- $x = 8$
- $x = 16$

Q: What is $\frac{1}{2} + \frac{1}{3}$?
+ $\frac{5}{6}$
- $\frac{2}{5}$
- $\frac{3}{5}$
- $\frac{1}{6}$
```

## Format

### Question Syntax

```
Q: Question text here
+ Correct answer
- Incorrect answer
- Incorrect answer
- Incorrect answer
```

- **Q:**: Starts a new question
- **+**: Marks a correct answer (can have multiple for multi-select)
- **-**: Marks an incorrect answer

### Empty Lines

Empty lines between questions are optional but improve readability:

```
Q: First question?
+ Answer 1
- Answer 2

Q: Second question?
+ Answer A
- Answer B
```

## How It Works

1. **Start**: Click "Start Quiz" button
2. **Timer begins**: 60-second countdown starts
3. **Answer questions**: Click your answer choice
4. **Automatic progression**: Moves to next question after selection
5. **Score display**: See results when time expires or all questions answered
6. **Restart**: Click "Start på nytt" to try again

## Best Practices

### Question Design

- Keep questions concise and clear
- Provide 3-4 answer options per question
- Make distractors plausible but clearly wrong
- Mix difficulty levels throughout the quiz

### Number of Questions

- **5-10 questions**: Quick knowledge check
- **10-20 questions**: Standard quiz
- **20+ questions**: Comprehensive review

With 60 seconds, students typically complete 10-15 questions depending on complexity.

### Answer Options

- **Single correct answer**: Most common format
- **Multiple correct answers**: Mark multiple options with `+`
- Students must select ALL correct answers to get credit

## Theme Support

The quiz automatically adapts to the current theme (light/dark/auto mode):

- Background colors adjust for readability
- Progress bar maintains visibility
- Answer cards provide clear contrast
- Selected state clearly visible

## Accessibility

- Keyboard navigation supported
- High contrast ratios
- Screen reader compatible
- Clear visual feedback

## Technical Details

### Dependencies

- **KaTeX**: For math rendering (loaded globally)
- **highlight.js**: For code syntax highlighting (loaded globally)
- **TimedMultipleChoiceQuiz.js**: Main quiz logic
- **MultipleChoiceQuestion.js**: Question rendering
- **utils.js**: Helper functions

### Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile responsive design
- Touch-friendly on tablets and phones
