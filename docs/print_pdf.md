# Print-Friendly PDF Formatting

This document explains how the print-specific CSS and JavaScript work to create clean, professional PDFs from the web books.

## Overview

When you use "Print to PDF" or "Save as PDF" from your browser, the following transformations happen automatically:

1. ✅ **Tab-sets are flattened** - All tabs show sequentially with part labels (a, b, c, etc.)
2. ✅ **Answers/solutions hidden** - Clean problem sheets without solutions visible
3. ✅ **Answer key generated** - All answers collected on a separate page at the end
4. ✅ **CAS popups hidden** - Interactive buttons removed
5. ✅ **Better page breaks** - Exercises and figures stay together

## Files Involved

### CSS: `_static/pdf_custom.css`
Contains all print-specific styling rules within `@media print { }` blocks.

**Key features:**
- Hides dropdown, interactive elements, and CAS popup buttons
- Flattens tab-set structures to show all tabs sequentially
- Hides answer and solution admonitions from main content
- Styles for the answer key section
- General print improvements (page breaks, contrast, etc.)

### JavaScript: `_static/print_answer_key.js`
Dynamically creates an answer key page when printing.

**Key features:**
- Listens for print events (`beforeprint`/`afterprint`)
- Collects all `.answer` admonitions from the page
- Links each answer to its parent exercise
- Handles tab-item parts (a, b, c, etc.)
- Creates formatted answer key section at the end
- Cleans up after printing (no duplicate content)

### Configuration: `_config.yml`
Registers the CSS and JavaScript files.

```yaml
pdfhtml:
  extra_css:
    - _static/pdf_custom.css
    - _static
  extra_js:
    - _static/print_answer_key.js

html:
  extra_js:
    - _static/print_answer_key.js
    # ... other scripts
```

## How It Works

### 1. Tab-Set Flattening

**Problem:** Interactive tabs don't work in PDF.

**Solution:**
```css
/* Hide tab controls */
.sd-tab-set > input[type="radio"],
.sd-tab-set > input[type="radio"] + label {
    display: none !important;
}

/* Show all tab content sequentially */
.sd-tab-set > .sd-tab-content {
    display: block !important;
    opacity: 1 !important;
}

/* Add part labels */
.sd-tab-content::before {
    content: attr(data-label);
}
```

**Result:** In PDF, you see:
```
Exercise 1

Del a)
[content of tab a]

Del b)
[content of tab b]

Del c)
[content of tab c]
```

### 2. Hiding Answers and Solutions

**Problem:** Students shouldn't see answers on problem sheets.

**Solution:**
```css
.admonition.answer,
.admonition.solution,
.admonition.hints {
    display: none !important;
}
```

**Result:** All answer/solution/hints admonitions are invisible in print.

### 3. Answer Key Generation

**Problem:** Need answers in a separate section for easy lookup.

**Solution:** JavaScript collects answers before printing:

```javascript
function createAnswerKey() {
    // 1. Find all .answer elements
    const answers = document.querySelectorAll('.admonition.answer');
    
    // 2. For each answer:
    //    - Find parent exercise
    //    - Get exercise title/number
    //    - Extract answer content
    //    - Note which part (a, b, c) if in tabs
    
    // 3. Create answer key section
    const answerKeySection = document.createElement('div');
    answerKeySection.className = 'answer-key-section';
    
    // 4. Format answers grouped by exercise
    // 5. Append to end of document
}

window.addEventListener('beforeprint', createAnswerKey);
```

**Result:** A new section appears at the end:
```
============================================
              Fasit
============================================

Oppgave 1
a) x = 5
b) x = 7
c) x = -3

Oppgave 2
42

Oppgave 3
a) ...
```

### 4. CAS Popup Hiding

**Problem:** Popup buttons are meaningless in PDF.

**Solution:**
```css
.cas-popup-button,
.popup-trigger,
.popup-wrapper {
    display: none !important;
}
```

**Result:** CAS popup buttons don't appear in printed version.

### 5. Exercise Formatting

**Problem:** Exercises should stay together, not split across pages.

**Solution:**
```css
.admonition.exercise {
    page-break-inside: avoid;
    margin-bottom: 2em;
    border: 1px solid #ddd;
    padding: 1em;
}
```

**Result:** Each exercise appears as a complete unit on the page.

## How to Use

### For Students: Creating a PDF

1. Open any chapter/page in the book
2. Use your browser's print function:
   - **Chrome/Edge:** Ctrl+P (Cmd+P on Mac)
   - **Firefox:** Ctrl+P (Cmd+P on Mac)
3. Choose "Save as PDF" as the destination
4. Adjust settings:
   - **Layout:** Portrait (usually)
   - **Margins:** Default or Minimal
   - **Background graphics:** ON (to keep colors)
