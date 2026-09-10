"""Bounded textual macro expansion; arithmetic is left to the scene compiler."""
import re

from ._plot_macros import substitute_macro_bindings
from .plot3d_2 import _split_top_level_commas


def expand_macros(lines):
    pending = [(str(line), i, 0) for i, line in enumerate(lines)]
    result, locations, macros = [], [], {}
    uses = 0
    fenced = bool(lines and lines[0].strip() == "---")
    while pending:
        line, source, depth = pending.pop(0)
        stripped = line.strip()
        if len(result) + len(pending) > 5000 or depth > 16:
            raise ValueError("Macro expansion exceeds its limit")
        match = re.fullmatch(r"macro:\s*([A-Za-z]\w*)\((.*?)\)", stripped)
        if match:
            name, args = match.groups()
            params = [a.strip() for a in args.split(",") if a.strip()]
            if len(set(params)) != len(params) or not all(
                re.fullmatch(r"[A-Za-z]\w*", p) for p in params
            ):
                raise ValueError(f"Invalid macro parameters: {args}")
            body = []
            while pending and pending[0][0].strip() != "endmacro":
                body.append(pending.pop(0)[0])
            if not pending:
                raise ValueError(f"Missing endmacro for {name}")
            pending.pop(0)
            macros[name] = (params, body)
            continue
        match = re.fullmatch(r"use:\s*([A-Za-z]\w*)(?:\((.*?)\))?", stripped)
        if match:
            name, args = match.groups()
            if name not in macros:
                raise ValueError(f"Unknown macro: {name}")
            params, body = macros[name]
            values = _split_top_level_commas(args or "")
            if len(params) != len(values):
                raise ValueError(f"Wrong argument count for macro {name}")
            uses += 1
            # Give each invocation its own let/def names before binding arguments.
            local_names = [
                m.group(1)
                for text in body
                if (m := re.match(r"\s*(?:let|def):\s*([A-Za-z]\w*)", text))
            ]
            rename = {n: f"mbmacro{uses}_{n}" for n in local_names}
            generated = [
                substitute_macro_bindings(
                    substitute_macro_bindings(text, rename), dict(zip(params, values))
                )
                for text in body
            ]
            pending[0:0] = [(text, source, depth + 1) for text in generated]
            continue
        if stripped == "endmacro":
            raise ValueError("Unexpected endmacro")
        result.append(line)
        locations.append(source)
        # Do not expand anything inside captions. Opening/closing frontmatter
        # fences and blank lines are part of the existing key/value convention.
        ended_fence = fenced and source > 0 and stripped == "---"
        caption = stripped and stripped != "---" and not re.match(r"[A-Za-z_][\w-]*\s*:", stripped)
        if ended_fence or caption:
            result.extend(text for text, _, _ in pending)
            locations.extend(index for _, index, _ in pending)
            break
    return result, locations
