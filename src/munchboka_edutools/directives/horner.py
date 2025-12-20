"""
Horner scheme (synthetic division) directive for Sphinx/Jupyter Book.

Generates SVG visualizations of Horner's method/synthetic division using LaTeX.
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


def synthetic_div(
    fname: str,
    p: str,
    x: float,
    stage: int = 12,
    svg: bool = True,
    tutor: bool = False,
):
    """
    Generate Horner scheme (synthetic division) figure using LaTeX.

    Args:
        fname: Base filename (without extension)
        p: Polynomial as string (e.g., "x^3 + 2x^2 - 3x - 6")
        x: Value to evaluate at
        stage: Stage number for step-by-step display (default: 12 = complete)
        svg: If True, convert to SVG; otherwise keep as PDF
        tutor: If True, enable tutor mode with step-by-step guidance
    """
    if not tutor:
        div_cmd = r"\polyhornerscheme[x={x}, resultstyle=\color{red}, showvar=true]{{p}}"
        div_cmd = div_cmd.replace("{p}", p).replace("{x}", str(x))
    else:
        div_cmd = r"\polyhornerscheme[x={x}, stage={stage}, tutor=true, tutorlimit=12, resultstyle=\color{red}, showvar=true]{{p}}"
        div_cmd = div_cmd.replace("{p}", p).replace("{x}", str(x)).replace("{stage}", str(stage))

    s = f"""\\documentclass{{standalone}}
\\usepackage{{polynom}}
\\usepackage{{xcolor}}
\\begin{{document}}
{div_cmd}
\\end{{document}}
    """

    with open("tmp.tex", "w") as f:
        f.write(s)

    os.system("pdflatex tmp.tex")
    if fname.endswith(".svg"):
        fname = fname.strip(".svg")

    if svg:
        os.system(f"pdf2svg tmp.pdf {fname}.svg")
    else:
        os.system(f"mv tmp.pdf {fname}.pdf")

    os.system("rm tmp.*")


class HornerDirective(SphinxDirective):
    """
    Generate (and cache) a Horner (synthetic division) scheme as inline SVG.

    Usage (MyST):

    ```
    ::::{horner}
    :p: x^3 + 2x^2 - 3x - 6
    :x: 1
    :stage: 2      # optional
    :width: 60%    # optional

    Optional caption here.
    ::::
    ```

    Or classic reStructuredText:

    ```
    .. horner::
       :p: x^3 + 2x^2 - 3x - 6
       :x: 1
       :stage: 2

       Optional caption here.
    ```
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        "p": directives.unchanged_required,
        "x": directives.unchanged_required,
        "stage": directives.nonnegative_int,
        "tutor": directives.flag,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "alt": directives.unchanged,
        "width": directives.length_or_percentage_or_unitless,
    }

    def run(self):
        env = self.state.document.settings.env
        app = env.app

        # Required options
        p = self.options.get("p")
        x_val = self.options.get("x")
        if p is None or x_val is None:
            return [
                self.state_machine.reporter.error(
                    "Directive 'horner' requires both :p: and :x: options.",
                    line=self.lineno,
                )
            ]

        # Optional options
        stage = self.options.get("stage", 12)
        tutor_mode = "tutor" in self.options
        explicit_name = self.options.get("name")

        # Cache key must include tutor mode so variants don't collide
        content_hash = _hash_key(p, x_val, stage, int(tutor_mode))
        base_name = explicit_name or f"horner_{content_hash}"

        # Paths / caching
        src_dir = app.srcdir
        rel_dir = os.path.join("_static", "horner")
        abs_dir = os.path.join(src_dir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_filename = f"{base_name}.svg"
        abs_svg_path = os.path.join(abs_dir, svg_filename)

        regenerate = "nocache" in self.options or not os.path.exists(abs_svg_path)
        if regenerate:
            cwd = os.getcwd()
            try:
                os.chdir(abs_dir)
                synthetic_div(
                    fname=base_name,
                    p=p,
                    x=x_val,
                    stage=stage,
                    svg=True,
                    tutor=tutor_mode,
                )
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating Horner scheme: {e}",
                        line=self.lineno,
                    )
                ]
            finally:
                os.chdir(cwd)

        # Post-process: strip explicit width/height if viewBox present for responsiveness
        try:
            if os.path.exists(abs_svg_path):
                with open(abs_svg_path, "r", encoding="utf-8") as f_svg:
                    raw_tmp = f_svg.read()
                if "viewBox" in raw_tmp:
                    cleaned = re.sub(r'\swidth="[^"]+"', "", raw_tmp)
                    cleaned = re.sub(r'\sheight="[^"]+"', "", cleaned)
                    if cleaned != raw_tmp:
                        with open(abs_svg_path, "w", encoding="utf-8") as f_out:
                            f_out.write(cleaned)
        except Exception:
            pass

        if not os.path.exists(abs_svg_path):
            return [
                self.state_machine.reporter.error(
                    (
                        f"horner: failed to generate SVG '{svg_filename}'. "
                        "Check that 'pdflatex' and 'pdf2svg' are installed."
                    ),
                    line=self.lineno,
                )
            ]

        # Track dependency & copy to output for HTML builder
        env.note_dependency(abs_svg_path)
        try:
            out_static = os.path.join(app.outdir, "_static", "horner")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg_path, os.path.join(out_static, svg_filename))
        except Exception:
            pass

        # Alt text construction
        if stage is not None and stage != 12:
            default_alt = f"Horner's scheme for ({p}) at x={x_val} – stage {stage}"
        else:
            default_alt = f"Horner's scheme for ({p}) at x={x_val}"
        if tutor_mode:
            default_alt += " (tutor mode)"
        alt = self.options.get("alt", default_alt)

        width_opt = self.options.get("width")
        percentage_width = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        # Read generated SVG
        try:
            with open(abs_svg_path, "r", encoding="utf-8") as f_svg:
                raw_svg = f_svg.read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"horner inline: could not read SVG: {e}",
                    line=self.lineno,
                )
            ]

        # Ensure unique IDs per embedding
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

        unique_prefix = f"hnr_{_hash_key(p, x_val, stage, int(tutor_mode))}_{uuid.uuid4().hex[:6]}_"
        raw_svg = _uniquify_ids(raw_svg, unique_prefix)

        # Augment root <svg> (unified width handling)
        def _augment(match):
            tag = match.group(0)
            if "class=" not in tag:
                tag = tag[:-1] + ' class="horner-inline-svg"' + ">"
            else:
                tag = tag.replace('class="', 'class="horner-inline-svg ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt}"' + ">"
            if width_opt:
                w_raw = width_opt.strip()
                if percentage_width:
                    w_css = w_raw
                    margin = "margin:0 auto;" if "margin:" not in tag else ""
                    style_frag = f"width:{w_css}; height:auto; display:block; {margin}".strip()
                else:
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

        # Build docutils figure
        figure = nodes.figure()
        figure.setdefault("classes", []).extend(["adaptive-figure", "horner-figure", "no-click"])

        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(["horner-image", "no-click", "no-scaled-link"])
        figure += raw_node

        extra_classes = self.options.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = self.options.get("align", "center")

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
    app.add_directive("horner", HornerDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