5. Click "Save"

**Result:** Clean PDF with:
- All problems visible
- No answers/solutions in main content
- Answer key on separate pages at the end
- No interactive elements
- Good page breaks

### For Teachers: Customizing

#### Show Answers Inline (Instead of Separate Page)

In `pdf_custom.css`, comment out the "hide answers" section and uncomment the alternative:

```css
/* Comment this out:
.admonition.answer {
    display: none !important;
}
*/

/* Uncomment this: */
.admonition.answer {
    display: block !important;
    border: 2px dashed #4CAF50;
    background: #f0f8f0 !important;
}
```

#### Disable Answer Key Generation

In `print_answer_key.js`, comment out the setup:

```javascript
// Comment this out:
// setupPrintListeners();
```

Or remove the script from `_config.yml`:

```yaml
html:
  extra_js:
    - _static
    # - _static/print_answer_key.js  # Commented out
```

#### Customize Part Labels

In `pdf_custom.css`, change the labels:

```css
.tabs-parts .sd-tab-content:nth-of-type(2)::before {
    content: "Part a)";  /* Changed from "Del a)" */
}
```

#### Show Solutions (Not Just Answers)

In `pdf_custom.css`, change what's hidden:

```css
/* Hide only hints, keep answers and solutions */
.admonition.hints {
    display: none !important;
}

/* Remove these lines to show answers and solutions:
.admonition.answer,
.admonition.solution {
    display: none !important;
}
*/
```

## Testing

### Quick Test

1. Build the book: `jb build matematikk_1t`
2. Open any page with exercises and answers
3. Open browser DevTools (F12)
4. Toggle device emulation to "Print"
5. Check:
   - ✅ Tabs are flattened with labels
   - ✅ Answers hidden in main content
   - ✅ Answer key appears at bottom
   - ✅ CAS buttons hidden
   - ✅ Good page breaks

### Full Test

1. Open a chapter page
2. Press Ctrl+P (Cmd+P)
3. Preview the PDF
4. Verify formatting
5. Save and check the actual PDF file

## Troubleshooting

### Answers Not Appearing in Answer Key

**Possible causes:**
1. JavaScript not loaded
2. Answers not inside `.exercise` admonitions
3. Browser blocking scripts

**Solutions:**
1. Check browser console for errors
2. Verify structure: `exercise > ... > answer`
3. Try different browser

### Tabs Not Flattening

**Possible causes:**
1. Custom CSS overriding print styles
2. Different tab structure than expected

**Solutions:**
1. Check CSS specificity
2. Inspect HTML structure in DevTools
3. Adjust selectors in `pdf_custom.css`

### Page Breaks in Wrong Places

**Possible causes:**
1. Content too long for page
2. `page-break-inside: avoid` not working

**Solutions:**
```css
/* Force break before certain elements */
.exercise {
    page-break-before: auto;
    page-break-inside: avoid;
    page-break-after: auto;
}
```

### CAS Popups Still Showing

**Possible causes:**
1. Different class names
2. CSS not loaded

**Solutions:**
1. Inspect element to find actual class
2. Add to CSS:
```css
.your-cas-class {
    display: none !important;
}
```

## Browser Compatibility

| Browser | Tab Flattening | Answer Key | Page Breaks |
|---------|---------------|------------|-------------|
| Chrome  | ✅            | ✅         | ✅          |
| Firefox | ✅            | ✅         | ⚠️ (limited) |
| Safari  | ✅            | ✅         | ✅          |
| Edge    | ✅            | ✅         | ✅          |

**Note:** Firefox has limited CSS page-break support, but basic functionality works.

## Advanced: Server-Side PDF Generation

For batch PDF generation, consider using:

1. **Playwright/Puppeteer:** Headless Chrome automation
   ```bash
   playwright generate-pdf https://your-book.com/chapter1
   ```

2. **WeasyPrint:** Python-based PDF generator
   ```bash
   weasyprint https://your-book.com/chapter1 chapter1.pdf
   ```

3. **Prince XML:** Commercial solution with excellent CSS support

All of these will respect the print CSS and run the JavaScript.

## Future Enhancements

Potential improvements:

1. **Chapter-specific answer keys** - One key per chapter instead of whole page
2. **QR codes** - Link to online solutions
3. **Difficulty indicators** - Visual marks for problem difficulty
4. **Time estimates** - Expected completion time per exercise
5. **Answer key first page** - Option to put answers before problems (teacher version)

## Contributing

To improve print formatting:

1. Test with different browsers
2. Try various page layouts
3. Check with different content types
4. Submit improvements via pull request

## License

Same as the main project (see LICENSE file).
