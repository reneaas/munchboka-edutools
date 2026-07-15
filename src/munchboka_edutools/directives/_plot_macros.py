"""Macro expansion for plot-like directives."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class PlotMacroContext:
    """Macro context for plot-style directives."""

    sympy_locals: dict[str, Any]
    numeric_functions: dict[str, Callable[..., float]]
    raw_bindings: tuple = ()


def sympy_allowed_base() -> dict[str, Any]:
    """Return a conservative SymPy locals dict for sympify()."""

    import sympy

    return {
        name: getattr(sympy, name)
        for name in [
            "pi",
            "E",
            "exp",
            "sqrt",
            "log",
            "sin",
            "cos",
            "tan",
            "asin",
            "acos",
            "atan",
            "Rational",
            "erf",
        ]
        if hasattr(sympy, name)
    }


def split_top_level_commas(text: str) -> list[str]:
    """Split a string on commas that are not nested inside brackets."""

    if not text.strip():
        return []
    out: list[str] = []
    cur: list[str] = []
    depth = 0
    for ch in text:
        if ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth = max(0, depth - 1)
            cur.append(ch)
        elif ch == "," and depth == 0:
            token = "".join(cur).strip()
            if token:
                out.append(token)
            cur = []
        else:
            cur.append(ch)
    tail = "".join(cur).strip()
    if tail:
        out.append(tail)
    return out


def format_macro_replacement(value: str) -> str:
    """Format a macro substitution value conservatively for text replacement."""

    s = str(value).strip()
    if not s:
        return s
    if re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$", s):
        return s
    if re.match(r"^[A-Za-z_]\w*$", s):
        return s
    if re.match(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$", s):
        return s
    if (s.startswith("(") and s.endswith(")")) or (s.startswith("[") and s.endswith("]")):
        return s
    return f"({s})"


def substitute_macro_bindings(text: str, bindings: dict[str, str]) -> str:
    """Substitute macro parameter names with bound expressions."""

    out = str(text)
    for name, value in bindings.items():
        out = re.sub(
            rf"\b{re.escape(name)}\b",
            format_macro_replacement(value),
            out,
        )
    return out


def replace_identifier_tokens(
    text: str,
    mapping: dict[str, str],
    exclude: set[str] | None = None,
) -> str:
    """Replace identifier tokens using a mapping, excluding specific names."""

    if not mapping:
        return text
    exclude = exclude or set()

    def repl(match: re.Match) -> str:
        token = match.group(0)
        if token in exclude:
            return token
        return mapping.get(token, token)

    return re.sub(r"\b[A-Za-z_]\w*\b", repl, text)


def rename_macro_locals_in_line(
    text: str,
    rename_map: dict[str, str],
    let_re: re.Pattern,
    def_re: re.Pattern,
) -> str:
    """Apply hygienic renaming for macro-local let/def bindings in one line."""

    stripped = text.strip()
    m_let = let_re.match(stripped)
    if m_let:
        name, expr_s = m_let.group(1), m_let.group(2)
        new_name = rename_map.get(name, name)
        new_expr = replace_identifier_tokens(expr_s, rename_map)
        return f"let: {new_name} = {new_expr}"

    m_def = def_re.match(stripped)
    if m_def:
        fname, arglist_s, body_s = m_def.group(1), m_def.group(2), m_def.group(3)
        arg_names = [part.strip() for part in arglist_s.split(",") if part.strip()]
        new_name = rename_map.get(fname, fname)
        new_body = replace_identifier_tokens(body_s, rename_map, exclude=set(arg_names))
        return f"def: {new_name}({', '.join(arg_names)}) = {new_body}"

    return replace_identifier_tokens(text, rename_map)


def parse_plot_macros(lines: list[str]) -> tuple[list[str], PlotMacroContext]:
    """Expand let/def/repeat macros in front matter.

    Supported macros:
    - ``let: NAME = EXPR``
    - ``def: fname(arg1[, arg2, ...]) = EXPR``
    - ``repeat: n=a..b; any supported front-matter line``
    - ``macro: name(arg1[, arg2, ...])`` ... ``endmacro``
    - ``use: name(expr1[, expr2, ...])``
    """

    import sympy

    let_re = re.compile(r"^let\s*:\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*$")
    def_re = re.compile(
        r"^def\s*:\s*([A-Za-z_]\w*)\s*\(\s*([^()]*)\s*\)\s*=\s*(.+?)\s*$"
    )
    macro_re = re.compile(r"^macro\s*:\s*([A-Za-z_]\w*)\s*\(\s*([^()]*)\s*\)\s*$")
    use_re = re.compile(r"^use\s*:\s*([A-Za-z_]\w*)(?:\s*\(\s*(.*?)\s*\))?\s*$")
    repeat_re = re.compile(
        r"^repeat\s*:\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*\.\.\s*(.+?)\s*;\s*(.+?)\s*$"
    )

    fm_start = 0
    fm_end = 0
    fenced = False
    if lines and lines[0].strip() == "---":
        fenced = True
        fm_start = 1
        idx = 1
        while idx < len(lines) and lines[idx].strip() != "---":
            idx += 1
        fm_end = idx
    else:
        macro_depth = 0
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if macro_depth > 0:
                fm_end = idx + 1
                if macro_re.match(stripped):
                    macro_depth += 1
                elif stripped == "endmacro":
                    macro_depth = max(0, macro_depth - 1)
                continue
            if not stripped:
                fm_end = idx + 1
                continue
            if macro_re.match(stripped):
                macro_depth = 1
                fm_end = idx + 1
                continue
            if re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line.rstrip()):
                fm_end = idx + 1
                continue
            break

    base_locals: dict[str, Any] = sympy_allowed_base()
    sympy_locals: dict[str, Any] = {}
    numeric_functions: dict[str, Callable[..., float]] = {}
    macros: dict[str, tuple[list[str], list[str]]] = {}
    raw_binding_lines: list[str] = []

    def _sympify(expr_s: str, extra: dict[str, Any] | None = None):
        loc = {**base_locals, **sympy_locals}
        if extra:
            loc.update(extra)
        return sympy.sympify(expr_s, locals=loc)

    def _parse_int(expr_s: str) -> int:
        v = _sympify(expr_s).evalf()
        f = float(v)
        i = int(round(f))
        if abs(f - i) > 1e-9:
            raise ValueError(f"repeat bounds must be integers, got: {expr_s}")
        return i

    def _subst_word(text: str, var: str, replacement: str) -> str:
        return re.sub(rf"\b{re.escape(var)}\b", replacement, text)

    def _parse_arg_names(arglist_s: str) -> list[str]:
        names = [part.strip() for part in arglist_s.split(",") if part.strip()]
        if not names:
            raise ValueError("def requires at least one argument")
        ident_re = re.compile(r"^[A-Za-z_]\w*$")
        if any(not ident_re.match(name) for name in names):
            raise ValueError(f"invalid def argument list: {arglist_s}")
        return names

    def _parse_macro_param_names(arglist_s: str) -> list[str]:
        if not arglist_s.strip():
            return []
        names = [part.strip() for part in arglist_s.split(",") if part.strip()]
        ident_re = re.compile(r"^[A-Za-z_]\w*$")
        if any(not ident_re.match(name) for name in names):
            raise ValueError(f"invalid macro parameter list: {arglist_s}")
        return names

    expanded_fm: list[str] = []
    pending_lines = list(lines[fm_start:fm_end])
    max_expanded_lines = 20000
    macro_use_counter = 0

    while pending_lines:
        raw = pending_lines.pop(0)
        line = raw.rstrip("\n")
        if not line.strip():
            expanded_fm.append(raw)
            continue

        m_macro = macro_re.match(line.strip())
        if m_macro:
            macro_name = m_macro.group(1)
            try:
                macro_params = _parse_macro_param_names(m_macro.group(2))
                macro_body: list[str] = []
                macro_depth = 1
                while pending_lines:
                    next_raw = pending_lines.pop(0)
                    next_line = next_raw.rstrip("\n")
                    next_stripped = next_line.strip()
                    if macro_re.match(next_stripped):
                        macro_depth += 1
                        macro_body.append(next_line.lstrip())
                        continue
                    if next_stripped == "endmacro":
                        macro_depth -= 1
                        if macro_depth == 0:
                            break
                        macro_body.append(next_line.lstrip())
                        continue
                    macro_body.append(next_line.lstrip())
                macros[macro_name] = (macro_params, macro_body)
            except Exception:
                expanded_fm.append(raw)
            continue

        if line.strip() == "endmacro":
            expanded_fm.append(raw)
            continue

        m_let = let_re.match(line.strip())
        if m_let:
            name, expr_s = m_let.group(1), m_let.group(2)
            raw_binding_lines.append(f"let:{name}={expr_s.strip()}")
            try:
                sympy_locals[name] = _sympify(expr_s)
            except Exception:
                pass
            continue

        m_def = def_re.match(line.strip())
        if m_def:
            fname, arglist_s, body_s = m_def.group(1), m_def.group(2), m_def.group(3)
            raw_binding_lines.append(f"def:{fname}({arglist_s.strip()})={body_s.strip()}")
            try:
                arg_names = _parse_arg_names(arglist_s)
                arg_symbols = sympy.symbols(", ".join(arg_names))
                if not isinstance(arg_symbols, tuple):
                    arg_symbols = (arg_symbols,)
                body_expr = _sympify(
                    body_s,
                    extra={name: symbol for name, symbol in zip(arg_names, arg_symbols)},
                )
                lambda_args: Any = arg_symbols[0] if len(arg_symbols) == 1 else arg_symbols
                sympy_locals[fname] = sympy.Lambda(lambda_args, body_expr)
                fn_np = sympy.lambdify(lambda_args, body_expr, modules=["numpy"])

                def _make_num(fn):
                    return lambda *xs: float(fn(*[float(x) for x in xs]))

                numeric_functions[fname] = _make_num(fn_np)
            except Exception:
                pass
            continue

        m_use = use_re.match(line.strip())
        if m_use:
            macro_name = m_use.group(1)
            if macro_name in macros:
                params, body_lines = macros[macro_name]
                arg_text = m_use.group(2) or ""
                arg_values = split_top_level_commas(arg_text)
                if len(arg_values) == len(params):
                    bindings = {name: value for name, value in zip(params, arg_values)}
                    generated = [substitute_macro_bindings(body, bindings) for body in body_lines]
                    local_names: set[str] = set()
                    for body in generated:
                        stripped_body = body.strip()
                        m_local_let = let_re.match(stripped_body)
                        if m_local_let:
                            local_names.add(m_local_let.group(1))
                            continue
                        m_local_def = def_re.match(stripped_body)
                        if m_local_def:
                            local_names.add(m_local_def.group(1))
                    if local_names:
                        macro_use_counter += 1
                        rename_map = {
                            name: f"__mb_macro_{macro_name}_{macro_use_counter}_{name}"
                            for name in sorted(local_names)
                        }
                        generated = [
                            rename_macro_locals_in_line(body, rename_map, let_re, def_re)
                            for body in generated
                        ]
                    if len(expanded_fm) + len(pending_lines) + len(generated) > max_expanded_lines:
                        expanded_fm.append(raw)
                    else:
                        pending_lines = generated + pending_lines
                    continue
            expanded_fm.append(raw)
            continue

        m_rep = repeat_re.match(line.strip())
        if m_rep:
            var, a_s, b_s, template = (
                m_rep.group(1),
                m_rep.group(2),
                m_rep.group(3),
                m_rep.group(4),
            )
            try:
                a = _parse_int(a_s)
                b = _parse_int(b_s)
                step = 1 if b >= a else -1
                generated: list[str] = []
                for k in range(a, b + step, step):
                    generated.append(_subst_word(template, var, str(k)))
                if len(expanded_fm) + len(pending_lines) + len(generated) > max_expanded_lines:
                    expanded_fm.append(raw)
                else:
                    pending_lines = generated + pending_lines
            except Exception:
                expanded_fm.append(raw)
            continue

        expanded_fm.append(raw)

    if fenced:
        out = [lines[0]] + expanded_fm
        if fm_end < len(lines) and lines[fm_end].strip() == "---":
            out.append(lines[fm_end])
            out.extend(lines[fm_end + 1 :])
        else:
            out.extend(lines[fm_end:])
        return out, PlotMacroContext(
            sympy_locals=sympy_locals,
            numeric_functions=numeric_functions,
            raw_bindings=tuple(sorted(raw_binding_lines)),
        )

    out = expanded_fm + lines[fm_end:]
    return out, PlotMacroContext(
        sympy_locals=sympy_locals,
        numeric_functions=numeric_functions,
        raw_bindings=tuple(sorted(raw_binding_lines)),
    )


_parse_plot_macros = parse_plot_macros


__all__ = [
    "PlotMacroContext",
    "format_macro_replacement",
    "parse_plot_macros",
    "rename_macro_locals_in_line",
    "replace_identifier_tokens",
    "split_top_level_commas",
    "substitute_macro_bindings",
    "sympy_allowed_base",
]
