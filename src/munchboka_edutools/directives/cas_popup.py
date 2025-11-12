"""
CAS Popup Directive
===================

A Sphinx directive that creates a button which opens a GeoGebra CAS (Computer Algebra System)
window in a popup dialog. The dialog can be resized, dragged, and positioned anywhere on the page.

Features:
- Customizable button text and dialog title
- Configurable width and height
- Sidebar layout option for floating the button to the side
- Scroll-locking when interacting with GeoGebra
- Responsive resizing
- Theme-aware styling (light/dark mode)

Dependencies:
- jQuery UI (for dialog functionality)
- GeoGebra API (loaded via geogebra-setup.js)

Usage Examples:
--------------

Basic usage (default 350x500 CAS window):
```
.. cas-popup::
```

Custom size with 600x700 window:
```
.. cas-popup:: 600 700
```

Custom button text and dialog title:
```
.. cas-popup:: 400 600 "Open Calculator" "My CAS Window"
```

Sidebar layout (floating button):
```
.. cas-popup:: 350 500 "CAS" "Calculator"
   :layout: sidebar
```

Author: Original implementation from matematikk_r1
"""

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
import uuid


class CASPopUpDirective(SphinxDirective):
    """
    Directive to create a popup GeoGebra CAS window.

    Arguments:
        1. width (optional): Width of the CAS window in pixels (default: 350)
        2. height (optional): Height of the CAS window in pixels (default: 500)
        3. button_text (optional): Text displayed on the button (default: "Åpne CAS‑vindu")
        4. dialog_title (optional): Title of the popup dialog (default: "CAS‑vindu")

    Options:
        :layout: Set to "sidebar" to float the button to the right side of the page
    """

    required_arguments = 0
    optional_arguments = 4  # width, height, button text, dialog title
    final_argument_whitespace = True
    has_content = False
    option_spec = {
        "layout": lambda arg: arg,  # e.g., "sidebar"
    }

    def run(self):
        # 1 » parse args -----------------------------------------------------
        width = int(self.arguments[0]) if len(self.arguments) > 0 else 350
        height = int(self.arguments[1]) if len(self.arguments) > 1 else 500

        button_text = self.arguments[2] if len(self.arguments) > 2 else "Åpne CAS‑vindu"
        dialog_title = self.arguments[3] if len(self.arguments) > 3 else "CAS‑vindu"

        # 2 » unique IDs -----------------------------------------------------
        cid = f"ggb-cas-{uuid.uuid4().hex[:8]}"
        dialog_id = f"dialog-{cid}"
        button_id = f"button-{cid}"

        # 3 » layout option --------------------------------------------------
        layout = self.options.get("layout", "").strip().lower()
        use_sidebar = layout == "sidebar"

        wrapper_start = '<div class="sidebar-cas">' if use_sidebar else ""
        wrapper_end = "</div>" if use_sidebar else ""

        # 4 » HTML content ---------------------------------------------------
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
.ggb-cas-button   {{margin-top: 1em; margin-bottom: 1em;}}
</style>

<script>
(function() {{
  $(function() {{
    let ggbReady = false;

    function applySize() {{
      if (!ggbReady) return;
      const w = $("#{cid}").width(),
            h = $("#{cid}").height();
      window.ggbApplet.setSize(Math.round(w), Math.round(h));
    }}

    const $dlg = $("#{dialog_id}").dialog({{
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
            perspective: "C", language: "nb",
            showToolBar: true, showAlgebraInput: true,
            borderRadius: 8, enableRightClick: true, showKeyboardOnFocus: false,
            customToolBar: "1001 | 1002 | 1007 | 1010 | 6",
            appletOnLoad: () => {{ ggbReady = true; applySize(); }}
          }}, true).inject("{cid}");
        }} else {{
          applySize();
        }}
      }}
    }});

    // Prevent background scroll when GeoGebra applet is active
    let scrollLocked = false;
    let lockedScrollTop = 0;
    let keyHandler = null;
    let wheelHandler = null;
    let scrollHandler = null;
    
    function lockScroll() {{
      if (scrollLocked) return;
      scrollLocked = true;
      lockedScrollTop = window.pageYOffset || document.documentElement.scrollTop || 0;
      
      // Instead of preventing keys, monitor and restore scroll position
      scrollHandler = () => {{
        if (scrollLocked) {{
          const currentScroll = window.pageYOffset || document.documentElement.scrollTop || 0;
          if (currentScroll !== lockedScrollTop) {{
            window.scrollTo(0, lockedScrollTop);
          }}
        }}
      }};
      
      // Prevent wheel scrolling on the page background
      wheelHandler = (e) => {{
        const dialogElement = e.target.closest('.ui-dialog');
        if (dialogElement) {{
          // Allow scrolling within dialog elements that can scroll
          let target = e.target;
          while (target && target !== dialogElement) {{
            const overflow = window.getComputedStyle(target).overflow;
            if (overflow === 'auto' || overflow === 'scroll') {{
              return; // Allow internal scrolling
            }}
            target = target.parentElement;
          }}
          // Prevent page scroll but don't stop the event from reaching GeoGebra
          if (!e.target.closest('#{cid}')) {{
            e.preventDefault();
            e.stopPropagation();
          }}
        }}
      }};
      
      // Monitor scroll events to maintain position
      window.addEventListener('scroll', scrollHandler, {{ passive: true }});
      document.addEventListener('wheel', wheelHandler, {{ capture: true, passive: false }});
    }}
    
    function unlockScroll() {{
      if (!scrollLocked) return;
      scrollLocked = false;
      
      if (scrollHandler) {{
        window.removeEventListener('scroll', scrollHandler);
        scrollHandler = null;
      }}
      if (wheelHandler) {{
        document.removeEventListener('wheel', wheelHandler, {{ capture: true }});
        wheelHandler = null;
      }}
    }}
    
    // Monitor GeoGebra applet focus/interaction to control scroll lock
    function bindScrollLock() {{
      const ggbContainer = document.getElementById('{cid}');
      if (!ggbContainer) {{
        setTimeout(bindScrollLock, 300);
        return;
      }}
      
      // Look for the actual GeoGebra canvas/applet elements
      const ggbApplet = ggbContainer.querySelector('canvas') || 
                       ggbContainer.querySelector('.ggbApplet') ||
                       ggbContainer.querySelector('[id^="ggbApplet"]') ||
                       ggbContainer;
      
      if (ggbApplet) {{
        // Lock scroll when interacting with GeoGebra
        ggbApplet.addEventListener('mousedown', lockScroll);
        ggbApplet.addEventListener('focus', lockScroll);
        ggbApplet.addEventListener('click', lockScroll);
        
        // Also monitor the container for any focus events
        ggbContainer.addEventListener('focusin', lockScroll);
        ggbContainer.addEventListener('mousedown', lockScroll);
        
        // Unlock when clicking outside or losing focus
        document.addEventListener('click', (e) => {{
          if (!ggbContainer.contains(e.target) && !e.target.closest('.ui-dialog')) {{
            unlockScroll();
          }}
        }});
        
        ggbContainer.addEventListener('focusout', (e) => {{
          // Small delay to check if focus moved outside the container
          setTimeout(() => {{
            if (!ggbContainer.contains(document.activeElement)) {{
              unlockScroll();
            }}
          }}, 100);
        }});
      }}
    }}
    
    // Start monitoring after GeoGebra is loaded
    setTimeout(bindScrollLock, 1000);
    
    // Cleanup on dialog close
    $dlg.on('dialogclose', unlockScroll);

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
    """Register the directive with Sphinx."""
    app.add_directive("cas-popup", CASPopUpDirective)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
