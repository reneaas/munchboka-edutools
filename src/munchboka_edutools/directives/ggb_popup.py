"""
GeoGebra popup directive for creating interactive GeoGebra applets in dialog windows.

This directive creates a button that opens a GeoGebra Classic applet in a
draggable, resizable dialog window using jQuery UI.

Usage:
    Basic usage with defaults (700x500 window):
    ```{ggb-popup}
    ```

    Custom size and text:
    ```{ggb-popup} 800 600 "Open Calculator" "GeoGebra Calculator"
    ```

    With options:
    ```{ggb-popup} 900 700 "Open Geometry" "Geometry Window"
    :perspective: G
    :menubar: true
    :layout: sidebar
    ```

Arguments (all optional):
    1. Width (default: 700) - Width of the GeoGebra applet in pixels
    2. Height (default: 500) - Height of the GeoGebra applet in pixels
    3. Button text (default: "Åpne Geogebra‑vindu") - Text shown on the button
    4. Dialog title (default: "Geogebra‑vindu") - Title of the dialog window

Options:
    - perspective: GeoGebra perspective/view (default: "AG")
      Common values: "AG" (Algebra & Graphics), "G" (Geometry), "GS" (Graphing), "CAS"
    - menubar: Show menu bar (default: "false") - "true" or "false"
    - layout: Layout style (default: none) - Use "sidebar" to wrap in sidebar-cas div

Features:
    - Draggable and resizable dialog window
    - GeoGebra Classic applet with full features
    - Responsive sizing when dialog is resized
    - Centered on screen when opened
    - jQuery UI styling
"""

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
import uuid


