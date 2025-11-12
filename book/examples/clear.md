# Clear Directive Examples

This page demonstrates the `{clear}` directive for clearing CSS floats.

## What is the Clear Directive?

The `{clear}` directive inserts a CSS `clear: both` element, which ensures that content flows below any floated elements rather than wrapping around them.

## Example 1: Clearing After Floated Content

Here's an example with some content that might float:

<div style="float: left; width: 200px; height: 100px; background: lightblue; margin: 10px; padding: 10px;">
This box is floated left. Without a clear, text would wrap around it.
</div>

Without the clear directive, this text would wrap around the floated box on the left. This can make layouts look awkward and hard to read.

```{clear}
```

After the `{clear}` directive, this text starts on a new line below the floated content. This ensures proper layout flow and readability.

---

## Example 2: Multiple Floated Elements

<div style="float: left; width: 150px; height: 80px; background: lightcoral; margin: 10px; padding: 10px;">
Left float
</div>

<div style="float: right; width: 150px; height: 80px; background: lightgreen; margin: 10px; padding: 10px;">
Right float
</div>

Text between floated elements can wrap around both of them, which often creates messy layouts.

```{clear}
```

The clear directive ensures this content starts below both floated elements, maintaining a clean layout.

---

## Example 3: Image Layouts

Imagine you have an image floated to the left:

<img src="https://via.placeholder.com/200x150" style="float: left; margin-right: 15px;" alt="Placeholder image" />

This text wraps around the floated image. In many cases, this is desirable for magazine-style layouts. However, sometimes you want the next section to start cleanly below the image.

```{clear}
```

### New Section

This section heading and its content now appear below the image, not wrapped around it. This is especially useful when starting new topics or sections.

---

## Example 4: Practical Use Case

Consider a page with side-by-side content using floats:

<div style="float: left; width: 45%; margin-right: 5%; padding: 10px; background: #f0f0f0;">

**Column 1**

Some content in the first column. This could be text, images, or any other content.

</div>

<div style="float: left; width: 45%; padding: 10px; background: #e0e0e0;">

**Column 2**

Some content in the second column. This creates a two-column layout using floats.

</div>

```{clear}
```

### Full Width Content

After the clear directive, this content spans the full width of the page again, below both columns.

---

## Usage

The syntax is extremely simple:

```markdown
\`\`\`{clear}
\`\`\`
```

That's it! No arguments, no options. Just insert it wherever you need to clear floats.

## When to Use

- ✅ After floated images
- ✅ Between sections with different layouts
- ✅ After multi-column content
- ✅ To prevent text wrapping around floated elements
- ✅ To ensure proper spacing between sections

## CSS Behind the Scenes

The directive simply inserts:

```html
<div style="clear: both;"></div>
```

This CSS property clears both left and right floats, ensuring content flows naturally below.
