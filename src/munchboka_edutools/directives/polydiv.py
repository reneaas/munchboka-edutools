"""
Polynomial long division directive for Sphinx/Jupyter Book.

Generates SVG visualizations of polynomial long division using LaTeX.
"""

import os
import shutil
import hashlib
import re
import uuid
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


def _hash_key(*parts):
    """Generate a hash key from multiple parts for caching."""
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


def polylongdiv(fname: str, p: str, q: str, stage: int = None, svg: bool = True, vars=None):
    """
    Generate polynomial long division figure using LaTeX.

    Args:
        fname: Base filename (without extension)
        p: Dividend polynomial as string (e.g., "x^3 + 2x^2 - 3x - 6")
        q: Divisor polynomial as string (e.g., "x - 2")
        stage: Optional stage number for step-by-step display
        svg: If True, convert to SVG; otherwise keep as PDF
        vars: Variable(s) used in polynomials (default: "x")
    """
    if not vars:
        vars = "x"

    # Generate unique temp filenames
    temp_id = uuid.uuid4().hex[:8]
    tex_file = f"tmp_{temp_id}.tex"
    pdf_file = f"tmp_{temp_id}.pdf"

    # Format LaTeX command
    if stage is None:
        div_cmd = r"\polylongdiv[style=C, div=:, vars=None]{{p}}{{q}}"
        div_cmd = div_cmd.replace("{p}", p).replace("{q}", q).replace("None", str(vars))
    else:
        div_cmd = r"\polylongdiv[style=C, div=:, stage={stage}]{{p}}{{q}}"
        div_cmd = div_cmd.replace("{p}", p).replace("{q}", q).replace("{stage}", str(stage))

    # Create LaTeX file
    s = f"""\\documentclass[border=0.2cm]{{standalone}}
\\usepackage{{polynom}}
\\begin{{document}}
{div_cmd}
\\end{{document}}
    """

    # Remove .svg extension properly if present
    if fname.endswith(".svg"):
        fname = fname[:-4]

    # Write and process files
    with open(tex_file, "w") as f:
        f.write(s)

    os.system(f"pdflatex {tex_file}")

    if svg:
        os.system(f"pdf2svg {pdf_file} {fname}.svg")
    else:
        os.system(f"mv {pdf_file} {fname}.pdf")

    # Cleanup temp files
    os.system(f"rm tmp_{temp_id}.*")


