"""
Sign Chart 2 Directive for Munchboka Edutools
==============================================

An improved sign chart directive with embedded plotting logic that supports:
- Polynomial functions
- Rational functions
- Transcendental functions (sin, cos, exp, log, etc.)
- Custom domains for numerical zero finding
- Flexible styling options

Usage in MyST Markdown:
    ```{signchart-2}
    ---
    function: x**2 - 4, f(x)
    factors: true
    domain: (-5, 5)
    width: 100%
    ---
    Optional caption text
    ```

Features:
    - Automatic factorization and zero finding
    - Support for singularities (poles/discontinuities)
    - Numerical zero finding for transcendental functions
    - Configurable colors, labels, and figure sizes
    - SVG output with theme-aware styling
    - Caching for faster builds

Author: René Aasen
Date: January 2026
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import uuid
import platform
import warnings
from typing import Any, Dict, List, Tuple

import numpy as np
import matplotlib.pyplot as plt
import sympy as sp

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


# ------------------------------------
# LaTeX Configuration
# ------------------------------------

# Check if LaTeX is available
if platform.system() == "Windows":
    latex_available = shutil.which("latex.exe") is not None
else:
    latex_available = shutil.which("latex") is not None

if latex_available:
    try:
        plt.rc("text", usetex=True)
    except (FileNotFoundError, RuntimeError):
        plt.rc("text", usetex=False)
else:
    plt.rc("text", usetex=False)


# ------------------------------------
# Core Plotting Functions
# ------------------------------------


def get_zeros_and_singularities(f, x, domain=None):
    """Find zeros and singularities (poles/discontinuities) of arbitrary functions.

    Args:
        f: sympy expression
        x: variable symbol
        domain: optional tuple (x_min, x_max) to search for numerical zeros

    Returns:
        dict with 'zeros' and 'singularities' lists containing symbolic/numeric values
    """
    zeros = []
    singularities = []

    # Detect singularities FIRST (for rational/transcendental functions)
    try:
        # Check denominator for rational functions
        numer, denom = f.as_numer_denom()
        if denom != 1:
            denom_zeros = sp.solve(denom, x, domain=sp.S.Reals)
            for z in denom_zeros:
                if z.is_real or (hasattr(z, "is_real") and z.is_real is not False):
                    singularities.append(z)
    except:
        pass

    # Try symbolic solving for zeros
    try:
        symbolic_zeros = sp.solve(f, x, domain=sp.S.Reals)
        if symbolic_zeros:
            for z in symbolic_zeros:
                if z.is_real or (hasattr(z, "is_real") and z.is_real is not False):
                    # Make sure this isn't a singularity
                    is_sing = False
                    for sing in singularities:
                        try:
                            if abs(float((z - sing).evalf())) < 1e-10:
                                is_sing = True
                                break
                        except:
                            pass
                    if not is_sing:
                        zeros.append(z)
    except (NotImplementedError, ValueError):
        pass

    # For transcendental/complex functions, find numerical zeros if domain provided
    if domain:
        try:
            # Sample points to find sign changes
            x_min, x_max = domain
            test_points = np.linspace(float(x_min), float(x_max), 1000)
            f_lamb = sp.lambdify(x, f, modules=["numpy"])

            # Suppress warnings for evaluation at singularities
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                y_vals = []
                valid_x = []
                for xp in test_points:
                    try:
                        yp = float(f_lamb(xp))
                        # Exclude points near singularities
                        near_sing = False
                        for sing in singularities:
                            try:
                                if abs(xp - float(sing.evalf())) < 1e-4:
                                    near_sing = True
                                    break
                            except:
                                pass
                        if not near_sing and np.isfinite(yp) and abs(yp) < 1e10:
                            y_vals.append(yp)
                            valid_x.append(xp)
                    except:
                        pass

                y_vals = np.array(y_vals)
                valid_x = np.array(valid_x)

                # Find sign changes (potential zeros) and near-zero values
                numerical_zeros = []
                if len(y_vals) > 1:
                    # Check for sign changes
                    signs = np.sign(y_vals)
                    sign_changes = np.where(np.diff(signs) != 0)[0]

                    for idx in sign_changes:
                        # Skip if both values are zero (avoid duplicates)
                        if abs(y_vals[idx]) < 1e-10 and abs(y_vals[idx + 1]) < 1e-10:
                            continue
                        # Refine zero location
                        try:
                            from scipy.optimize import brentq

                            x_zero = brentq(f_lamb, valid_x[idx], valid_x[idx + 1], xtol=1e-10)
                            numerical_zeros.append(sp.Float(x_zero))
                        except:
                            # Use midpoint if brentq fails
                            x_zero = (valid_x[idx] + valid_x[idx + 1]) / 2
                            numerical_zeros.append(sp.Float(x_zero))

                    # Also check for near-zero values at sample points
                    near_zero_idx = np.where(np.abs(y_vals) < 1e-10)[0]
                    for idx in near_zero_idx:
                        x_val = sp.Float(valid_x[idx])
                        # Verify it's actually a zero by checking nearby points
                        # (avoid singularities that happen to evaluate near zero)
                        try:
                            y_val = float(f_lamb(float(x_val)))
                            eps = 1e-6
                            y_left = float(f_lamb(float(x_val) - eps))
                            y_right = float(f_lamb(float(x_val) + eps))
                            # Only add if function is continuous and actually crosses zero
                            if np.isfinite(y_left) and np.isfinite(y_right) and abs(y_val) < 1e-8:
                                # Avoid duplicates
                                if not any(abs(float(z - x_val)) < 1e-8 for z in numerical_zeros):
                                    numerical_zeros.append(x_val)
                        except:
                            pass

                # Merge symbolic and numerical zeros, removing duplicates and singularities
                all_zeros = list(zeros)  # Start with symbolic zeros
                for nz in numerical_zeros:
                    # Check if this is actually a singularity
                    is_singularity = False
                    for sing in singularities:
                        try:
                            if abs(float(sing.evalf() - nz.evalf())) < 1e-6:
                                is_singularity = True
                                break
                        except:
                            pass

                    if is_singularity:
                        continue  # Skip singularities

                    # Check if this zero is already in the list (symbolic or numeric)
                    is_duplicate = False
                    for z in all_zeros:
                        try:
                            if abs(float(z.evalf() - nz.evalf())) < 1e-8:
                                is_duplicate = True
                                break
                        except:
                            pass
                    if not is_duplicate:
                        all_zeros.append(nz)

                zeros = all_zeros
        except:
            pass

    return {"zeros": zeros, "singularities": singularities}


def get_factors(polynomial, x):
    """Get factors for polynomial functions (legacy support)."""
    polynomial = sp.expand(polynomial)
    factor_list = sp.factor_list(polynomial)
    # SymPy's factor_list may leave leading coefficients inside factors (e.g., 2*x*(2*x**2-3*a**2)),
    # which makes the displayed overall coefficient misleading. We normalize factors to be monic in `x`
    # by absorbing each factor's leading coefficient into the overall coefficient.
    leading_coeff = factor_list[0]

    # We'll add the overall coefficient as its own factor after we've normalized the remaining
    # factors (so the displayed coefficient is the true leading coefficient in x).
    linear_factors: List[Dict[str, Any]] = []

    for linear_factor, exponent in factor_list[1]:
        exponent = int(exponent)

        # Normalize factor to be monic in x (when possible), and move its leading coefficient into
        # the overall coefficient so the leading coefficient shown matches sp.LC(polynomial, x).
        try:
            factor_lc = sp.LC(linear_factor, x)
        except Exception:
            factor_lc = 1

        if factor_lc not in (0, 1, sp.Integer(1)):
            leading_coeff = sp.simplify(leading_coeff * (factor_lc**exponent))
            linear_factor = sp.simplify(linear_factor / factor_lc)

        roots = sp.solve(linear_factor, x)

        # Handle factors that may have multiple real roots (e.g., quadratics like x^2 - 2)
        if not roots:
            linear_factors.append(
                {
                    "expression": linear_factor,
                    "exponent": exponent,
                    "root": -np.inf,
                }
            )
        else:
            # For each root of the factor, create a separate entry with the correct exponent
            for root_value in roots:
                # Only include roots that are real or not provably non-real.
                # For parameter-dependent roots (e.g. involving `a`), SymPy often
                # returns `is_real is None` unless assumptions are attached.
                if root_value.is_real is not False:
                    # Store both the expression (for evaluation) and a display LaTeX string.
                    # SymPy's default latex() often reorders addition as `c + x`, which is
                    # visually unusual in this context; we want `x + c` / `x - c`.
                    if root_value == 0:
                        expression_latex = sp.latex(x)
                    elif getattr(root_value, "could_extract_minus_sign", lambda: False)():
                        expression_latex = f"{sp.latex(x)} + {sp.latex(-root_value)}"
                    else:
                        expression_latex = f"{sp.latex(x)} - {sp.latex(root_value)}"

                    linear_factors.append(
                        {
                            "expression": x - root_value,
                            "expression_latex": expression_latex,
                            "exponent": exponent,  # Use the actual exponent from factorization
                            "root": root_value,
                        }
                    )

    if leading_coeff != 1:
        linear_factors.insert(0, {"expression": leading_coeff, "exponent": 1, "root": -np.inf})

    return linear_factors


def get_transcendental_factors(f, x, zeros, singularities):
    """Extract factors from transcendental or composite functions.

    Args:
        f: sympy expression
        x: variable symbol
        zeros: list of zeros found numerically/symbolically
        singularities: list of singularities (poles)

    Returns:
        list of factor dictionaries (one per unique expression+exponent, with all roots)
    """
    factors = []

    # First check if it's a rational function with transcendental parts
    try:
        numer, denom = f.as_numer_denom()
        if denom != 1 and not (denom.is_polynomial() and numer.is_polynomial()):
            # Transcendental rational function - process numerator and denominator separately
            # Process numerator
            numer_factors = _extract_factors_from_expression(numer, x, zeros, [])
            factors.extend(numer_factors)

            # Process denominator
            denom_factors = _extract_factors_from_expression(denom, x, [], singularities)
            factors.extend(denom_factors)

            return factors
    except:
        pass

    # Not a rational function, process as a single expression
    return _extract_factors_from_expression(f, x, zeros, singularities)


def _extract_factors_from_expression(expr, x, zeros, singularities):
    """Helper function to extract factors from a single expression (not a rational function).

    Args:
        expr: sympy expression (numerator or denominator)
        x: variable symbol
        zeros: zeros to associate with this expression
        singularities: singularities to associate with this expression

    Returns:
        list of factor dictionaries
    """
    factors = []

    try:
        # Try to factor the expression
        factored = sp.factor(expr)

        # Check if it's a power expression (e.g., cos(x)**3)
        if factored.is_Pow:
            base = factored.base
            exponent = int(factored.exp) if factored.exp.is_integer else 1

            # Find zeros of the base
            base_zeros = []
            try:
                base_zeros_sym = sp.solve(base, x, domain=sp.S.Reals)
                for z in base_zeros_sym:
                    if z.is_real:
                        # Match with known zeros
                        for known_zero in zeros:
                            try:
                                if abs(float(z.evalf()) - float(known_zero.evalf())) < 1e-8:
                                    base_zeros.append(known_zero)
                                    break
                            except:
                                pass
            except:
                # If symbolic solve fails, use all known zeros
                base_zeros = zeros

            # Create single factor with all zeros
            if base_zeros:
                factors.append(
                    {
                        "expression": base,
                        "exponent": exponent,
                        "roots": base_zeros,  # Changed: store all roots together
                    }
                )

        # If it's a product, try to extract individual factors
        elif factored.is_Mul:
            # Group factors by (expression, exponent) to avoid duplicates
            factor_dict = {}

            for arg in factored.args:
                # Check if this arg is a power
                if arg.is_Pow:
                    base = arg.base
                    exponent = int(arg.exp) if arg.exp.is_integer else 1
                    expr_to_use = base
                else:
                    expr_to_use = arg
                    exponent = 1

                # Create a key for grouping
                key = (str(expr_to_use), exponent)

                if key not in factor_dict:
                    factor_dict[key] = {
                        "expression": expr_to_use,
                        "exponent": exponent,
                        "zeros": [],
                        "singularities": [],
                    }

                # Find zeros of this factor
                try:
                    arg_zeros = sp.solve(expr_to_use, x, domain=sp.S.Reals)
                    for z in arg_zeros:
                        if z.is_real:
                            # Check if this zero is in our list
                            for known_zero in zeros:
                                try:
                                    if abs(float(z.evalf()) - float(known_zero.evalf())) < 1e-8:
                                        if known_zero not in factor_dict[key]["zeros"]:
                                            factor_dict[key]["zeros"].append(known_zero)
                                        break
                                except:
                                    pass
                except:
                    pass

                # Check for singularities in denominator
                try:
                    numer, denom = expr_to_use.as_numer_denom()
                    if denom != 1:
                        denom_zeros = sp.solve(denom, x, domain=sp.S.Reals)
                        for z in denom_zeros:
                            if z.is_real:
                                for known_sing in singularities:
                                    try:
                                        if abs(float(z.evalf()) - float(known_sing.evalf())) < 1e-8:
                                            if known_sing not in factor_dict[key]["singularities"]:
                                                factor_dict[key]["singularities"].append(known_sing)
                                            break
                                    except:
                                        pass
                except:
                    pass

            # Convert grouped factors to list
            # Include ALL factors, even those without zeros/singularities
            for factor_info in factor_dict.values():
                all_roots = factor_info["zeros"] + factor_info["singularities"]
                # Always add the factor, even if it has no roots
                factors.append(
                    {
                        "expression": factor_info["expression"],
                        "exponent": factor_info["exponent"],
                        "roots": all_roots if all_roots else [],
                    }
                )
        else:
            # Not a product or power, show as single factor
            all_roots = zeros + singularities
            factors.append(
                {
                    "expression": factored,
                    "exponent": 1,
                    "roots": all_roots if all_roots else [],
                }
            )
    except:
        # Fallback: just use the original expression
        all_roots = zeros + singularities
        factors.append(
            {
                "expression": expr,
                "exponent": 1,
                "roots": all_roots if all_roots else [],
            }
        )

    return factors


def sort_factors(factors):
    def get_numeric_root(factor, subs: Dict[sp.Symbol, float] | None = None):
        # Handle both old format ("root") and new format ("roots")
        if "roots" in factor and factor["roots"]:
            # For new format, use the first root for sorting
            root = factor["roots"][0]
        elif "root" in factor:
            root = factor.get("root")
        else:
            # No roots - sort to end
            return np.inf

        if root == -np.inf or root is None:
            return -np.inf
        try:
            # Try to convert symbolic roots to float for comparison
            if subs:
                return float(sp.N(sp.sympify(root).subs(subs)))
            return float(sp.N(sp.sympify(root)))
        except (AttributeError, TypeError):
            try:
                return float(root)
            except:
                return -np.inf

    factors = sorted(factors, key=lambda f: get_numeric_root(f, subs=None))
    return factors


def _parse_domain_option(domain_val: Any) -> Tuple[Tuple[float, float] | None, str | None]:
    """Parse the directive `domain:` option.

    Back-compat: if `domain` parses as a 2-tuple of floats, treat it as x-domain
    for numerical zero finding.

    New: otherwise treat it as parameter assumptions, e.g. `a > 0`.
    """
    if domain_val is None:
        return None, None

    s = str(domain_val).strip()
    if not s:
        return None, None

    tup = _parse_tuple(s, float)
    if tup and len(tup) == 2:
        return tup, None

    return None, s


_ASSUMPTION_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(<=|>=|!=|==|=|<|>)\s*(.+?)\s*$")


def _choose_param_subs(
    symbols: List[sp.Symbol],
    assumptions: str | None,
) -> Dict[sp.Symbol, float]:
    """Choose a numeric substitution for parameter symbols.

    Intended to allow ordering/evaluating expressions like roots that depend on
    parameters under simple constraints, e.g. `a > 0`.

    Supported constraints (conjunctions via `and` or comma):
    - `a > 0`, `a >= 0`, `a < 0`, `a <= 0`
    - `a != 0`
    - `a = 2` / `a == 2`

    For anything more complex, this falls back to defaults (1.0).
    """

    subs: Dict[sp.Symbol, float] = {s: 1.0 for s in symbols}
    if not assumptions:
        return subs

    parts = [p.strip() for p in re.split(r"\band\b|,", assumptions) if p.strip()]
    if not parts:
        return subs

    name_to_sym = {s.name: s for s in symbols}

    # Collect constraints per symbol
    constraints: Dict[sp.Symbol, List[Tuple[str, str]]] = {}
    for part in parts:
        m = _ASSUMPTION_RE.match(part)
        if not m:
            continue
        name, op, rhs_txt = m.group(1), m.group(2), m.group(3)
        sym = name_to_sym.get(name)
        if sym is None:
            continue
        constraints.setdefault(sym, []).append((op, rhs_txt))

    # Apply constraints
    for sym, cs in constraints.items():
        # Prefer explicit equality if present
        eq = [c for c in cs if c[0] in {"=", "=="}]
        if eq:
            op, rhs_txt = eq[-1]
            try:
                rhs = float(sp.N(sp.sympify(rhs_txt, locals=name_to_sym)))
                subs[sym] = rhs
                continue
            except Exception:
                pass

        # Otherwise take the last inequality-ish constraint
        op, rhs_txt = cs[-1]
        try:
            rhs_val = float(sp.N(sp.sympify(rhs_txt, locals=name_to_sym)))
        except Exception:
            rhs_val = 0.0

        if op in {">", ">="}:
            subs[sym] = rhs_val + (1.0 if rhs_val != 0.0 else 1.0)
        elif op in {"<", "<="}:
            subs[sym] = rhs_val - (1.0 if rhs_val != 0.0 else 1.0)
        elif op == "!=":
            # Pick something different from rhs_val
            candidate = 1.0
            if abs(candidate - rhs_val) < 1e-9:
                candidate = 2.0
            subs[sym] = candidate

    return subs


def _numeric(expr: Any, subs: Dict[sp.Symbol, float] | None = None) -> float:
    """Best-effort numeric evaluation for sorting and sampling."""
    e = sp.sympify(expr)
    if subs:
        e = e.subs(subs)
    v = sp.N(e)
    # Only accept real-ish numbers
    if getattr(v, "is_real", None) is False:
        raise ValueError("non-real")
    return float(v)


def _eval_sign_at(
    expr: Any,
    x: sp.Symbol,
    x0: float,
    subs: Dict[sp.Symbol, float] | None = None,
    *,
    zero_tol: float = 1e-10,
) -> int | None:
    """Return sign of expr(x0) over reals.

    Returns:
        +1, -1, 0 for real finite values; None when undefined/non-real/non-finite.
    """
    submap = {x: x0}
    if subs:
        submap.update(subs)

    try:
        v = sp.N(sp.sympify(expr).subs(submap))
    except Exception:
        return None

    # Non-real or non-finite => undefined on reals at this point.
    if getattr(v, "is_real", None) is False:
        return None
    if getattr(v, "is_finite", None) is False:
        return None

    try:
        fv = float(v)
    except Exception:
        return None
    if not np.isfinite(fv):
        return None

    if abs(fv) <= zero_tol:
        return 0
    return 1 if fv > 0 else -1


def _domain_breakpoints_real(
    f: sp.Expr, x: sp.Symbol
) -> tuple[list[Any], sp.Set | None]:
    """Best-effort extraction of real-domain boundary points.

    This is used to split the sign chart into intervals where a function like log(x)
    is (not) defined over the reals.
    """
    try:
        from sympy.calculus.util import continuous_domain

        dom = continuous_domain(f, x, sp.S.Reals)
    except Exception:
        return [], None

    breaks: list[Any] = []

    def add_endpoint(e):
        if e in (sp.S.NegativeInfinity, sp.S.Infinity, sp.S.ComplexInfinity):
            return
        try:
            e_s = sp.sympify(e)
        except Exception:
            return
        if e_s.is_real is False:
            return
        if e_s.is_finite is False:
            return
        breaks.append(e_s)

    def walk(s: sp.Set):
        if isinstance(s, sp.Interval):
            add_endpoint(s.start)
            add_endpoint(s.end)
            return
        if isinstance(s, sp.Union):
            for arg in s.args:
                walk(arg)
            return
        # FiniteSet: boundary points may matter for splitting
        if isinstance(s, sp.FiniteSet):
            for pt in s:
                add_endpoint(pt)

    walk(dom)

    # Deduplicate while preserving order (symbolic equality)
    out: list[Any] = []
    for b in breaks:
        if b not in out:
            out.append(b)
    return out, dom


def draw_factors(
    f,
    factors,
    roots,
    root_positions,
    ax,
    color_pos,
    color_neg,
    x,
    dy=-1,
    dx=0.02,
    fontsize=24,
    subs: Dict[sp.Symbol, float] | None = None,
    root_numeric: Dict[Any, float] | None = None,
    singularities_set: set[Any] | None = None,
):
    x_min = -0.05
    x_max = 1.05
    # Draw horizontal sign lines for each factor
    for i, factor in enumerate(factors):
        expression = factor.get("expression")
        exponent = factor.get("exponent")

        # Handle both old format (single "root") and new format (multiple "roots")
        factor_roots = (
            factor.get("roots", [factor.get("root")])
            if factor.get("root") is not None or factor.get("roots")
            else []
        )

        # Use LaTeX rendering for proper mathematical notation.
        # Prefer a precomputed override (keeps `x` first for linear factors).
        expression_latex_override = factor.get("expression_latex")
        if expression_latex_override:
            expression_latex = expression_latex_override
        else:
            try:
                expression_latex = sp.latex(expression)
            except:
                # Fallback to string representation if latex fails
                expression_latex = str(expression)

        if exponent > 1:
            s = f"$({expression_latex})^{{{exponent}}}$"
        else:
            s = f"${expression_latex}$"

        plt.text(
            x=-0.1,
            y=(i + 1) * dy,
            s=s,
            fontsize=fontsize,
            ha="right",
            va="center",
        )

        # If no real roots (constant factor)
        if -np.inf in factor_roots or not factor_roots:
            submap = {x: 0}
            if subs:
                submap.update(subs)
            y_value = sp.sympify(expression).evalf(subs=submap)
            if y_value > 0:
                ax.plot(
                    [x_min, x_max],
                    [(i + 1) * dy, (i + 1) * dy],
                    color=color_pos,
                    linestyle="-",
                    lw=2,
                )
            else:
                ax.plot(
                    [x_min, x_max],
                    [(i + 1) * dy, (i + 1) * dy],
                    color=color_neg,
                    linestyle="--",
                    lw=2,
                )
        else:
            # Sort roots for drawing
            symbolic_roots = [r for r in factor_roots if r != -np.inf]
            if root_numeric is None:
                root_numeric = {r: _numeric(r, subs) for r in symbolic_roots}
            sorted_roots = sorted(
                symbolic_roots, key=lambda r: root_numeric.get(r, _numeric(r, subs))
            )

            # Determine if even exponent (doesn't change sign) or odd (changes sign)
            is_even_exponent = exponent % 2 == 0

            # Create the full expression with exponent for evaluation
            expr = expression
            if exponent > 1:
                full_expr = expr**exponent
            else:
                full_expr = expr

            # Draw segments between roots
            # We need to evaluate signs in each interval
            all_positions = [x_min] + [root_positions[r] for r in sorted_roots] + [x_max]

            for j in range(len(all_positions) - 1):
                left_pos = all_positions[j]
                right_pos = all_positions[j + 1]

                # Add gap around roots (except at boundaries)
                if j > 0:  # Not the leftmost segment
                    left_pos += dx
                if j < len(all_positions) - 2:  # Not the rightmost segment
                    right_pos -= dx

                # Map position back to actual x value for evaluation
                # Position is normalized 0-1, map to actual domain
                if j < len(sorted_roots):
                    if j == 0:
                        # Before first root
                        test_x = root_numeric[sorted_roots[0]] - 1
                    else:
                        # Between roots
                        test_x = (
                            root_numeric[sorted_roots[j - 1]] + root_numeric[sorted_roots[j]]
                        ) / 2
                else:
                    # After last root
                    test_x = root_numeric[sorted_roots[-1]] + 1

                # Evaluate sign at test point
                try:
                    submap = {x: test_x}
                    if subs:
                        submap.update(subs)
                    y_val = sp.sympify(full_expr).evalf(subs=submap)
                    is_positive = y_val > 0
                    color = color_pos if is_positive else color_neg
                    linestyle = "-" if is_positive else "--"
                except:
                    # Fallback
                    color = color_pos
                    linestyle = "-"

                # Draw segment
                ax.plot(
                    [left_pos, right_pos],
                    [(i + 1) * dy, (i + 1) * dy],
                    color=color,
                    linestyle=linestyle,
                    lw=2,
                )

            # Draw markers at roots
            for root in sorted_roots:
                root_pos = root_positions[root]

                # Factor rows represent the factor itself, so at its roots it is 0.
                # Poles (undefined values) are a property of the full function f(x)
                # and should be rendered only on the f(x) row.
                plt.text(
                    x=root_pos,
                    y=(i + 1) * dy,
                    s=f"$0$",
                    fontsize=fontsize,
                    ha="center",
                    va="center",
                )


def draw_function(
    factors,
    roots,
    root_positions,
    ax,
    color_pos,
    color_neg,
    x,
    f,
    fn_name=None,
    include_factors=True,
    dy=-1,
    dx=0.02,
    fontsize=24,
    subs: Dict[sp.Symbol, float] | None = None,
    root_numeric: Dict[Any, float] | None = None,
    singularities_set: set[Any] | None = None,
):

    x_min = -0.05
    x_max = 1.05

    if include_factors:
        y = (len(factors) + 1) * dy
    else:
        y = dy
    plt.text(
        x=-0.1,
        y=y,
        s=f"${fn_name}$" if fn_name else f"$f({str(x)})$",
        fontsize=fontsize,
        ha="right",
        va="center",
    )

    # Case 1: the function has no explicit roots/breakpoints.
    if len(roots) == 0:
        x0 = 0
        sgn = _eval_sign_at(f, x, x0, subs)
        if sgn is None:
            ax.plot(
                [x_min, x_max],
                [y, y],
                color="black",
                linestyle=":",
                lw=2,
                alpha=0.6,
            )
            plt.text(
                x=(x_min + x_max) / 2,
                y=y,
                s=f"$\\times$",
                fontsize=fontsize,
                ha="center",
                va="center",
            )
        elif sgn > 0:
            ax.plot(
                [x_min, x_max],
                [y, y],
                color=color_pos,
                linestyle="-",
                lw=2,
            )
        else:
            ax.plot(
                [x_min, x_max],
                [y, y],
                color=color_neg,
                linestyle="--",
                lw=2,
            )

        return None

    intervals = []
    interval_positions = []

    if root_numeric is None:
        root_numeric = {r: _numeric(r, subs) for r in roots}

    # Intervals before first root
    intervals.append((root_numeric[roots[0]] - 1, root_numeric[roots[0]] - 0.1))
    interval_positions.append((x_min, root_positions[roots[0]] - dx))

    # Intervals between roots
    for i in range(len(roots) - 1):
        intervals.append((root_numeric[roots[i]] + 0.1, root_numeric[roots[i + 1]] - 0.1))
        interval_positions.append(
            (root_positions[roots[i]] + dx, root_positions[roots[i + 1]] - dx)
        )

    # Interval after last root
    intervals.append((root_numeric[roots[-1]] + 0.1, root_numeric[roots[-1]] + 1))
    interval_positions.append((root_positions[roots[-1]] + dx, x_max))

    for i, (x0_interval, pos_interval) in enumerate(zip(intervals, interval_positions)):
        x0 = (x0_interval[0] + x0_interval[1]) / 2
        sgn = _eval_sign_at(f, x, x0, subs)
        if sgn is None:
            ax.plot(
                [pos_interval[0], pos_interval[1]],
                [y, y],
                color="black",
                linestyle=":",
                lw=2,
                alpha=0.6,
            )
            plt.text(
                x=(pos_interval[0] + pos_interval[1]) / 2,
                y=y,
                s=f"$\\times$",
                fontsize=fontsize,
                ha="center",
                va="center",
            )
        elif sgn > 0:
            ax.plot(
                [pos_interval[0], pos_interval[1]],
                [y, y],
                color=color_pos,
                linestyle="-",
                lw=2,
            )
        else:
            ax.plot(
                [pos_interval[0], pos_interval[1]],
                [y, y],
                color=color_neg,
                linestyle="--",
                lw=2,
            )

    # Plot zeros at root positions
    for root in roots:
        root_pos = root_positions[root]
        # Prefer explicit pole tracking.
        if singularities_set is not None:
            is_singularity = root in singularities_set
        else:
            try:
                if subs:
                    f_eval = sp.sympify(f).subs(subs)
                else:
                    f_eval = sp.sympify(f)
                f_at_root = f_eval.evalf(subs={x: root_numeric[root]})
                is_singularity = (not getattr(f_at_root, "is_finite", True)) or (
                    "zoo" in str(f_at_root)
                )
            except Exception:
                is_singularity = False

        if not is_singularity:
            plt.text(
                x=root_pos,
                y=y,
                s=f"$0$",
                fontsize=fontsize,
                ha="center",
                va="center",
            )
        else:
            plt.text(
                x=root_pos + 0.005,
                y=y,
                s=f"$\\times$",
                fontsize=fontsize,
                ha="center",
                va="center",
            )


def draw_vertical_lines(
    roots,
    root_positions,
    factors,
    ax,
    include_factors=True,
    dy=-1,
):
    # Draw vertical lines to separate regions
    offset_dy = 0.2

    if include_factors:
        # Collect y positions of zeros from factors
        y_zeros_dict = {}
        for i, factor in enumerate(factors):
            # Handle both old format ("root") and new format ("roots")
            factor_roots = (
                factor.get("roots", [factor.get("root")])
                if factor.get("root") is not None or factor.get("roots")
                else []
            )

            for root in factor_roots:
                if root != -np.inf:
                    y_zero = (i + 1) * dy
                    if root in y_zeros_dict:
                        y_zeros_dict[root].append(y_zero)
                    else:
                        y_zeros_dict[root] = [y_zero]
        # Add y position of zero from function
        y_function = (len(factors) + 1) * dy
    else:
        y_zeros_dict = {}
        y_function = dy

    y_min = -0.4
    y_max = y_function + 0.5

    for root in roots:
        root_pos = root_positions[root]
        # Collect y positions where zeros are placed at this root
        zero_y_positions = []
        # From factors
        if root in y_zeros_dict:
            zero_y_positions.extend(y_zeros_dict[root])
        # From function
        zero_y_positions.append(y_function)
        # Now adjust zero_y_positions to include offset_dy
        y_positions = [y_min]
        for y_zero in zero_y_positions:
            y_positions.extend([y_zero - offset_dy, y_zero + offset_dy])
        y_positions.append(y_max)
        y_positions = sorted(y_positions)

        # Now plot segments between pairs
        for i in range(1, len(y_positions) - 1):
            y_start = y_positions[i]
            y_end = y_positions[i + 1]
            # Skip the segments around the zeros
            if (i % 2) == 0:
                if y_end - y_start > 0:
                    ax.plot(
                        [root_pos, root_pos],
                        [y_start, y_end],
                        color="black",
                        linestyle="-",
                        lw=1,
                    )


def make_axis(x, fontsize=24, labelpad=-15):
    fig, ax = plt.subplots()

    # Remove y-axis spines
    ax.spines["left"].set_color("none")  # Remove the left y-axis
    ax.spines["right"].set_color("none")  # Remove the right y-axis

    # Move the x-axis to y=0
    ax.spines["bottom"].set_position("zero")  # Position the bottom x-axis at y=0
    ax.spines["top"].set_color("none")  # Remove the top x-axis

    # Move x-axis ticks and labels to the top
    ax.xaxis.set_ticks_position("top")  # Move ticks to the top
    ax.xaxis.set_label_position("top")  # Move labels to the top
    ax.tick_params(
        axis="x",
        which="both",  # Hide bottom ticks and labels
        bottom=False,
        labelbottom=False,
        length=10,
    )

    # Attach arrow to the right end of the x-axis
    ax.plot(1, 0, ">k", transform=ax.get_yaxis_transform(), clip_on=False)

    # Label the x-axis
    ax.set_xlabel(f"${str(x)}$", fontsize=fontsize, loc="right", labelpad=labelpad)

    # Remove tick labels on y-axis
    plt.yticks([])

    # Set x-limits
    ax.set_xlim(-0.05, 1.05)

    return fig, ax


def plot(
    f,
    x=None,
    fn_name=None,
    color=True,
    include_factors=True,
    generic_labels=False,
    small_figsize=False,
    figsize=None,
    domain=None,
    assumptions=None,
    fontsize=24,
    labelpad=-15,
):
    """Draws a sign chart for a function f (polynomial, rational, or transcendental).

    Args:
        f (sp.Expr, str):
            Function expression. May be a sympy.Expr or str. Supports polynomials,
            rational functions, and transcendental functions (sin, cos, exp, log, etc.).
        x (sp.symbols, str, optional):
            Variable in the function
        fn_name (str, optional):
            Name of the function. Defaults `None`.
        color (bool, optional):
            Enables coloring of sign chart. Default: `True`.
        include_factors (bool, optional):
            Includes all linear factors of f(x) for polynomials. For non-polynomial
            functions, this shows the function name only. Default: `True`.
        generic_label (bool, optional):
            Uses generic labels for roots: x_1, x_2, ..., x_N. Default: `False`.
        small_figsize (bool, optional):
            Enables rescaling of the figure for a smaller figure size. Default: `False`.
        domain (tuple, optional):
            Domain (x_min, x_max) for searching zeros numerically in transcendental functions.
            If None, uses a default range or symbolic solving only. Example: (-10, 10)
        fontsize (int, optional):
            Font size for all text in the chart. Default: 24.
        labelpad (float, optional):
            Padding for the x-axis label. Negative values move it closer to the axis. Default: -15.

    Returns:
        fig (plt.figure)
            matplotlib figure.
        ax (plt.Axis)
            matplotlib axis.
    """
    if isinstance(f, str):
        f = sp.sympify(f)

    # Robust variable selection: prefer symbol named 'x' if present.
    if x is None:
        free = list(f.free_symbols)
        sym_x = None
        for s in free:
            if s.name == "x":
                sym_x = s
                break
        if sym_x is None and free:
            sym_x = sorted(free, key=lambda s: s.name)[0]
        if sym_x is None:
            sym_x = sp.Symbol("x")
        x = sp.Symbol(sym_x.name, real=True)
        f = f.subs(sym_x, x)
    else:
        if isinstance(x, str):
            x = sp.Symbol(x, real=True)

    # Parameter symbols are everything except x
    param_symbols = sorted([s for s in f.free_symbols if s != x], key=lambda s: s.name)
    param_subs = _choose_param_subs(
        param_symbols, str(assumptions).strip() if assumptions else None
    )

    if color:
        color_pos = "red"
        color_neg = "blue"
    else:
        color_pos = color_neg = "black"

    # Determine function type and extract zeros/singularities
    is_polynomial = f.is_polynomial()
    is_rational = False
    singularities: List[Any] = []

    if is_polynomial:
        # Use existing polynomial factorization
        factors = get_factors(polynomial=f, x=x)
        factors = sort_factors(factors)
    else:
        # Check if it's a rational function
        try:
            numer, denom = f.as_numer_denom()
            if denom != 1 and denom.is_polynomial() and numer.is_polynomial():
                is_rational = True
                # Handle as rational function. Use a cancelled form so removable
                # discontinuities don't get marked as poles.
                f = sp.cancel(f)
                numer_c, denom_c = f.as_numer_denom()

                p_factors = get_factors(polynomial=numer_c, x=x) if numer_c != 1 else []
                q_factors = get_factors(polynomial=denom_c, x=x) if denom_c != 1 else []

                for fac in p_factors:
                    fac["is_denominator"] = False
                for fac in q_factors:
                    fac["is_denominator"] = True

                singularities = [
                    fac.get("root")
                    for fac in q_factors
                    if fac.get("root") is not None and fac.get("root") != -np.inf
                ]

                factors = p_factors + q_factors
                factors = sort_factors(factors)
            else:
                # General transcendental or composite function
                is_rational = False
                # Use general zero finding
                result = get_zeros_and_singularities(f, x, domain=domain)
                zeros = result["zeros"]
                singularities = result["singularities"]

                # Extract factors from transcendental function
                factors = get_transcendental_factors(f, x, zeros, singularities)
                factors = sort_factors(factors)
                # Now we can show factors for transcendental functions too!
        except:
            # Fallback: general function
            result = get_zeros_and_singularities(f, x, domain=domain)
            zeros = result["zeros"]
            singularities = result["singularities"]

            # Extract factors
            factors = get_transcendental_factors(f, x, zeros, singularities)
            factors = sort_factors(factors)

    # Add real-domain breakpoints for functions like log(x) and sqrt(x)
    domain_breaks, domain_set = _domain_breakpoints_real(sp.sympify(f), x)

    # Create figure
    fig, ax = make_axis(x, fontsize=fontsize, labelpad=labelpad)

    # Extract roots - handle both old format (single "root") and new format (multiple "roots")
    roots = []
    for factor in factors:
        if "roots" in factor and factor["roots"]:
            # New format: multiple roots per factor
            for r in factor["roots"]:
                if r != -np.inf and r not in roots:
                    roots.append(r)
        elif "root" in factor and factor["root"] != -np.inf:
            # Old format: single root per factor
            if factor["root"] not in roots:
                roots.append(factor["root"])

    # Ensure domain boundary points (finite endpoints) are included to split intervals
    for b in domain_breaks:
        if b != -np.inf and b not in roots:
            roots.append(b)

    # Sort roots (support parameter-dependent roots)
    root_numeric: Dict[Any, float] = {}
    for r in roots:
        try:
            root_numeric[r] = _numeric(r, param_subs)
        except Exception:
            # If a root can't be evaluated numerically, keep it but sort to the end
            root_numeric[r] = float("inf")

    roots = sorted(roots, key=lambda r: root_numeric.get(r, float("inf")))

    # Convert singularities (often computed separately) into the canonical root objects
    # we use for positioning/labeling, by matching numerically.
    singularities_set: set[Any] = set()
    if singularities:
        for s in singularities:
            try:
                s_num = _numeric(s, param_subs)
            except Exception:
                continue
            for r in roots:
                if r == s:
                    singularities_set.add(r)
                    continue
                try:
                    if abs(root_numeric.get(r, float("inf")) - s_num) < 1e-6:
                        singularities_set.add(r)
                except Exception:
                    continue

    # Mark out-of-domain boundary points as singularities (shown as \times on the f(x) row)
    if domain_set is not None:
        for r in roots:
            try:
                contains = domain_set.contains(r)
            except Exception:
                continue
            if contains is sp.S.false:
                singularities_set.add(r)

    # Map roots to positions
    num_roots = len(roots)
    x_min = -0.05
    x_max = 1.05
    positions = np.linspace(0, 1, num_roots + 2)[1:-1]  # Exclude 0 and 1
    root_positions = dict(zip(roots, positions))

    # Set tick marks for roots of the polynomial
    plt.xticks(
        ticks=positions,
        labels=[
            f"${sp.latex(root)}$" if not generic_labels else f"$x_{i + 1}$"
            for i, root in enumerate(roots)
        ],
        fontsize=fontsize,
    )

    # Draw factors
    if include_factors:
        draw_factors(
            f,
            factors,
            roots,
            root_positions,
            ax,
            color_pos,
            color_neg,
            x,
            fontsize=fontsize,
            subs=param_subs,
            root_numeric=root_numeric,
            singularities_set=singularities_set,
        )

    # Draw sign lines for function
    draw_function(
        factors,
        roots,
        root_positions,
        ax,
        color_pos,
        color_neg,
        x,
        f,
        fn_name,
        include_factors,
        fontsize=fontsize,
        subs=param_subs,
        root_numeric=root_numeric,
        singularities_set=singularities_set,
    )

    # Remove tick labels on y-axis
    plt.yticks([])

    plt.xlim(x_min, x_max)

    if include_factors:
        if figsize:
            fig.set_size_inches(figsize)
        else:
            fig.set_size_inches(8, 2 + int(0.7 * len(factors)))

    elif small_figsize:
        fig.set_size_inches(4, 1.5)
    else:
        fig.set_size_inches(8, 2)

    draw_vertical_lines(roots, root_positions, factors, ax, include_factors)

    plt.tight_layout()

    return fig, ax


# ------------------------------------
# Utilities
# ------------------------------------


def _hash_key(*parts) -> str:
    """
    Generate a short hash key from multiple parts.

    Used for creating unique filenames based on function content.

    Args:
        *parts: Variable number of parts to hash

    Returns:
        str: 12-character hex hash
    """
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


def _safe_literal(val: str):
    """
    Safely evaluate a string as a Python literal.

    Args:
        val: String to evaluate

    Returns:
        Evaluated value or None if evaluation fails
    """
    import ast

    try:
        return ast.literal_eval(val)
    except Exception:
        return None


def _parse_bool(val, default: bool | None = None) -> bool | None:
    """
    Parse a value as a boolean.

    Args:
        val: Value to parse (bool, str, or None)
        default: Default value if parsing fails

    Returns:
        bool | None: Parsed boolean value or default
    """
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s == "":
        return True
    if s in {"true", "yes", "on", "1"}:
        return True
    if s in {"false", "no", "off", "0"}:
        return False
    return default


def _parse_tuple(val, element_type=float):
    """
    Parse a value as a tuple.

    Args:
        val: Value to parse (string like "(1, 2)" or tuple)
        element_type: Type to convert elements to (default: float)

    Returns:
        tuple or None if parsing fails
    """
    if val is None:
        return None
    if isinstance(val, (list, tuple)):
        try:
            return tuple(element_type(x) for x in val)
        except:
            return None
    # Try to parse as literal
    lit = _safe_literal(str(val))
    if isinstance(lit, (list, tuple)):
        try:
            return tuple(element_type(x) for x in lit)
        except:
            return None
    return None


def _strip_root_svg_size(svg_text: str) -> str:
    """
    Remove width/height attributes from the root <svg> tag.

    This allows CSS to control the SVG size.

    Args:
        svg_text: Raw SVG content

    Returns:
        str: SVG with width/height removed from root tag
    """

    def repl(m):
        tag = m.group(0)
        tag = re.sub(r'\swidth="[^"]+"', "", tag)
        tag = re.sub(r'\sheight="[^"]+"', "", tag)
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def _rewrite_ids(txt: str, prefix: str) -> str:
    """
    Rewrite all id attributes in SVG to avoid conflicts.

    When multiple SVGs are on the same page, id conflicts can cause
    rendering issues. This function prefixes all ids with a unique prefix.

    Args:
        txt: SVG content
        prefix: Prefix to add to all ids

    Returns:
        str: SVG with rewritten ids
    """
    ids = re.findall(r'\bid="([^"]+)"', txt)
    if not ids:
        return txt
    skip_prefixes = (
        "DejaVu",
        "CM",
        "STIX",
        "Nimbus",
        "Bitstream",
        "Arial",
        "Times",
        "Helvetica",
    )
    mapping = {}
    for i in ids:
        if i.startswith(skip_prefixes):
            continue
        mapping[i] = f"{prefix}{i}"
    if not mapping:
        return txt

    def repl_id(m: re.Match) -> str:
        old = m.group(1)
        new = mapping.get(old, old)
        return f'id="{new}"'

    txt = re.sub(r'\bid="([^"]+)"', repl_id, txt)

    def repl_url(m: re.Match) -> str:
        old = m.group(1).strip()
        new = mapping.get(old, old)
        return f"url(#{new})"

    txt = re.sub(r"url\(#\s*([^\)\s]+)\s*\)", repl_url, txt)

    def repl_href(m: re.Match) -> str:
        attr = m.group(1)
        quote = m.group(2)
        old = m.group(3).strip()
        new = mapping.get(old, old)
        return f"{attr}={quote}#{new}{quote}"

    txt = re.sub(r'(xlink:href|href)\s*=\s*(["\'])#\s*([^"\']+)\s*\2', repl_href, txt)
    return txt


# ------------------------------------
# Sphinx Directive
# ------------------------------------


class SignChart2Directive(SphinxDirective):
    """
    Sphinx directive for generating improved sign charts with embedded plotting.

    This directive supports polynomial, rational, and transcendental functions with
    extensive customization options.

    Options:
        function (required): The function expression and optional label
                            Format: "expression, label" or ("expression", "label")
                            Example: "sin(x)*cos(x), f(x)"
        factors (optional): Whether to show factored form (default: true)
        domain (optional): Either
            - an x-domain tuple (xmin, xmax) for numerical zero finding, e.g. "(-10, 10)", or
            - parameter assumptions, e.g. "a > 0" to handle indeterminate constants.
        color (optional): Enable colored sign chart (default: true)
        generic_labels (optional): Use x₁, x₂ labels instead of actual values (default: false)
        small_figsize (optional): Use compact figure size (default: false)
        figsize (optional): Custom figure size as tuple (width, height)
                           Example: "(10, 4)" or (10, 4)
        fontsize (optional): Font size for all text in the chart (default: 24)
                            Example: "20" or 20
        labelpad (optional): Padding for x-axis label. Negative moves it closer (default: -15)
                            Example: "-15" or -15
        width (optional): Width of the chart (e.g., "100%", "500px", "500")
        align (optional): Alignment ("left", "center", "right")
        class (optional): Additional CSS classes
        name (optional): Reference name for the figure
        nocache (optional): Force regeneration of the chart
        debug (optional): Keep original SVG dimensions and ids
        alt (optional): Alt text for accessibility (default: "Fortegnsskjema")

    Example:
        ```{signchart-2}
        ---
        function: sin(x)*cos(x), f(x)
        domain: (-3.14, 3.14)
        factors: true
        width: 100%
        ---
        Sign chart for f(x) = sin(x)·cos(x)
        ```
    """

    has_content = True
    required_arguments = 0
    option_spec = {
        # presentation / misc
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "debug": directives.flag,
        "alt": directives.unchanged,
        # specific options
        "function": directives.unchanged_required,
        "factors": directives.unchanged,
        "domain": directives.unchanged,
        "color": directives.unchanged,
        "generic_labels": directives.unchanged,
        "small_figsize": directives.unchanged,
        "figsize": directives.unchanged,
        "fontsize": directives.unchanged,
        "labelpad": directives.unchanged,
    }

    def _parse_kv_block(self) -> Tuple[Dict[str, Any], int]:
        """
        Parse YAML-style key-value block from directive content.

        Supports two formats:
        1. YAML front-matter style with --- delimiters
        2. Simple key: value pairs at the start

        Returns:
            tuple: (dict of parsed options, index where caption starts)
        """
        lines = list(self.content)
        scalars: Dict[str, Any] = {}
        idx = 0
        if lines and lines[0].strip() == "---":
            idx = 1
            while idx < len(lines) and lines[idx].strip() != "---":
                line = lines[idx].rstrip()
                if not line.strip():
                    idx += 1
                    continue
                m = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
                if m:
                    scalars[m.group(1)] = m.group(2)
                idx += 1
            if idx < len(lines) and lines[idx].strip() == "---":
                idx += 1
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            return scalars, idx

        caption_start = 0
        for i, line in enumerate(lines):
            if not line.strip():
                caption_start = i + 1
                continue
            m = re.match(r"^([A-Za-z_][\w]*)\s*:\s*(.*)$", line)
            if m:
                scalars[m.group(1)] = m.group(2)
                caption_start = i + 1
            else:
                break
        return scalars, caption_start

    def run(self):  # noqa: C901
        """
        Generate the sign chart.

        Returns:
            list: List of docutils nodes (figure containing SVG)
        """
        env = self.state.document.settings.env
        app = env.app

        scalars, caption_idx = self._parse_kv_block()
        merged: Dict[str, Any] = {**scalars, **self.options}

        func_raw = merged.get("function")
        if not func_raw:
            return [
                self.state_machine.reporter.error(
                    "Directive 'signchart-2' requires 'function:' option",
                    line=self.lineno,
                )
            ]

        # Parse function as either (expr, label) literal or "expr, label"
        f_expr = None
        f_name = None
        lit = _safe_literal(str(func_raw))
        if isinstance(lit, (list, tuple)) and len(lit) >= 1:
            f_expr = str(lit[0]).strip()
            if len(lit) > 1:
                f_name = str(lit[1]).strip() or None
        else:
            s = str(func_raw)
            if "," in s:
                expr, label = s.split(",", 1)
                f_expr = expr.strip()
                label = label.strip()
                f_name = label or None
            else:
                f_expr = s.strip()
                f_name = None

        # Parse options
        include_factors = _parse_bool(merged.get("factors"), default=True)
        use_color = _parse_bool(merged.get("color"), default=True)
        generic_labels = _parse_bool(merged.get("generic_labels"), default=False)
        small_figsize = _parse_bool(merged.get("small_figsize"), default=False)
        explicit_name = merged.get("name")
        debug_mode = "debug" in merged

        # Parse domain: either numeric x-domain tuple OR parameter assumptions.
        domain_val = merged.get("domain")
        custom_domain, domain_assumptions = _parse_domain_option(domain_val)

        # Parse figsize
        figsize_val = merged.get("figsize")
        custom_figsize = _parse_tuple(figsize_val, float) if figsize_val else None

        # Parse fontsize
        fontsize_val = merged.get("fontsize")
        custom_fontsize = int(fontsize_val) if fontsize_val else 24

        # Parse labelpad
        labelpad_val = merged.get("labelpad")
        custom_labelpad = float(labelpad_val) if labelpad_val else -15

        # Hash includes all plot parameters
        content_hash = _hash_key(
            f_expr,
            f_name or "",
            int(bool(include_factors)),
            int(bool(use_color)),
            int(bool(generic_labels)),
            int(bool(small_figsize)),
            str(custom_domain) if custom_domain else "",
            str(domain_assumptions) if domain_assumptions else "",
            str(custom_figsize) if custom_figsize else "",
            str(custom_fontsize),
            str(custom_labelpad),
        )
        base_name = explicit_name or f"signchart2_{content_hash}"

        rel_dir = os.path.join("_static", "signchart")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)

        regenerate = ("nocache" in merged) or not os.path.exists(abs_svg)
        if regenerate:
            try:
                # Render using embedded plot function
                plot_kwargs = {
                    "f": f_expr,
                    "fn_name": f_name or None,
                    "include_factors": bool(include_factors),
                    "color": bool(use_color),
                    "generic_labels": bool(generic_labels),
                    "small_figsize": bool(small_figsize),
                    "fontsize": custom_fontsize,
                    "labelpad": custom_labelpad,
                    "assumptions": domain_assumptions,
                }
                if custom_domain is not None:
                    plot_kwargs["domain"] = custom_domain
                if custom_figsize is not None:
                    plot_kwargs["figsize"] = custom_figsize

                fig, ax = plot(**plot_kwargs)
                fig.savefig(abs_svg, format="svg", bbox_inches="tight", transparent=True)
                plt.close(fig)
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"Error generating sign chart: {e}",
                        line=self.lineno,
                    )
                ]

        if not os.path.exists(abs_svg):
            return [
                self.state_machine.reporter.error(
                    "signchart-2: SVG file missing.", line=self.lineno
                )
            ]

        env.note_dependency(abs_svg)
        # copy into build _static
        try:
            out_static = os.path.join(app.outdir, "_static", "signchart")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"signchart-2 inline: could not read SVG: {e}", line=self.lineno
                )
            ]

        if not debug_mode and "viewBox" in raw_svg:
            raw_svg = _strip_root_svg_size(raw_svg)

        if not debug_mode:
            raw_svg = _rewrite_ids(raw_svg, f"sgc2_{content_hash}_{uuid.uuid4().hex[:6]}_")

        alt_default = "Fortegnsskjema"
        alt = merged.get("alt", alt_default)

        width_opt = merged.get("width")
        percent = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        def _augment(m):
            """Add classes, aria-label, and width styling to root SVG tag."""
            tag = m.group(0)
            if "class=" not in tag:
                tag = tag[:-1] + ' class="graph-inline-svg"' + ">"
            else:
                tag = tag.replace('class="', 'class="graph-inline-svg ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt}"' + ">"
            if width_opt:
                if percent:
                    wval = width_opt.strip()
                else:
                    wval = width_opt.strip()
                    if wval.isdigit():
                        wval += "px"
                style_frag = f"width:{wval}; height:auto; display:block; margin:0 auto;"
                if "style=" in tag:
                    tag = re.sub(
                        r'style="([^"]*)"',
                        lambda mm: f'style="{mm.group(1)}; {style_frag}"',
                        tag,
                        count=1,
                    )
                else:
                    tag = tag[:-1] + f' style="{style_frag}"' + ">"
            return tag

        raw_svg = re.sub(r"<svg\b[^>]*>", _augment, raw_svg, count=1)

        figure = nodes.figure()
        figure.setdefault("classes", []).extend(["adaptive-figure", "signchart-figure", "no-click"])
        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(["graph-image", "no-click", "no-scaled-link"])
        figure += raw_node

        extra_classes = merged.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = merged.get("align", "center")

        caption_lines = list(self.content)[caption_idx:]
        while caption_lines and not caption_lines[0].strip():
            caption_lines.pop(0)
        if caption_lines:
            caption = nodes.caption()
            caption_text = "\n".join(caption_lines)
            # Parse as inline text to support math while avoiding extra paragraph nodes
            parsed_nodes, messages = self.state.inline_text(caption_text, self.lineno)
            caption.extend(parsed_nodes)
            figure += caption

        if explicit_name := merged.get("name"):
            self.add_name(figure)
        return [figure]


def setup(app):
    """
    Setup function to register the directive with Sphinx.

    This function is called automatically by Sphinx when the extension is loaded.
    It registers both 'signchart-2' and 'signchart2' directives for compatibility.

    Args:
        app: The Sphinx application instance

    Returns:
        dict: Extension metadata including version and parallel processing flags
    """
    app.add_directive("signchart-2", SignChart2Directive)
    app.add_directive("signchart2", SignChart2Directive)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
