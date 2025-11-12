# `quiz` directive

The `quiz` directive supports creating interactive quizzes with multiple-choice questions. You can insert figures, mathematical expressions and code as part of the questions and answers.



## Examples


### Example 1

A basic quiz with one question and four answer options:

```markdown
:::{quiz}
Q: What is the answer to $2 + 2$?
+ $4$
- $3$
- $2$
- $1$

:::
```

which gives the following output:

:::{quiz}
Q: What is the answer to $2 + 2$?
+ $4$
- $3$
- $2$
- $1$

:::


### Example 2
A quiz with multiple questions with four answers each:


```markdown
:::{quiz}
Q: What is the output from the following code: <pre><code class="python">def f(x):\n    return x**2 - 2*x + 1\n\nx = 1\ny = f(x)\n\nprint(x)</code></pre>
+ $0$
- $1$
- $-1$
- $2$

Q: Which code will produce the sequence $1, 2, 4, 8$?
+ <pre><code class="python">for i in range(4):\n    print(2**i)</code></pre>
- <pre><code class="python">for i in range(4):\n    print(i*2)</code></pre>
- <pre><code class="python">for i in range(4):\n    print(i+1)</code></pre>
- <pre><code class="python">for i in range(4):\n    print(i**3)</code></pre>
:::
```

The result:

:::{quiz}
Q: What is the output from the following code: <pre><code class="python">def f(x):\n    return x**2 - 2*x + 1\n\nx = 1\ny = f(x)\n\nprint(x)</code></pre>
+ $0$
- $1$
- $-1$
- $2$

Q: Which code will produce the sequence $1, 2, 4, 8$?
+ <pre><code class="python">for i in range(4):\n    print(2**i)</code></pre>
- <pre><code class="python">for i in range(4):\n    print(i*2)</code></pre>
- <pre><code class="python">for i in range(4):\n    print(i+1)</code></pre>
- <pre><code class="python">for i in range(4):\n    print(i**3)</code></pre>
:::