class PolyDivDirective(SphinxDirective):
    """
    Generate (and cache) a polynomial long division figure as SVG and embed it.

    Usage (MyST):

    ```
    ::::{polydiv}
    :p: x^3 + 2x^2 - 3x - 6
    :q: x - 2
    :stage: 2        # optional
    :vars: x         # optional (default x)
    :align: center   # optional (left|center|right)
    :class: small    # optional extra CSS classes on figure

    Optional caption here.
    ::::
    ```

    Or classic reStructuredText:

    ```
    .. polydiv::
       :p: x^3 + 2x^2 - 3x - 6
       :q: x - 2
       :stage: 2
       :vars: x

       Optional caption here.
    ```
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        "p": directives.unchanged_required,
        "q": directives.unchanged_required,
        "stage": directives.nonnegative_int,
        "vars": directives.unchanged,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,  # optional explicit base filename / ref name
        "cache": directives.flag,  # include to enable (default on)
        "nocache": directives.flag,  # include to force regeneration
        "alt": directives.unchanged,
        "width": directives.length_or_percentage_or_unitless,
        # Always inline now; legacy 'inline' option kept (ignored) for backward compatibility
        "inline": directives.flag,
    }

    def run(self):
        """Main directive entry: always inline-embed generated SVG and allow width control & centering."""
        env = self.state.document.settings.env
        app = env.app

        # Options
        p = self.options.get("p")
        q = self.options.get("q")
        if p is None or q is None:
            return [
                self.state_machine.reporter.error(
                    "Directive 'polydiv' requires both :p: and :q: options.",
                    line=self.lineno,
                )
            ]
        stage = self.options.get("stage")
        vars_opt = self.options.get("vars", "x")
        explicit_name = self.options.get("name")
        content_hash = _hash_key(p, q, stage, vars_opt)
        base_name = explicit_name or f"polydiv_{content_hash}"

        # Paths
        src_dir = app.srcdir
        rel_dir = os.path.join("_static", "polydiv")
        abs_dir = os.path.join(src_dir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_filename = f"{base_name}.svg"
        abs_svg_path = os.path.join(abs_dir, svg_filename)

        regenerate = "nocache" in self.options or not os.path.exists(abs_svg_path)
        if regenerate:
            cwd = os.getcwd()
            try:
                os.chdir(abs_dir)
                polylongdiv(
                    fname=base_name,
                    p=p,
                    q=q,
                    stage=stage,
                    vars=vars_opt,
                )
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating polynomial division: {e}",
                        line=self.lineno,
                    )
                ]
            finally:
                os.chdir(cwd)

        # Post-process: strip width/height for responsiveness if viewBox present
        try:
            if os.path.exists(abs_svg_path):
                with open(abs_svg_path, "r", encoding="utf-8") as f_svg:
                    svg_text_tmp = f_svg.read()
                if "viewBox" in svg_text_tmp:
                    cleaned = re.sub(r'\swidth="[^"]+"', "", svg_text_tmp)
                    cleaned = re.sub(r'\sheight="[^"]+"', "", cleaned)
                    if cleaned != svg_text_tmp:
                        with open(abs_svg_path, "w", encoding="utf-8") as f_out:
                            f_out.write(cleaned)
        except Exception:
            pass

        if not os.path.exists(abs_svg_path):
            return [
                self.state_machine.reporter.error(
                    (
                        f"polydiv: failed to generate SVG '{svg_filename}'. "
                        "Check that 'pdflatex' and 'pdf2svg' are installed."
                    ),
                    line=self.lineno,
                )
            ]

        env.note_dependency(abs_svg_path)
        try:
            out_static = os.path.join(app.outdir, "_static", "polydiv")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg_path, os.path.join(out_static, svg_filename))
        except Exception:
            pass

        # Alt text
        if stage is not None:
            default_alt = f"Polynomial division of ({p}) : ({q}) – stage {stage}"
        else:
            default_alt = f"Polynomial division of ({p}) : ({q})"
        alt = self.options.get("alt", default_alt)

        width_opt = self.options.get("width")
        percentage_width = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        # Read final SVG
        try:
            with open(abs_svg_path, "r", encoding="utf-8") as f_svg:
                raw_svg = f_svg.read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"polydiv inline: could not read SVG: {e}",
                    line=self.lineno,
                )
            ]

        # Uniquify IDs to prevent collisions
        def _uniquify_ids(svg_text: str, prefix: str) -> str:
            ids = set(re.findall(r'\bid="([^"]+)"', svg_text))
            if not ids:
                return svg_text
            mapping = {old: f"{prefix}{old}" for old in ids}
            for old, new in mapping.items():
                svg_text = re.sub(rf'\bid="{re.escape(old)}"', f'id="{new}"', svg_text)
            for old, new in mapping.items():
                svg_text = re.sub(
                    rf'(?:xlink:)?href="#?{re.escape(old)}"', f'href="#{new}"', svg_text
                )
                svg_text = re.sub(
                    rf'xlink:href="#?{re.escape(old)}"',
                    f'xlink:href="#{new}"',
                    svg_text,
                )
            for old, new in mapping.items():
                svg_text = re.sub(rf"url\(#\s*{re.escape(old)}\s*\)", f"url(#{new})", svg_text)
            for old, new in mapping.items():
                svg_text = re.sub(rf"#({re.escape(old)})\b", f"#{new}", svg_text)
            return svg_text

        unique_prefix = f"pd_{_hash_key(p, q, stage, vars_opt)}_{uuid.uuid4().hex[:6]}_"
        raw_svg = _uniquify_ids(raw_svg, unique_prefix)

        # Augment root <svg> (single pass handles both percent and fixed widths)
        def _augment(match):
            tag = match.group(0)
            if "class=" not in tag:
                tag = tag[:-1] + ' class="polydiv-inline-svg"' + ">"
            else:
                tag = tag.replace('class="', 'class="polydiv-inline-svg ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt}"' + ">"
            if width_opt:
                w_raw = width_opt.strip()
                if percentage_width:
                    # percentage width: keep percent, center block
                    w_css = w_raw
                    margin = "margin:0 auto;" if "margin:" not in tag else ""
                    style_frag = f"width:{w_css}; height:auto; display:block; {margin}".strip()
                else:
                    # fixed / unit width: add px if bare number
                    w_css = (w_raw + "px") if w_raw.isdigit() else w_raw
                    style_frag = f"width:{w_css}; height:auto; display:block;"
                if "style=" in tag:
                    tag = re.sub(
                        r'style="([^"]*)"',
                        lambda m: f'style="{m.group(1)}; {style_frag}"',
                        tag,
                        count=1,
                    )
                else:
                    tag = tag[:-1] + f' style="{style_frag}"' + ">"
            return tag

        raw_svg = re.sub(r"<svg\b[^>]*>", _augment, raw_svg, count=1)

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(
            [
                "adaptive-figure",
                "polydiv-figure",
                "no-click",
            ]
        )

        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(
            [
                "polydiv-image",
                "no-click",
                "no-scaled-link",
            ]
        )
        figure += raw_node

        # Extra classes & alignment
        extra_classes = self.options.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = self.options.get("align", "center")

        # Caption
        if self.content:
            caption_node = nodes.caption()
            caption_text = "\n".join(self.content)
            # Parse as inline text to support math while avoiding extra paragraph nodes
            parsed_nodes, messages = self.state.inline_text(caption_text, self.lineno)
            caption_node.extend(parsed_nodes)
            figure += caption_node

        if explicit_name:
            self.add_name(figure)

        return [figure]


def setup(app):
    app.add_directive("polydiv", PolyDivDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
