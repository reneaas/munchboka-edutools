"""Generate bounded renderer fixtures from the production scene parser.

Run from the repository root: PYTHONPATH=src python experiments/renderer3d/build_cases.py
The mesh fixture is experimental data, not new directive syntax.
"""
import json
import math
from pathlib import Path

from munchboka_edutools.directives._scene3d import build_scene


def case(identifier, title, question, lines):
    scene, _, _ = build_scene([
        "xrange: (-2.5,2.5)", "yrange: (-2.5,2.5)", "zrange: (-2.5,2.5)",
        "elev: 25", "azim: -55", *lines,
    ])
    return dict(id=identifier, title=title, question=question, scene=scene)


cases = [
    case("sphere", "Line through an opaque sphere",
         "Rotate through a full turn. Does the line disappear only where the sphere covers it? Three.js also draws hidden portions as faint dashes.", [
        "sphere: center=(0,0,0), radius=1, color=teal, alpha=1",
        "line: point=(0,0,0), direction=(1,0.3,0.2), color=red, lw=3",
        "text: at=(1.3,0.5,0.5), value=\"$\\ell$\"",
    ]),
    case("planes", "Intersecting translucent planes",
         "The order of the orange and blue surfaces should change across their intersection. Standard transparency sorting is intentionally left exposed in both renderers.", [
        "plane: equation=z=0, xrange=(-1.8,1.8), yrange=(-1.8,1.8), color=orange, alpha=0.45",
        "plane: equation=x=0, yrange=(-1.8,1.8), zrange=(-1.8,1.8), color=blue, alpha=0.45",
        "line-segment: (0,-1.8,0), (0,1.8,0), black, lw=3",
    ]),
    case("pyramid", "Opaque pyramid and hidden edges",
         "Check whether front faces hide back edges consistently. Three.js uses a separate depth-tested dashed pass for hidden edges.", []),
    case("surface", "Solid of revolution and a space curve",
         "Both sides receive the same 384 quadrilateral surface faces. Compare rotation smoothness and visibility of the curve as it passes around the solid.", [
        "curve: x=1.3*cos(t), y=1.3*sin(t), z=t/pi-2, t=(0,4*pi), samples=300, color=red, lw=2.5",
    ]),
    case("labels", "Math labels and live construction",
         "Move a, rotate, resize, and enlarge the page. Both renderers use the same KaTeX labels; geometry sliders must preserve the camera.", [
        "interactive-var: a, 0.2, 2, 37", "interactive-var-start: 1",
        "point: (a,1,1), red", "vector: (0,0,0), (a,1,1), blue",
        "right-angle: at=(0,0,0), dir1=(1,0,0), dir2=(0,1,0), size=0.4",
        "angle: dir1=(1,0,0), dir2=(0,1,1), radius=0.7",
        "text: at=(a,1,1), value=\"$P(a,1,1)$\", offset=(0.15,0.15,0.15)",
        "text: at=(-1,0,1.8), value=\"$\\theta=\\arccos\\frac{\\vec u\\cdot\\vec v}{|\\vec u||\\vec v|}$\"",
    ]),
]

base = [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1]]
apex = [0,0,1.5]
faces = [base, *[[base[i],base[(i+1)%4],apex] for i in range(4)]]
edges = [[base[i],base[(i+1)%4]] for i in range(4)] + [[p,apex] for p in base]
cases[2]["scene"]["primitives"].append(dict(type="mesh", faces=faces, edges=edges,
                                            color="#79b9cf", alpha=1, lw=2))
faces = []
def surface(i, j):
    z = -1.7+3.4*i/16
    r = 0.6+0.25*math.cos(z*2)
    theta = j*2*math.pi/24
    return [r*math.cos(theta), r*math.sin(theta), z]
for i in range(16):
    for j in range(24):
        faces.append([surface(i,j),surface(i+1,j),surface(i+1,j+1),surface(i,j+1)])
cases[3]["scene"]["primitives"].append(dict(type="mesh", faces=faces, edges=[],
                                            color="#7aa88e", alpha=1, lw=1))
for i in range(3):
    cases.append(case(f"extra-{i}", f"Additional figure {i+1}",
                      "Extra independent scenes exercise page lifecycle and renderer sharing.", [
        f"vector: (0,0,0), ({i+0.5},1,1.5), blue",
    ]))
Path(__file__).with_name("cases.json").write_text(json.dumps(cases, indent=2)+"\n")
print(f"Wrote {len(cases)} matched pairs")
