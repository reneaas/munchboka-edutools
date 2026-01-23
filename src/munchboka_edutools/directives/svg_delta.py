"""SVG Delta Engine
================

Computes differences between SVG frames to minimize storage and enable
efficient multi-variable interactive graphs.

Instead of storing N full SVG files, we store:
- 1 base SVG (static elements)
- N delta objects (only the changes)

This reduces storage from O(N × size) to O(1 × size + N × changes).
For typical interactive graphs: 100MB → 2-5MB (95-98% reduction).
"""

import json
import re
from typing import Dict, List, Tuple, Any

import xml.etree.ElementTree as ET


_SVG_XML_DECL_RE = re.compile(r"<\?xml[^?]*\?>", flags=re.IGNORECASE)
_SVG_DOCTYPE_RE = re.compile(r"<!DOCTYPE[^>]*>", flags=re.IGNORECASE)
_SVG_METADATA_RE = re.compile(r"<metadata[\s\S]*?</metadata>", flags=re.IGNORECASE)


def _prepare_svg_for_deltas(svg: str) -> str:
    """Prepare SVGs for delta computation without breaking rendering.

    Goals:
    - Strip non-visual metadata that changes per render (dc:date etc.)
    - Assign deterministic ids to elements that *lack* an id (so we can track
      geometry changes on anonymous <path> etc. across frames)

    Important: we do NOT overwrite existing ids, and we do NOT rewrite url(#..)
    references here. Many Matplotlib ids are stable already (line2d_*, text_*).
    """
    cleaned = _SVG_XML_DECL_RE.sub("", svg)
    cleaned = _SVG_DOCTYPE_RE.sub("", cleaned)
    cleaned = _SVG_METADATA_RE.sub("", cleaned)

    try:
        from lxml import etree as LET
    except ImportError:
        return cleaned

    try:
        parser = LET.XMLParser(recover=False, remove_blank_text=False, huge_tree=True)
        root = LET.fromstring(cleaned.encode("utf-8"), parser)
    except Exception:
        # Fall back to the cleaned raw SVG if strict parsing fails.
        return cleaned

    counters: Dict[str, int] = {}

    for elem in root.iter():
        if not isinstance(elem.tag, str):
            continue
        if elem.get("id"):
            continue

        local = LET.QName(elem).localname
        # Skip top-level/structural nodes that rarely need ids.
        if local in ("svg", "defs", "style", "metadata", "title", "desc"):
            continue

        idx = counters.get(local, 0)
        counters[local] = idx + 1
        elem.set("id", f"{local}_{idx}")

    return LET.tostring(root, encoding="unicode")