class GGBPopUpDirective(SphinxDirective):
    """
    Directive for creating GeoGebra popup windows.

    Creates a button that opens a GeoGebra Classic applet in a jQuery UI dialog.
    """

    required_arguments = 0
    optional_arguments = 4  # width, height, button text, dialog title
    final_argument_whitespace = True
    has_content = False
    option_spec = {
        "layout": lambda arg: arg,  # e.g., "sidebar"
        "menubar": lambda arg: arg,  # e.g., "true" or "false"
        "perspective": lambda arg: arg,  # e.g., "GS"
    }

    def run(self):
        """Generate HTML for the GeoGebra popup."""
        # 1 » Parse arguments
        width = int(self.arguments[0]) if len(self.arguments) > 0 else 700
        height = int(self.arguments[1]) if len(self.arguments) > 1 else 500

        button_text = self.arguments[2] if len(self.arguments) > 2 else "Åpne Geogebra‑vindu"
        dialog_title = self.arguments[3] if len(self.arguments) > 3 else "Geogebra‑vindu"

        menubar = self.options.get("menubar", "false")

        perspective = self.options.get("perspective", "AG").strip()

        # 2 » Generate unique IDs
        cid = f"ggb-geogebra-{uuid.uuid4().hex[:8]}"
        dialog_id = f"dialog-{cid}"
        button_id = f"button-{cid}"

        # 3 » Handle layout option
        layout = self.options.get("layout", "").strip().lower()
        use_sidebar = layout == "sidebar"

        wrapper_start = '<div class="sidebar-cas">' if use_sidebar else ""
        wrapper_end = "</div>" if use_sidebar else ""

        # 4 » Generate HTML content
        html = f"""
{wrapper_start}
<meta name="viewport" content="width=device-width, initial-scale=1">

<button id="{button_id}" class="ggb-cas-button">{button_text}</button>
<div id="{dialog_id}" title="{dialog_title}" style="display:none;">
    <div id="{cid}" class="ggb-window"></div>
</div>

<style>
.ui-resizable-handle {{ min-width:16px;min-height:16px; }}
.ui-dialog-content{{padding:0!important;}}
.ggb-window       {{width:100%!important;height:100%!important;box-sizing:border-box;}}
.ggb-popup-button {{margin-top: 1em; margin-bottom: 1em;}}
.ggb-reset-btn {{
  position: absolute;
  right: 2.5em;
  top: 50%;
  transform: translateY(-50%);
  width: 2em;
  height: 2em;
  padding: 0.25em;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  opacity: 0.7;
}}
.ggb-reset-btn:hover {{
  opacity: 1;
  background-color: rgba(0, 0, 0, 0.1);
}}
[data-theme="dark"] .ggb-reset-btn:hover,
html[data-theme="dark"] .ggb-reset-btn:hover {{
  background-color: rgba(255, 255, 255, 0.1);
}}
.ggb-reset-btn svg {{
  color: inherit;
}}
</style>

<script>
(function() {{
  $(function() {{
    let ggbReady = false;
    const storageKey = 'ggb-geogebra-state-{cid}';

    function applySize() {{
      if (!ggbReady) return;
      const w = $("#{cid}").width(),
            h = $("#{cid}").height();
      window.ggbApplet.setSize(Math.round(w), Math.round(h));
    }}

    function saveState() {{
      if (!ggbReady || !window.ggbApplet) return;
      try {{
        const state = window.ggbApplet.getBase64();
        localStorage.setItem(storageKey, state);
        // Update timestamp for this state
        localStorage.setItem(storageKey + '-timestamp', Date.now().toString());
      }} catch (e) {{
        // If quota exceeded, try cleaning up old states and retry
        if (e.name === 'QuotaExceededError') {{
          cleanupOldStates();
          try {{
            const state = window.ggbApplet.getBase64();
            localStorage.setItem(storageKey, state);
            localStorage.setItem(storageKey + '-timestamp', Date.now().toString());
          }} catch (retryError) {{
            // Still failed after cleanup - silently give up
          }}
        }}
      }}
    }}

    function cleanupOldStates() {{
      try {{
        // Find all GeoGebra states with timestamps (both CAS and regular)
        const ggbStates = [];
        for (let i = 0; i < localStorage.length; i++) {{
          const key = localStorage.key(i);
          if (key && (key.startsWith('ggb-geogebra-state-') || key.startsWith('ggb-cas-state-')) && key.endsWith('-timestamp')) {{
            const stateKey = key.replace('-timestamp', '');
            const timestamp = parseInt(localStorage.getItem(key) || '0', 10);
            ggbStates.push({{ key: stateKey, timestamp: timestamp }});
          }}
        }}
        
        // Sort by timestamp (oldest first)
        ggbStates.sort((a, b) => a.timestamp - b.timestamp);
        
        // Delete oldest 25% of states (minimum 1, maximum 10)
        const numToDelete = Math.max(1, Math.min(10, Math.floor(ggbStates.length * 0.25)));
        for (let i = 0; i < numToDelete && i < ggbStates.length; i++) {{
          localStorage.removeItem(ggbStates[i].key);
          localStorage.removeItem(ggbStates[i].key + '-timestamp');
        }}
      }} catch (e) {{
        // Cleanup failed - silently continue
      }}
    }}

    function restoreState() {{
      if (!ggbReady || !window.ggbApplet) return;
      try {{
        const savedState = localStorage.getItem(storageKey);
        if (savedState) {{
          window.ggbApplet.setBase64(savedState);
        }}
      }} catch (e) {{
        // Silently fail if restore fails
      }}
    }}

    $("#{dialog_id}").dialog({{
      autoOpen: false,
      width: {width+40}, height: {height+80},
      resizable: true, draggable: true,
      position: {{ my: "center", at: "center", of: window }},
      resize: () => window.requestAnimationFrame(applySize),
      open: function() {{
        if (!ggbReady) {{
          new GGBApplet({{
            appName: "classic", id: "{cid}",
            width: {width}, height: {height},
            perspective: "{perspective}", language: "nb",
            showToolBar: true, showAlgebraInput: true,
            borderRadius: 8, enableRightClick: true, showKeyboardOnFocus: false,
            showMenuBar: {menubar},
            appletOnLoad: () => {{ 
              ggbReady = true; 
              applySize();
              // Restore state after a short delay to ensure GeoGebra is fully initialized
              setTimeout(restoreState, 100);
            }}
          }}, true).inject("{cid}");
        }} else {{
          applySize();
        }}
      }},
      close: function() {{
        // Save state when dialog is closed
        saveState();
      }}
    }});

    // Add refresh button to title bar
    const $dlg = $("#{dialog_id}");
    const titleBar = $dlg.parent().find('.ui-dialog-titlebar');
    const refreshBtn = $('<button type="button" class="ggb-reset-btn" title="Start på nytt (slett lagret innhold)"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M13.65 2.35C12.2 0.9 10.21 0 8 0 3.58 0 0.01 3.58 0.01 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L9 7h7V0l-2.35 2.35z" fill="currentColor"/></svg></button>');
    refreshBtn.on('click', function() {{
      if (confirm('Er du sikker på at du vil slette lagret innhold og starte på nytt?')) {{
        try {{
          localStorage.removeItem(storageKey);
          localStorage.removeItem(storageKey + '-timestamp');
          if (ggbReady && window.ggbApplet) {{
            // Clear the container
            $("#{cid}").empty();
            // Reset the flag
            ggbReady = false;
            // Recreate the applet from scratch
            new GGBApplet({{
              appName: "classic", id: "{cid}",
              width: {width}, height: {height},
              perspective: "{perspective}", language: "nb",
              showToolBar: true, showAlgebraInput: true,
              borderRadius: 8, enableRightClick: true, showKeyboardOnFocus: false,
              showMenuBar: {menubar},
              appletOnLoad: () => {{ 
                ggbReady = true; 
                applySize();
              }}
            }}, true).inject("{cid}");
          }}
        }} catch (e) {{
          console.error('Failed to reset:', e);
        }}
      }}
    }});
    titleBar.append(refreshBtn);

    // Save state when page is unloaded (refresh, navigate away, close tab)
    $(window).on('beforeunload', function() {{
      if ($dlg.dialog('isOpen')) {{
        saveState();
      }}
    }});

    $("#{button_id}").button()
      .on("click touchend pointerup", e => {{
        e.preventDefault();
        $("#{dialog_id}").dialog("open");
      }});
  }});
}})();
</script>
{wrapper_end}
        """
        return [nodes.raw("", html, format="html")]


def setup(app):
    """Register the ggb-popup directive with Sphinx."""
    app.add_directive("ggb-popup", GGBPopUpDirective)
    # Also register without hyphen for MyST compatibility
    app.add_directive("ggbpopup", GGBPopUpDirective)

    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
