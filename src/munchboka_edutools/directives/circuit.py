"""Circuit directive

Generates simple electric circuit diagrams as inline SVG using `schemdraw`.

Design goals
------------
- Author expresses *physics topology* via `series(...)` / `parallel(...)`.
- Components can be declared separately via repeated `component:` lines.
- Output embeds SVG inline (like `plot`) and rewrites ids to avoid collisions.

Quick start (MyST)
------------------

:::{circuit}
component: V1, battery, 12 V
component: R1, resistor, 1 kΩ
component: L1, lamp
component: D1, led
component: R2, resistor, 330 Ω
component: RV1, var_resistor, 10 kΩ

circuit: series(V1, R1, parallel(L1, series(D1, R2)), RV1)
width: 80%
:::

Syntax
------
Repeated keys:
- `component:` (alias: `comp:`) registers a component.
  Format: `ID, type[, value][, label]` (CSV-like; quotes allowed).

- `circuit:` provides a topology expression:
  - `series(A, B, C, ...)`
  - `parallel(A, B, C, ...)`
  - `A` may be a component ID or another nested group.

Options
-------
- `width`, `align`, `class`, `name`, `alt`, `nocache`, `debug` (like `plot`)
- `symbols`: `iec` (default) or `ieee`
- `unit`: schemdraw unit size (float, default 1.2)
- `layout`: `ladder` (default) or `loop` (rectangular/perimeter layout for typical series circuits)
- `branch`: `auto|up|down|both` (default auto)
- `junctions`: `true|false` (default true)

Notes
-----
- If a component referenced in `circuit:` is not declared, we try to infer its
  type from the ID prefix (e.g. `R1` -> resistor, `D1` -> led).
- Labels default to TeX-ish names: `R1` -> `$R_1$`, `RV12` -> `$RV_{12}$`.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective


# ------------------------------------
# Small shared helpers (mirrors plot.py behaviour)
# ------------------------------------


def _hash_key(*parts: Any) -> str:
    h = hashlib.sha1()
    for p in parts:
        if p is None:
            p = "__NONE__"
        h.update(str(p).encode("utf-8"))
        h.update(b"||")
    return h.hexdigest()[:12]


def _parse_bool(val: Any, default: Optional[bool] = None) -> Optional[bool]:
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


def _strip_root_svg_size(svg_text: str) -> str:
    def repl(m: re.Match) -> str:
        tag = m.group(0)
        tag = re.sub(r'\swidth="[^"]+"', "", tag)
        tag = re.sub(r'\sheight="[^"]+"', "", tag)
        return tag

    return re.sub(r"<svg\b[^>]*>", repl, svg_text, count=1)


def _rewrite_ids(txt: str, prefix: str) -> str:
    ids = re.findall(r'\bid="([^"]+)"', txt)
    if not ids:
        return txt

    mapping: Dict[str, str] = {}
    for i in ids:
        mapping[i] = f"{prefix}{i}"

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

    txt = re.sub(r'(xlink:href|href)\s*=\s*(["\"])#\s*([^"\"]+)\s*\2', repl_href, txt)
    return txt


# ------------------------------------
# Data model
# ------------------------------------


@dataclass(frozen=True)
class Component:
    id: str
    type: str
    value: str = ""
    label: str = ""


@dataclass(frozen=True)
class Ref:
    id: str


@dataclass(frozen=True)
class Series:
    items: Tuple["Topo", ...]


@dataclass(frozen=True)
class Parallel:
    branches: Tuple["Topo", ...]


Topo = Union[Ref, Series, Parallel]


# ------------------------------------
# Parsing
# ------------------------------------


_ID_TEX_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _auto_tex_label(component_id: str) -> str:
    """Convert e.g. R1 -> $R_1$, RV12 -> $RV_{12}$."""
    cid = (component_id or "").strip()
    m = _ID_TEX_RE.match(cid)
    if not m:
        # Fallback: if it's only letters, render as $ID$ else return literal.
        if re.fullmatch(r"[A-Za-z]+", cid):
            return f"${cid}$"
        return cid
    prefix, digits = m.group(1), m.group(2)
    if len(digits) == 1:
        return f"${prefix}_{digits}$"
    return f"${prefix}_{{{digits}}}$"


def _infer_component_type(component_id: str) -> str:
    cid = (component_id or "").strip()
    up = cid.upper()
    if up.startswith("RV"):
        return "var_resistor"
    if up.startswith("R"):
        return "resistor"
    if up.startswith("LED"):
        return "led"
    if up.startswith("D"):
        return "led"
    if up.startswith("L"):
        return "lamp"
    if up.startswith("V"):
        return "battery"
    return "wire"


def _parse_csv_fields(s: str) -> List[str]:
    try:
        row = next(csv.reader([s], skipinitialspace=True))
    except Exception:
        row = [p.strip() for p in s.split(",")]
    return [str(x).strip() for x in row]


def _parse_component_line(raw: str) -> Component:
    parts = _parse_csv_fields(raw)
    parts = [p for p in parts if p is not None]
    if not parts or not parts[0].strip():
        raise ValueError("component: missing id")

    cid = parts[0].strip()
    ctype = (parts[1].strip() if len(parts) >= 2 and parts[1].strip() else "").lower()
    if not ctype:
        ctype = _infer_component_type(cid)
    value = parts[2].strip() if len(parts) >= 3 else ""
    label = parts[3].strip() if len(parts) >= 4 else ""
    if not label:
        label = _auto_tex_label(cid)
    return Component(id=cid, type=ctype, value=value, label=label)


class _TopoParser:
    def __init__(self, text: str):
        self.text = text
        self.i = 0

    def _peek(self) -> str:
        return self.text[self.i : self.i + 1]

    def _skip_ws(self) -> None:
        while self.i < len(self.text) and self.text[self.i].isspace():
            self.i += 1

    def _consume(self, ch: str) -> None:
        self._skip_ws()
        if not self.text.startswith(ch, self.i):
            raise ValueError(f"Expected '{ch}' at pos {self.i}")
        self.i += len(ch)

    def _ident(self) -> str:
        self._skip_ws()
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", self.text[self.i :])
        if not m:
            raise ValueError(f"Expected identifier at pos {self.i}")
        ident = m.group(0)
        self.i += len(ident)
        return ident

    def _maybe_consume(self, ch: str) -> bool:
        self._skip_ws()
        if self.text.startswith(ch, self.i):
            self.i += len(ch)
            return True
        return False

    def parse(self) -> Topo:
        node = self._expr()
        self._skip_ws()
        if self.i != len(self.text):
            raise ValueError(f"Unexpected trailing input at pos {self.i}")
        return node

    def _expr(self) -> Topo:
        name = self._ident()
        self._skip_ws()
        if self._maybe_consume("("):
            args: List[Topo] = []
            self._skip_ws()
            if not self._maybe_consume(")"):
                while True:
                    args.append(self._expr())
                    self._skip_ws()
                    if self._maybe_consume(","):
                        continue
                    self._consume(")")
                    break
            lname = name.lower()
            if lname == "series":
                return Series(tuple(args))
            if lname == "parallel":
                return Parallel(tuple(args))
            raise ValueError(f"Unknown group function '{name}' (expected series/parallel)")
        return Ref(name)


def _parse_topology(expr: str) -> Topo:
    return _TopoParser(expr.strip()).parse()


# ------------------------------------
# Rendering (simple ladder layout)
# ------------------------------------


def _slot_count(node: Topo) -> int:
    if isinstance(node, Ref):
        return 1
    if isinstance(node, Series):
        return sum(_slot_count(x) for x in node.items)
    if isinstance(node, Parallel):
        return max((_slot_count(b) for b in node.branches), default=1)
    return 1


def _resolve_symbol_classes(symbols: str):
    import schemdraw.elements as elm

    sym = (symbols or "iec").strip().lower()

    def pick(iec_cls, ieee_cls):
        return iec_cls if sym == "iec" else ieee_cls

    # Some elements don't have separate IEC/IEEE variants in schemdraw.
    return {
        "battery": elm.BatteryCell if hasattr(elm, "BatteryCell") else elm.Battery,
        "resistor": pick(
            getattr(elm, "ResistorIEC", elm.Resistor), getattr(elm, "ResistorIEEE", elm.Resistor)
        ),
        "var_resistor": pick(
            getattr(elm, "ResistorVarIEC", getattr(elm, "ResistorVar", elm.Resistor)),
            getattr(elm, "ResistorVarIEEE", getattr(elm, "ResistorVar", elm.Resistor)),
        ),
        # Lamp2 is the circle-with-cross symbol; Lamp is filament-style.
        "lamp": getattr(elm, "Lamp2", getattr(elm, "Lamp", None)),
        "led": getattr(elm, "LED", None),
        "diode": getattr(elm, "Diode", None),
        "wire": getattr(elm, "Line", None),
        "dot": getattr(elm, "Dot", None),
    }


def _dir_apply(elem, flow: str):
    f = (flow or "right").strip().lower()
    if f == "right":
        return elem.right()
    if f == "left":
        return elem.left()
    if f == "up":
        return elem.up()
    if f == "down":
        return elem.down()
    return elem.right()


def _draw_component(d, comp: Component, clsmap: Dict[str, Any], flow: str, slot_len: float):
    ctype = (comp.type or "wire").strip().lower()
    if ctype in {"battery", "source", "dc", "ac", "outlet"}:
        ctype = "battery"
    if ctype in {"r", "res"}:
        ctype = "resistor"
    if ctype in {"rv", "pot", "potmeter", "variable_resistor", "variabel_resistor"}:
        ctype = "var_resistor"

    Elem = clsmap.get(ctype)
    if Elem is None:
        Elem = clsmap.get("wire")

    e = Elem()
    try:
        e = e.length(slot_len)
    except Exception:
        pass
    e = _dir_apply(e, flow)

    # Flip voltage source polarity without changing path direction.
    # (schemdraw Battery/BatteryCell supports reverse())
    if ctype == "battery":
        try:
            e = e.reverse()
        except Exception:
            pass

    # Label/value (best-effort).
    if comp.label:
        try:
            e = e.label(comp.label, loc="top")
        except Exception:
            pass
    if comp.value:
        try:
            e = e.label(comp.value, loc="bot")
        except Exception:
            pass

    d += e


def _draw_wire(d, at: Tuple[float, float], flow: str, length: float, clsmap: Dict[str, Any]):
    Line = clsmap.get("wire")
    if Line is None:
        return
    e = Line().at(at)
    e = _dir_apply(e, flow)
    try:
        e = e.length(length)
    except Exception:
        pass
    d += e


def _draw_dot(d, at: Tuple[float, float], clsmap: Dict[str, Any]):
    Dot = clsmap.get("dot")
    if Dot is None:
        return
    try:
        d += Dot().at(at)
    except Exception:
        pass


def _draw_node(
    d,
    node: Topo,
    comps: Dict[str, Component],
    clsmap: Dict[str, Any],
    flow: str,
    slot_len: float,
    branch_mode: str,
    junctions: bool,
) -> int:
    """Draw node at current drawing cursor. Returns slots consumed along main flow."""
    if isinstance(node, Ref):
        comp = comps.get(node.id)
        if comp is None:
            comp = Component(
                id=node.id, type=_infer_component_type(node.id), label=_auto_tex_label(node.id)
            )
        _draw_component(d, comp, clsmap, flow, slot_len)
        return 1

    if isinstance(node, Series):
        n = 0
        for it in node.items:
            n += _draw_node(d, it, comps, clsmap, flow, slot_len, branch_mode, junctions)
        return n

    if isinstance(node, Parallel):
        branches = list(node.branches)
        if not branches:
            return 0

        left = tuple(d.here)
        if junctions:
            _draw_dot(d, left, clsmap)

        main_flow = (flow or "right").strip().lower()
        is_horizontal = main_flow in {"right", "left"}

        width_slots = max(_slot_count(b) for b in branches)
        width_len = float(width_slots) * float(slot_len)

        # Compute far junction coordinate WITHOUT drawing a bypass wire.
        if is_horizontal:
            dx = width_len if main_flow == "right" else -width_len
            far = (left[0] + dx, left[1])
        else:
            dy = width_len if main_flow == "down" else -width_len
            far = (left[0], left[1] + dy)

        d.here = far
        if junctions:
            _draw_dot(d, far, clsmap)

        # Determine branch offsets
        n_br = len(branches)
        mode = (branch_mode or "auto").strip().lower()
        if mode not in {"auto", "both", "up", "down"}:
            mode = "auto"
        if mode == "auto":
            mode = "both"

        # Separation between branches (perpendicular to main flow).
        step = float(slot_len) * 1.15
        offsets: List[float] = []
        if mode == "up":
            offsets = [step * (i + 1) for i in range(n_br)]
        elif mode == "down":
            offsets = [-step * (i + 1) for i in range(n_br)]
        else:
            center = (n_br - 1) / 2.0
            offsets = [-(i - center) * step for i in range(n_br)]

        # For vertical main flow, interpret up/down as left/right offsets.
        if not is_horizontal:
            # Keep offsets sign meaning consistent visually: positive -> left.
            offsets = offsets

        # Draw each branch
        for br, off in zip(branches, offsets):
            d.push()
            d.here = left

            # Move perpendicular from start junction to branch lane.
            if abs(off) > 1e-9:
                seg = clsmap.get("wire")().at(left)
                if is_horizontal:
                    seg = seg.up() if off > 0 else seg.down()
                else:
                    # Vertical main flow: offset left/right
                    seg = seg.left() if off > 0 else seg.right()
                seg = seg.length(abs(off))
                d += seg

            # Draw branch content along main flow.
            expected = max(0, _slot_count(br))
            extra = max(0, width_slots - expected)
            lead = extra // 2

            if lead:
                _draw_wire(d, tuple(d.here), main_flow, lead * slot_len, clsmap)

            slots_used = _draw_node(
                d, br, comps, clsmap, main_flow, slot_len, branch_mode, junctions
            )
            remaining = max(0, width_slots - lead - slots_used)
            if remaining:
                _draw_wire(d, tuple(d.here), main_flow, remaining * slot_len, clsmap)

            # Move perpendicular back to far junction lane.
            end_point = tuple(d.here)
            if abs(off) > 1e-9:
                seg2 = clsmap.get("wire")().at(end_point)
                if is_horizontal:
                    seg2 = seg2.down() if off > 0 else seg2.up()
                else:
                    seg2 = seg2.right() if off > 0 else seg2.left()
                seg2 = seg2.length(abs(off))
                d += seg2

            d.pop()

        # Continue main drawing cursor at the far junction.
        d.here = far
        return width_slots

    return 0


def _normalize_loop_topology(topo: Topo) -> Topo:
    """If user writes series(V1, ..., V1) in loop layout, drop the last V1.

    This matches the author intent: V1 at the end is a "close the loop" marker,
    not a second voltage source.
    """

    if isinstance(topo, Series) and len(topo.items) >= 2:
        first = topo.items[0]
        last = topo.items[-1]
        if isinstance(first, Ref) and isinstance(last, Ref) and first.id == last.id:
            return Series(topo.items[:-1])
    return topo


def _contains_parallel(node: Topo) -> bool:
    if isinstance(node, Parallel):
        return True
    if isinstance(node, Series):
        return any(_contains_parallel(x) for x in node.items)
    return False


def _max_parallel_branches(node: Topo) -> int:
    """Return the maximum number of branches in any Parallel node within topology."""
    if isinstance(node, Parallel):
        return len(node.branches)
    if isinstance(node, Series):
        return max((_max_parallel_branches(x) for x in node.items), default=0)
    return 0


def _draw_loop_return(
    d,
    start: Tuple[float, float],
    end: Tuple[float, float],
    flow: str,
    slot_len: float,
    clsmap: Dict[str, Any],
    branch_mode: str,
    junctions: bool,
    max_parallel_branches: int = 0,
) -> None:
    """Draw a simple rectangular return wire from end back to start."""

    Line = clsmap.get("wire")
    if Line is None:
        return

    mode = (branch_mode or "auto").strip().lower()
    # If branches are pushed down, route loop above; if branches up, route below.
    route = "down"
    if mode == "down":
        route = "up"
    elif mode == "up":
        route = "down"

    # Keep loop closure compact, but increase offset when parallel groups exist
    # so the return wire doesn't cut through branch space.
    base = float(slot_len) * 1.8
    extra = float(slot_len) * 1.2 * max(0, int(max_parallel_branches) - 1)
    loop_offset = base + extra
    if route == "up":
        loop_offset = -loop_offset

    # We draw using absolute coordinates so it works for both right/left flow.
    sx, sy = start
    ex, ey = end

    d.push()
    try:
        # Vertical away from end
        d.here = (ex, ey)
        v1 = Line().at((ex, ey))
        v1 = v1.down() if loop_offset > 0 else v1.up()
        v1 = v1.length(abs(loop_offset))
        d += v1
        c1 = tuple(d.here)

        # Horizontal back toward start x
        dx = sx - c1[0]
        h = Line().at(c1)
        h = h.right() if dx > 0 else h.left()
        h = h.length(abs(dx))
        d += h
        c2 = tuple(d.here)

        # Vertical back to start y
        dy = sy - c2[1]
        v2 = Line().at(c2)
        v2 = v2.up() if dy > 0 else v2.down()
        v2 = v2.length(abs(dy))
        d += v2

        if junctions:
            _draw_dot(d, (ex, ey), clsmap)
            _draw_dot(d, (sx, sy), clsmap)
    finally:
        d.pop()


def _choose_wrap_width(total_slots: int) -> int:
    """Choose a series wrap width (in slots) that yields a compact loop.

    We prefer widths near sqrt(total_slots) and slightly prefer an even number
    of rows (snake ends near start), which usually reduces the return segment.
    """

    if total_slots <= 0:
        return 1

    # For short circuits, wrapping usually wastes space.
    if total_slots <= 6:
        return total_slots

    target = max(2, int(math.ceil(math.sqrt(total_slots))))
    candidates = sorted(
        {
            max(2, target - 3),
            max(2, target - 2),
            max(2, target - 1),
            max(2, target),
            max(2, target + 1),
            max(2, target + 2),
            max(2, target + 3),
            total_slots,
        }
    )

    best_w = candidates[0]
    best_cost = float("inf")
    row_penalty = 10.0
    for w in candidates:
        rows = int(math.ceil(total_slots / w))
        # Estimated cost: strongly penalize extra rows to avoid huge vertical whitespace.
        cost = w + rows * row_penalty
        # Slight preference for even rows (snake ends closer to start).
        if rows % 2 == 1 and rows > 1:
            cost += w * 0.35
        if cost < best_cost:
            best_cost = cost
            best_w = w

    return max(2, min(best_w, total_slots))


def _draw_series_wrapped(
    d,
    items: Sequence[Topo],
    comps: Dict[str, Component],
    clsmap: Dict[str, Any],
    flow: str,
    slot_len: float,
    max_run_slots: int,
    row_step: float,
    branch_mode: str,
    junctions: bool,
) -> int:
    """Draw a series list, wrapping into multiple rows to reduce width.

    Returns the total slots consumed.
    """

    run_slots = 0
    total = 0
    cur_flow = flow

    for it in items:
        need = _slot_count(it)
        if run_slots > 0 and (run_slots + need) > max_run_slots:
            # Move to next row and reverse direction.
            _draw_wire(d, tuple(d.here), "down", row_step, clsmap)
            cur_flow = "left" if cur_flow == "right" else "right"
            run_slots = 0
            if junctions:
                _draw_dot(d, tuple(d.here), clsmap)

        used = _draw_node(
            d,
            it,
            comps,
            clsmap,
            flow=cur_flow,
            slot_len=slot_len,
            branch_mode=branch_mode,
            junctions=junctions,
        )
        run_slots += used
        total += used

    return total


def _is_simple_series_of_refs(node: Topo) -> bool:
    return isinstance(node, Series) and all(isinstance(x, Ref) for x in node.items)


def _draw_loop_perimeter_series(
    d,
    items: Sequence[Topo],
    comps: Dict[str, Component],
    clsmap: Dict[str, Any],
    flow: str,
    slot_len: float,
    branch_mode: str,
    junctions: bool,
) -> None:
    """Draw a compact rectangular loop with components distributed around the perimeter.
    """

    if len(items) < 3:
        _draw_node(
            d,
            Series(tuple(items)),
            comps,
            clsmap,
            flow=flow,
            slot_len=slot_len,
            branch_mode=branch_mode,
            junctions=junctions,
        )
        return

    start = tuple(d.here)
    if junctions:
        _draw_dot(d, start, clsmap)

    # Distribute items by slot-count budget across 4 sides.
    total_slots = sum(_slot_count(it) for it in items)
    # Aim for a near-square loop: top and bottom share half the slots,
    # vertical sides share the other half.
    horiz_slots = int(math.ceil(total_slots / 2))
    vert_slots = max(1, total_slots - horiz_slots)
    top_slots = int(math.ceil(horiz_slots / 2))
    right_slots = int(math.ceil(vert_slots / 2))
    bottom_slots = max(1, horiz_slots - top_slots)
    left_slots = max(1, vert_slots - right_slots)

    side1: List[Topo] = []
    side2: List[Topo] = []
    side3: List[Topo] = []
    side4: List[Topo] = []

    side_budgets = [top_slots, right_slots, bottom_slots, left_slots]
    sides = [side1, side2, side3, side4]
    side_idx = 0
    used_in_side = 0
    for it in items:
        need = _slot_count(it)
        if side_idx < 3 and used_in_side > 0 and (used_in_side + need) > side_budgets[side_idx]:
            side_idx += 1
            used_in_side = 0
        sides[side_idx].append(it)
        used_in_side += need

    dir1 = flow  # right|left
    dir2 = "down"
    dir3 = "left" if dir1 == "right" else "right"
    dir4 = "up"

    min_side = slot_len * 0.9

    def draw_side(side_items: Sequence[Topo], direction: str) -> int:
        used = 0
        for it in side_items:
            used += _draw_node(
                d,
                it,
                comps,
                clsmap,
                flow=direction,
                slot_len=slot_len,
                branch_mode=branch_mode,
                junctions=junctions,
            )
        return used

    def pad_to(target_slots: int, used_slots: int, direction: str) -> None:
        remaining = max(0, int(target_slots) - int(used_slots))
        if remaining:
            _draw_wire(d, tuple(d.here), direction, remaining * slot_len, clsmap)

    # Target side lengths (in slots). Use the budget, but never shorter than what
    # actually got placed on that side (items may overflow a budget boundary).
    side1_target = max(top_slots, sum(_slot_count(it) for it in side1) or 1)
    side2_target = max(right_slots, sum(_slot_count(it) for it in side2) or 1)
    side3_target = max(bottom_slots, sum(_slot_count(it) for it in side3) or 1)
    side4_target = max(left_slots, sum(_slot_count(it) for it in side4) or 1)

    # Side 1 (top)
    used1 = draw_side(side1, dir1)
    pad_to(side1_target, used1, dir1)
    if junctions:
        _draw_dot(d, tuple(d.here), clsmap)

    # Side 2 (right vertical)
    if side2:
        used2 = draw_side(side2, dir2)
        pad_to(side2_target, used2, dir2)
    else:
        _draw_wire(d, tuple(d.here), dir2, max(min_side, side2_target * slot_len), clsmap)
    if junctions:
        _draw_dot(d, tuple(d.here), clsmap)

    # Side 3 (bottom)
    if side3:
        used3 = draw_side(side3, dir3)
        pad_to(side3_target, used3, dir3)
    else:
        _draw_wire(d, tuple(d.here), dir3, max(min_side, side3_target * slot_len), clsmap)
    if junctions:
        _draw_dot(d, tuple(d.here), clsmap)

    # Side 4 (left vertical up)
    if side4:
        used4 = draw_side(side4, dir4)
        pad_to(side4_target, used4, dir4)
    else:
        _draw_wire(d, tuple(d.here), dir4, max(min_side, side4_target * slot_len), clsmap)
    bottom_end = tuple(d.here)

    # Close loop back to start with wires.
    # First, ensure we're at start.x
    dx = start[0] - bottom_end[0]
    if abs(dx) > 1e-6:
        horiz = clsmap.get("wire")().at(bottom_end)
        horiz = horiz.right() if dx > 0 else horiz.left()
        horiz = horiz.length(abs(dx))
        d += horiz

    at_left_bottom = tuple(d.here)
    dy = start[1] - at_left_bottom[1]
    if abs(dy) > 1e-6:
        vert = clsmap.get("wire")().at(at_left_bottom)
        vert = vert.up() if dy > 0 else vert.down()
        vert = vert.length(abs(dy))
        d += vert

    if junctions:
        _draw_dot(d, start, clsmap)


# ------------------------------------
# Directive
# ------------------------------------


class CircuitDirective(SphinxDirective):
    has_content = True
    required_arguments = 0
    option_spec = {
        "width": directives.length_or_percentage_or_unitless,
        "align": lambda a: directives.choice(a, ["left", "center", "right"]),
        "class": directives.class_option,
        "name": directives.unchanged,
        "nocache": directives.flag,
        "debug": directives.flag,
        "alt": directives.unchanged,
        # circuit-specific
        "symbols": directives.unchanged,
        "unit": directives.unchanged,
        "flow": directives.unchanged,
        "layout": directives.unchanged,
        "branch": directives.unchanged,
        "junctions": directives.unchanged,
        "transparent": directives.unchanged,
        "fontsize": directives.unchanged,
    }

    _repeated_keys = {"component", "comp"}

    def _strip_inline_comment(self, val: str) -> str:
        # Treat '#' as comment starter for simple config-like values.
        # This matches how our docs are written (e.g. `flow: right  # comment`).
        if "#" not in val:
            return val.strip()
        return val.split("#", 1)[0].strip()

    def _parse_kv_block(self) -> Tuple[Dict[str, str], Dict[str, List[str]], str]:
        scalars: Dict[str, str] = {}
        lists: Dict[str, List[str]] = {}
        caption_lines: List[str] = []

        for line in self.content:
            if not line.strip():
                continue
            if ":" not in line:
                caption_lines.append(line)
                continue

            key, val = line.split(":", 1)
            key = key.strip()
            if not key:
                continue
            val = self._strip_inline_comment(val)
            lkey = key.lower()

            if lkey in self._repeated_keys:
                if val:
                    lists.setdefault("component", []).append(val)
                continue

            if lkey == "caption":
                if val:
                    caption_lines.append(val)
                continue

            scalars[lkey] = val

        return scalars, lists, "\n".join(caption_lines).strip()

    def run(self):
        env = self.state.document.settings.env
        app = env.app

        try:
            import schemdraw
        except Exception as e:
            err = nodes.error()
            err += nodes.paragraph(text=f"circuit: kunne ikke importere schemdraw: {e}")
            return [err]

        scalars, lists, caption_text = self._parse_kv_block()
        merged: Dict[str, Any] = {**scalars, **self.options}

        expr = merged.get("circuit")
        if not expr:
            return [
                self.state_machine.reporter.error(
                    "circuit: mangler 'circuit:' uttrykk.", line=self.lineno
                )
            ]

        # Parse components
        comps: Dict[str, Component] = {}
        for raw in lists.get("component", []):
            try:
                c = _parse_component_line(str(raw))
                comps[c.id] = c
            except Exception:
                continue

        # Parse topology
        try:
            topo = _parse_topology(str(expr))
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"circuit: ugyldig circuit-uttrykk: {e}", line=self.lineno
                )
            ]

        # Options
        symbols = str(merged.get("symbols", "iec"))
        flow = str(merged.get("flow", "right")).strip().lower()
        if flow not in {"right", "left"}:
            return [
                self.state_machine.reporter.error(
                    "circuit: foreløpig støttes bare flow: right|left.",
                    line=self.lineno,
                )
            ]

        layout = str(merged.get("layout", "ladder")).strip().lower()
        branch_mode = str(merged.get("branch", "auto")).strip().lower()
        junctions = _parse_bool(merged.get("junctions"), default=True)
        try:
            unit = float(merged.get("unit", 1.2))
        except Exception:
            unit = 1.2

        try:
            fontsize_raw = merged.get("fontsize")
            fontsize = (
                float(fontsize_raw)
                if fontsize_raw is not None and str(fontsize_raw).strip() != ""
                else None
            )
        except Exception:
            fontsize = None

        transparent = _parse_bool(merged.get("transparent"), default=True)

        # Hash/cache
        explicit_name = merged.get("name")
        content_hash = _hash_key(
            expr,
            symbols,
            flow,
            layout,
            branch_mode,
            unit,
            fontsize,
            transparent,
            "|".join([f"{k}:{v.type}:{v.value}:{v.label}" for k, v in sorted(comps.items())]),
        )
        base_name = explicit_name or f"circuit_{content_hash}"

        rel_dir = os.path.join("_static", "circuit")
        abs_dir = os.path.join(app.srcdir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)
        svg_name = f"{base_name}.svg"
        abs_svg = os.path.join(abs_dir, svg_name)

        debug_mode = "debug" in merged
        regenerate = ("nocache" in merged) or not os.path.exists(abs_svg)

        if regenerate:
            try:
                clsmap = _resolve_symbol_classes(symbols)
                d = schemdraw.Drawing(show=False)
                d.config(unit=unit, fontsize=fontsize)

                # fixed slot length for stable layout
                slot_len = 3.0

                if layout not in {"ladder", "loop"}:
                    layout = "ladder"

                topo_to_draw = topo
                if layout == "loop":
                    topo_to_draw = _normalize_loop_topology(topo)

                start = tuple(d.here)

                did_close_loop = False

                if layout == "loop" and isinstance(topo_to_draw, Series):
                    total_slots = _slot_count(topo_to_draw)
                    has_parallel = _contains_parallel(topo_to_draw)
                    if total_slots <= 32 and not has_parallel:
                        _draw_loop_perimeter_series(
                            d,
                            topo_to_draw.items,
                            comps,
                            clsmap,
                            flow=flow,
                            slot_len=slot_len,
                            branch_mode=branch_mode,
                            junctions=bool(junctions),
                        )
                        did_close_loop = True
                    else:
                        wrap_w = _choose_wrap_width(total_slots)
                        row_step = slot_len * 3.2
                        _draw_series_wrapped(
                            d,
                            topo_to_draw.items,
                            comps,
                            clsmap,
                            flow=flow,
                            slot_len=slot_len,
                            max_run_slots=wrap_w,
                            row_step=row_step,
                            branch_mode=branch_mode,
                            junctions=bool(junctions),
                        )
                else:
                    _draw_node(
                        d,
                        topo_to_draw,
                        comps,
                        clsmap,
                        flow=flow,
                        slot_len=slot_len,
                        branch_mode=branch_mode,
                        junctions=bool(junctions),
                    )

                if layout == "loop" and not did_close_loop:
                    end = tuple(d.here)
                    max_br = _max_parallel_branches(topo_to_draw) if layout == "loop" else 0
                    _draw_loop_return(
                        d,
                        start=start,
                        end=end,
                        flow=flow,
                        slot_len=slot_len,
                        clsmap=clsmap,
                        branch_mode=branch_mode,
                        junctions=bool(junctions),
                        max_parallel_branches=max_br,
                    )

                # Use schemdraw's save() so matplotlib export can be transparent.
                d.save(abs_svg, transparent=bool(transparent))
            except Exception as e:
                return [
                    self.state_machine.reporter.error(
                        f"circuit: feil under generering: {e}", line=self.lineno
                    )
                ]

        if not os.path.exists(abs_svg):
            return [self.state_machine.reporter.error("circuit: SVG mangler.", line=self.lineno)]

        env.note_dependency(abs_svg)

        # Copy to build _static
        try:
            out_static = os.path.join(app.outdir, "_static", "circuit")
            os.makedirs(out_static, exist_ok=True)
            shutil.copy2(abs_svg, os.path.join(out_static, svg_name))
        except Exception:
            pass

        try:
            raw_svg = open(abs_svg, "r", encoding="utf-8").read()
        except Exception as e:
            return [
                self.state_machine.reporter.error(
                    f"circuit inline: kunne ikke lese SVG: {e}", line=self.lineno
                )
            ]

        if not debug_mode and "viewBox" in raw_svg:
            raw_svg = _strip_root_svg_size(raw_svg)

        if not debug_mode:
            raw_svg = _rewrite_ids(raw_svg, f"circuit_{content_hash}_{uuid.uuid4().hex[:6]}_")

        alt_default = "Elektrisk krets"
        alt = merged.get("alt", alt_default)

        width_opt = merged.get("width")
        percent = isinstance(width_opt, str) and width_opt.strip().endswith("%")

        def _augment(m: re.Match) -> str:
            tag = m.group(0)
            cls_add = "graph-inline-svg circuit-inline-svg"
            if "class=" not in tag:
                tag = tag[:-1] + f' class="{cls_add}"' + ">"
            else:
                tag = tag.replace('class="', f'class="{cls_add} ')
            if alt and "aria-label=" not in tag:
                tag = tag[:-1] + f' role="img" aria-label="{alt}"' + ">"
            if width_opt:
                wval = width_opt.strip() if isinstance(width_opt, str) else str(width_opt)
                if not percent and wval.isdigit():
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
        figure.setdefault("classes", []).extend(["adaptive-figure", "circuit-figure", "no-click"])
        raw_node = nodes.raw("", raw_svg, format="html")
        raw_node.setdefault("classes", []).extend(["graph-image", "no-click", "no-scaled-link"])
        figure += raw_node

        extra_classes = merged.get("class")
        if extra_classes:
            figure["classes"].extend(extra_classes)
        figure["align"] = merged.get("align", "center")

        if caption_text:
            caption = nodes.caption()
            parsed_nodes, _messages = self.state.inline_text(caption_text, self.lineno)
            caption.extend(parsed_nodes)
            figure += caption

        if explicit_name:
            self.add_name(figure)

        return [figure]


def setup(app):  # pragma: no cover
    app.add_directive("circuit", CircuitDirective)
    try:
        app.add_css_file("munchboka/css/general_style.css")
    except Exception:
        pass
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