def compute_svg_deltas(svg_frames: List[str]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Compute deltas between SVG frames.

    Args:
        svg_frames: List of SVG strings (one per frame)

    Returns:
        Tuple of (base_svg, deltas) where:
        - base_svg: First frame with all elements
        - deltas: List of frame-specific changes
    """
    if not svg_frames:
        raise ValueError("Need at least one frame")

    # Prepare SVGs so deltas become meaningful: remove metadata noise and add
    # deterministic ids for anonymous elements.
    prepared_frames = [_prepare_svg_for_deltas(s) for s in svg_frames]

    # Use first frame as base
    base_svg = prepared_frames[0]

    # Parse frames with lxml which handles namespaces better
    try:
        from lxml import etree as LET

        use_lxml = True
    except ImportError:
        use_lxml = False
        import xml.etree.ElementTree as ET

    try:
        if use_lxml:
            # lxml handles namespaces gracefully
            parser = LET.XMLParser(recover=True, remove_blank_text=True)
            trees = [LET.fromstring(svg.encode("utf-8"), parser) for svg in prepared_frames]
            base_tree = trees[0]
        else:
            # Fallback to ET - remove namespaces manually
            cleaned_frames = []
            for svg in prepared_frames:
                # Remove xmlns declarations
                cleaned = re.sub(r'\s+xmlns[^=]*="[^"]*"', "", svg)
                cleaned_frames.append(cleaned)
            trees = [ET.fromstring(svg) for svg in cleaned_frames]
            base_tree = trees[0]
    except Exception as e:
        raise ValueError(f"Failed to parse SVG frames: {e}")

    # Build element index for base (id -> element)
    base_elements = {}
    for elem in base_tree.iter():
        # Get tag without namespace
        if use_lxml:
            # For lxml, need to handle QName properly
            tag_str = str(elem.tag) if elem.tag is not None else ""
            tag = tag_str.split("}")[-1] if "}" in tag_str else tag_str
        else:
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        elem_id = elem.get("id")
        if elem_id:
            base_elements[elem_id] = elem

    def _has_text_ancestor_lxml(elem) -> bool:
        """Return True if elem is inside a Matplotlib text group (id startswith 'text_')."""
        if not use_lxml:
            return False
        parent = elem.getparent()
        while parent is not None:
            pid = parent.get("id")
            if pid and pid.startswith("text_"):
                return True
            parent = parent.getparent()
        return False

    def _is_xlink_href(attr_name: str) -> bool:
        # lxml uses Clark notation for namespaced attrs: "{ns}local"
        return attr_name.endswith("}href") and attr_name.startswith(
            "{http://www.w3.org/1999/xlink}"
        )

    # Compute deltas for each frame
    deltas = []

    for frame_idx, tree in enumerate(trees):
        frame_delta = {"frame": frame_idx, "changes": {}}

        # Find all elements with IDs in current frame
        for elem in tree.iter():
            elem_id = elem.get("id")
            if not elem_id:
                continue

            # Robust text handling: Matplotlib often represents text as a group
            # (`<g id="text_...">`) containing a variable number of glyph nodes.
            # When text length changes, the internal structure changes, making
            # per-glyph deltas brittle. Instead, for the top-level text group we
            # replace the whole subtree via `outerHTML`.
            if use_lxml and elem_id.startswith("text_"):
                base_elem = base_elements.get(elem_id)
                if base_elem is None:
                    continue
                try:
                    cur_html = LET.tostring(elem, encoding="unicode")
                    base_html = LET.tostring(base_elem, encoding="unicode")
                except Exception:
                    cur_html = None
                    base_html = None

                if cur_html is not None and cur_html != base_html:
                    frame_delta["changes"][elem_id] = {"outerHTML": cur_html}
                continue

            # If this element is under a text group, skip it.
            if use_lxml and _has_text_ancestor_lxml(elem):
                continue

            base_elem = base_elements.get(elem_id)
            if base_elem is None:
                continue

            # Compare attributes
            changes = {}

            # Check all attributes in current element
            for attr, value in elem.attrib.items():
                if attr == "id":
                    continue
                # Ignore noisy internal-reference attributes that often change
                # due to non-deterministic Matplotlib ids (notably clipPath ids).
                if attr in ("clip-path",):
                    continue

                # Matplotlib often regenerates marker <defs> ids on each render,
                # which causes many <use xlink:href="#m..."> diffs.
                # Those references point to ids that do NOT exist in our base.svg
                # (since we only keep base defs), so applying them makes markers
                # (including point primitives) disappear.
                if _is_xlink_href(attr) and isinstance(value, str) and value.startswith("#m"):
                    base_value = base_elem.get(attr)
                    if isinstance(base_value, str) and base_value.startswith("#m"):
                        continue

                base_value = base_elem.get(attr)
                if value != base_value:
                    changes[attr] = value

            # Check for removed attributes
            for attr in base_elem.attrib:
                if attr == "id":
                    continue
                if attr in ("clip-path",):
                    continue
                if _is_xlink_href(attr):
                    base_value = base_elem.get(attr)
                    cur_value = elem.get(attr)
                    if (
                        isinstance(base_value, str)
                        and base_value.startswith("#m")
                        and isinstance(cur_value, str)
                    ):
                        # Keep the base marker reference even if Matplotlib drops/changes it.
                        continue
                if attr not in elem.attrib:
                    changes[attr] = None

            # Compare text content
            elem_text = (elem.text or "").strip()
            base_text = (base_elem.text or "").strip()
            if elem_text != base_text:
                changes["textContent"] = elem_text

            # NOTE: we intentionally do NOT include tail text changes.
            # The runtime JS skips tailContent (non-visual in our SVGs).

            # If there are changes, add to delta
            if changes:
                frame_delta["changes"][elem_id] = changes

        deltas.append(frame_delta)

    return base_svg, deltas


def save_delta_format(base_svg: str, deltas: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Save delta format to disk.

    Args:
        base_svg: Base SVG string
        deltas: List of delta objects
        output_dir: Directory to save files
    """
    import os

    os.makedirs(output_dir, exist_ok=True)

    # Save base SVG
    base_path = os.path.join(output_dir, "base.svg")
    with open(base_path, "w", encoding="utf-8") as f:
        f.write(base_svg)

    # Save deltas as JSON
    deltas_path = os.path.join(output_dir, "deltas.json")
    with open(deltas_path, "w", encoding="utf-8") as f:
        json.dump(deltas, f, separators=(",", ":"))  # Compact JSON

    # Save metadata
    metadata = {"frame_count": len(deltas), "format_version": "1.0", "compression": "delta"}
    meta_path = os.path.join(output_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def generate_delta_html(
    base_svg_url: str,
    deltas_json_url: str,
    unique_id: str,
    var_name: str,
    var_values: List[float],
    initial_idx: int = 0,
    wrapper_style: str = "",
    height: str = "auto",
) -> str:
    """
    Generate HTML for delta-based interactive graph.

    Args:
        base_svg_url: URL to base SVG
        deltas_json_url: URL to deltas JSON
        unique_id: Unique identifier for this graph
        var_name: Variable name to display
        var_values: List of variable values
        initial_idx: Initial frame index
        wrapper_style: CSS style for wrapper div (alignment, width)
        height: Height CSS value for SVG

    Returns:
        HTML string with delta application JavaScript
    """
    var_min = var_values[0]
    var_max = var_values[-1]
    initial_value = var_values[initial_idx]
    values_js = "[" + ",".join(f"{v:.10f}" for v in var_values) + "]"

    return f"""
<div class="interactive-graph-wrapper" style="{wrapper_style}">
    <div class="interactive-graph-container" style="display: inline-block; width: 100%;">
        <div class="interactive-graph-display" style="text-align: center;">
            <div id="svg-container-{unique_id}" class="adaptive-figure" style="width: 100%; display: block;"></div>
        </div>
        <div class="interactive-graph-controls" style="padding: 8px 0; text-align: center;">
            <div style="display: flex; align-items: center; gap: 10px; max-width: 600px; margin: 0 auto;">
                <span style="font-family: monospace; min-width: 40px; text-align: right; font-size: 14px;">{var_min:.2f}</span>
                <input type="range" 
                       id="interactive-slider-{unique_id}"
                       class="interactive-slider"
                       min="0" 
                       max="{len(var_values) - 1}" 
                       value="{initial_idx}"
                       step="1"
                       style="flex: 1; cursor: pointer; -webkit-appearance: none; appearance: none; height: 8px; border-radius: 5px; background: #ddd; outline: none;">
                <span style="font-family: monospace; min-width: 40px; text-align: left; font-size: 14px;">{var_max:.2f}</span>
            </div>
            <div style="margin-top: 10px; font-family: monospace; font-size: 16px; font-weight: bold;">
                <span id="interactive-value-{unique_id}">{var_name} = {initial_value:.2f}</span>
            </div>
        </div>
    </div>
</div>

<style>
.interactive-slider::-webkit-slider-thumb {{
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2196F3;
    cursor: pointer;
}}

.interactive-slider::-moz-range-thumb {{
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2196F3;
    cursor: pointer;
    border: none;
}}
</style>

<script>
(function() {{
    const uniqueId = '{unique_id}';
    const baseSvgUrl = '{base_svg_url}';
    const deltasJsonUrl = '{deltas_json_url}';
    const values = {values_js};
    const varName = '{var_name}';
    
    console.log('Initializing delta graph:', uniqueId);
    console.log('Base SVG URL:', baseSvgUrl);
    console.log('Deltas JSON URL:', deltasJsonUrl);
    
    const container = document.getElementById('svg-container-' + uniqueId);
    const slider = document.getElementById('interactive-slider-' + uniqueId);
    const valueDisplay = document.getElementById('interactive-value-' + uniqueId);
    
    if (!container) {{
        console.error('Container not found:', 'svg-container-' + uniqueId);
        return;
    }}
    if (!slider) {{
        console.error('Slider not found:', 'interactive-slider-' + uniqueId);
        return;
    }}

    function latexForVarName(name) {{
        const greek = {{
            alpha: '\\\\alpha', beta: '\\\\beta', gamma: '\\\\gamma', delta: '\\\\delta',
            epsilon: '\\\\epsilon', zeta: '\\\\zeta', eta: '\\\\eta', theta: '\\\\theta',
            iota: '\\\\iota', kappa: '\\\\kappa', lambda: '\\\\lambda', mu: '\\\\mu',
            nu: '\\\\nu', xi: '\\\\xi', pi: '\\\\pi', rho: '\\\\rho', sigma: '\\\\sigma',
            tau: '\\\\tau', upsilon: '\\\\upsilon', phi: '\\\\phi', chi: '\\\\chi',
            psi: '\\\\psi', omega: '\\\\omega',
            varphi: '\\\\varphi', vartheta: '\\\\vartheta'
        }};
        if (greek[name]) return greek[name];
        if (name.includes('_') || /\\d/.test(name)) return name;
        if (/^[A-Za-z]$/.test(name)) return name;
        return name;
    }}

    const varLatex = latexForVarName(varName);

    function updateValueDisplay(index) {{
        const v = values[index];
        const vStr = (typeof v === 'number' ? v.toFixed(2) : String(v));
        if (window.katex && valueDisplay) {{
            try {{
                valueDisplay.innerHTML = window.katex.renderToString(varLatex + ' = ' + vStr, {{
                    throwOnError: false,
                    displayMode: false,
                }});
                return;
            }} catch (e) {{
                // fall through
            }}
        }}
        valueDisplay.textContent = varName + ' = ' + vStr;
    }}
    
    let svgDoc = null;
    let deltas = null;
    let svgElements = {{}};  // Cache of ID -> element
    let pendingFrame = null;
    
    console.log('Starting fetch...');
    
    // Load base SVG and deltas
    Promise.all([
        fetch(baseSvgUrl).then(r => {{
            console.log('Base SVG response:', r.status, r.statusText);
            if (!r.ok) throw new Error('Failed to load base SVG: ' + r.status + ' ' + r.statusText);
            return r.text();
        }}),
        fetch(deltasJsonUrl).then(r => {{
            console.log('Deltas JSON response:', r.status, r.statusText);
            if (!r.ok) throw new Error('Failed to load deltas JSON: ' + r.status + ' ' + r.statusText);
            return r.json();
        }})
    ]).then(([svgText, deltasData]) => {{
        console.log('SVG text length:', svgText.length);
        console.log('Deltas count:', deltasData.length);
        
        // Remove XML declaration, DOCTYPE, and metadata with undeclared namespaces
        svgText = svgText.replace(/<\\?xml[^?]*\\?>/g, '');
        svgText = svgText.replace(/<!DOCTYPE[^>]*>/g, '');
        svgText = svgText.replace(/<metadata>[\\s\\S]*?<\\/metadata>/g, '');
        
        // Parse as SVG XML to ensure correct namespaces/paint behavior.
        // (Parsing as text/html can turn the SVG into plain HTML elements,
        // especially if serialization introduces prefixed tags like ns0:svg.)
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgText, 'image/svg+xml');

        const parserError = doc.querySelector('parsererror');
        if (parserError) {{
            console.error('SVG XML parse error:', parserError.textContent);
            throw new Error('Failed to parse base.svg as SVG XML');
        }}

        const svgElement = doc.documentElement;
        if (!svgElement || svgElement.localName !== 'svg') {{
            console.error('No SVG element found after parsing');
            throw new Error('No SVG element found in loaded content');
        }}

        // Import the SVG into the current document
        const importedSvg = document.importNode(svgElement, true);

        container.innerHTML = '';
        container.appendChild(importedSvg);
        svgDoc = importedSvg;
        deltas = deltasData;
        
        console.log('SVG element found:', !!svgDoc);
        
        if (!svgDoc) {{
            throw new Error('No SVG element found in loaded content');
        }}
        
        console.log('Styling SVG...');
        // Style the SVG for responsive sizing
        svgDoc.style.width = '100%';
        svgDoc.style.height = '{height}';
        svgDoc.style.display = 'block';
        svgDoc.classList.add('adaptive-figure');
        
        console.log('Building element cache...');
        // Build element cache
        buildElementCache();
        
        console.log('Element cache size:', Object.keys(svgElements).length);
        console.log('Applying initial frame...');
        
        // Apply initial frame
        applyDelta(parseInt(slider.value));
        
        console.log('Attaching event listeners...');
        console.log('SVG dimensions:', svgDoc.getBoundingClientRect());
        console.log('Container dimensions:', container.getBoundingClientRect());
        
        // Attach event listeners AFTER SVG is loaded
        slider.addEventListener('input', updateFrame);
        slider.addEventListener('change', updateFrame);
        slider.addEventListener('touchmove', updateFrame);
        
        // Keyboard navigation
        slider.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {{
                e.preventDefault();
                this.value = Math.max(0, parseInt(this.value) - 1);
                updateFrame();
            }} else if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {{
                e.preventDefault();
                this.value = Math.min({len(var_values) - 1}, parseInt(this.value) + 1);
                updateFrame();
            }}
        }});
        
        console.log('Delta-based graph loaded:', uniqueId, deltas.length, 'frames');
    }}).catch(err => {{
        console.error('Failed to load delta graph:', err);
        container.innerHTML = '<p style="color: red; padding: 20px;">Failed to load interactive graph: ' + err.message + '</p>';
    }});
    
    function buildElementCache() {{
        if (!svgDoc) return;
        svgElements = {{}};
        svgDoc.querySelectorAll('[id]').forEach(elem => {{
            svgElements[elem.id] = elem;
        }});
    }}
    
    function applyDelta(frameIndex) {{
        console.log('applyDelta called with frameIndex:', frameIndex);
        if (!deltas || frameIndex < 0 || frameIndex >= deltas.length) return;
        
        const delta = deltas[frameIndex];
        console.log('Applying delta with', Object.keys(delta.changes).length, 'element changes');
        
        let didReplaceOuterHtml = false;

        function parseNamespacedAttr(attr) {{
            // Supports:
            // - Clark notation from lxml/ElementTree (namespace + localname)
            // - Double-brace encoding (JSON-safe alternative)
            //
            // NOTE: This string is emitted from a Python f-string; avoid
            // literal brace characters in this JS source.

            if (!attr || attr.length < 3) return null;

            const LBRACE = 123; // left brace
            const RBRACE = 125; // right brace

            if (attr.charCodeAt(0) !== LBRACE) return null;

            // Double-brace encoding: starts with '{{'
            if (attr.length >= 4 && attr.charCodeAt(1) === LBRACE) {{
                // Find the first occurrence of '}}' after position 2
                for (let i = 2; i < attr.length - 1; i++) {{
                    if (attr.charCodeAt(i) === RBRACE && attr.charCodeAt(i + 1) === RBRACE) {{
                        const ns = attr.slice(2, i);
                        const local = attr.slice(i + 2);
                        if (ns && local) return {{ ns, local }};
                        return null;
                    }}
                }}
                return null;
            }}

            // Clark notation: starts with '{' and has a single closing '}'
            const close = attr.indexOf(String.fromCharCode(RBRACE));
            if (close <= 1) return null;
            const ns = attr.slice(1, close);
            const local = attr.slice(close + 1);
            if (!ns || !local) return null;
            return {{ ns, local }};
        }}

        function replaceWithOuterHtml(existingElem, outerHtml) {{
            try {{
                // Parse fragment by wrapping it in an <svg> root so namespaces work.
                const parser = new DOMParser();
                const wrapper = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">' + outerHtml + '</svg>';
                const doc = parser.parseFromString(wrapper, 'image/svg+xml');
                const parserError = doc.querySelector('parsererror');
                if (parserError) {{
                    console.error('outerHTML parse error:', parserError.textContent);
                    return;
                }}
                const replacement = doc.documentElement.firstElementChild;
                if (!replacement) return;
                const imported = document.importNode(replacement, true);
                existingElem.replaceWith(imported);
                didReplaceOuterHtml = true;
            }} catch (e) {{
                console.error('Failed to apply outerHTML delta:', e);
            }}
        }}

        // Apply each change
        for (const [elemId, changes] of Object.entries(delta.changes)) {{
            const elem = svgElements[elemId];
            if (!elem) continue;
            
            for (const [attr, value] of Object.entries(changes)) {{
                if (attr === 'outerHTML') {{
                    replaceWithOuterHtml(elem, value);
                }} else if (attr === 'textContent') {{
                    elem.textContent = value;
                }} else if (attr === 'tailContent') {{
                    // Tail text is text after the element (rare in SVG)
                    // For now, skip this
                }} else if (value === null) {{
                    // Handle namespaced attributes for removal
                    const nsInfo = parseNamespacedAttr(attr);
                    if (nsInfo) {{
                        elem.removeAttributeNS(nsInfo.ns, nsInfo.local);
                    }} else {{
                        elem.removeAttribute(attr);
                    }}
                }} else {{
                    // Handle namespaced attributes (xlink and similar).
                    const nsInfo = parseNamespacedAttr(attr);
                    if (nsInfo) {{
                        elem.setAttributeNS(nsInfo.ns, nsInfo.local, value);
                    }} else {{
                        elem.setAttribute(attr, value);
                    }}
                }}
            }}
        }}

        // If we replaced any subtree, rebuild cache so subsequent deltas can
        // find newly created nodes by id.
        if (didReplaceOuterHtml) {{
            buildElementCache();
        }}
        
        // Update value display
        updateValueDisplay(frameIndex);
    }}
    
    function updateFrame() {{
        const index = parseInt(slider.value);
        console.log('updateFrame called, slider value:', index);
        
        if (pendingFrame !== null) {{
            cancelAnimationFrame(pendingFrame);
        }}
        
        pendingFrame = requestAnimationFrame(() => {{
            applyDelta(index);
            pendingFrame = null;
        }});
    }}
}})();
</script>
"""
