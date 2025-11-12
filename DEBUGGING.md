# Debugging Interactive Code

## Steps to Debug

1. **Open the page in your browser:**
   ```
   file:///Users/reneaas/codes/vgs_books/munchboka-edutools/book/_build/html/examples/interactive_code.html
   ```

2. **Open Browser Console** (press F12 or Cmd+Option+I on Mac)

3. **Look for these specific errors:**

   a. **"makeInteractiveCode is not defined"**
      - This means the scripts aren't loading in the right order
      - Check the Console > Sources tab to see which scripts loaded

   b. **"CodeMirror is not defined"**
      - This means CodeMirror CDN didn't load
      - Check Network tab for failed requests

   c. **"Worker failed to initialize"**
      - This means Pyodide isn't loading in the Web Worker
      - Could be CORS issue or CDN problem

   d. **"Failed to load packages"**
      - Package loading issue
      - Check if Pyodide CDN is accessible

   e. **No errors but no output**
      - Click "Run" button and watch Console
      - Look for ANY console.log messages
      - Check if buttons are clickable

4. **Test the minimal HTML file:**
   ```
   file:///Users/reneaas/codes/vgs_books/munchboka-edutools/book/_build/html/test_minimal.html
   ```
   
   If this works but the Jupyter Book page doesn't, it's a build issue.

5. **Compare with working version:**
   Open the working original and check its console:
   ```
   file:///Users/reneaas/codes/vgs_books/matematikk_r1/_build/html/book/potenser_og_logaritmer/oppgavesamling/oppgaver.html
   ```
   
   Look for console.log messages when you click Run.

## What to Report Back

Please copy-paste:
1. ALL console errors (red text)
2. ALL console warnings (yellow text)  
3. Any console.log messages that appear
4. Whether the "Run" button is visible and clickable
5. Whether the code editor appears with syntax highlighting
6. Whether test_minimal.html works

## Expected Console Output (when working)

When clicking "Run", you should see console.log messages like:
- "InteractiveCodeSetup - Preload packages: ..."
- "Unique ID: ..."
- "Packages to load: ..."
- "Preload packages in WorkerManager: ..."

If you see NONE of these, the JavaScript isn't running at all.
