import re
from pathlib import Path

import numpy as np
import plotmath
from matplotlib.colors import to_hex
from sphinx.application import Sphinx

import munchboka_edutools.directives.plot3d_2 as plot3d2_module
from munchboka_edutools.directives._plot_macros import parse_plot_macros
from munchboka_edutools.directives.plot3d_2 import (
    _angle_arc_points,
    _curve_arrow_faces,
    _curve_depth_weights,
    _curve_front_back_segments,
    _curve_local_depth_weights,
    _curve_points,
    _curve_segment_collections,
    _curve_xy_style_index,
    _grid_values,
    _line_box_segment,
    _line_shaded_segments,
    _parse_angle_primitive,
    _parse_curve_primitive,
    _parse_line_segment_primitive,
    _parse_line_primitive,
    _parse_ngon_primitive,
    _parse_normal_segment_primitive,
    _parse_point_primitive,
    _parse_plane_primitive,
    _parse_prism_primitive,
    _parse_pyramid_primitive,
    _parse_right_angle_primitive,
    _parse_sphere_primitive,
    _parse_solid_of_revolution_primitive,
    _parse_text_primitive,
    _parse_vector_primitive,
    _plot3d2_macro_context,
    _plot3d2_matplotlib_text_context,
    _front_back_poly_facecolors,
    _front_back_poly_faces,
    _plane_surface_grids,
    _render_plot3d2,
    _normal_segment_points,
    _right_angle_points,
    _save_plot3d2_svg,
    _sphere_guide_segments,
    _sphere_surface_grids,
    _tick_values,
    _vector_arrow_geometry,
)


def test_plot3d2_tick_values_exclude_axis_endpoints_and_origin():
    assert _tick_values(-2, 2, 1) == [-1, 1]
    assert _tick_values(-3, 3, 1) == [-2, -1, 1, 2]


def test_plot3d2_grid_values_include_axis_endpoints_and_origin():
    assert _grid_values(-2, 2, 1) == [-2, -1, 0, 1, 2]
    assert _grid_values(-3, 3, 2) == [-2, 0, 2]


def test_plot3d2_vector_parser_uses_plotmath_blue_by_default():
    vector = _parse_vector_primitive("(0, 0, 0), (1, 2, 3)")

    assert vector == {
        "start": (0.0, 0.0, 0.0),
        "end": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["blue"],
    }


def test_plot3d2_vector_arrow_geometry_uses_small_capped_head_at_endpoint():
    vector = _parse_vector_primitive("(0, 0, 0), (10, 0, 0), red")
    geometry = _vector_arrow_geometry(
        vector,
        elev=22,
        azim=-55,
        xrange=(-5, 5),
        yrange=(-5, 5),
        zrange=(-5, 5),
    )
    shaft, head_faces = geometry
    shaft_start, shaft_end = (np.asarray(point, dtype=float) for point in shaft)
    tip = np.asarray(head_faces[0][0], dtype=float)
    head_length = float(np.linalg.norm(tip - shaft_end))

    assert np.allclose(shaft_start, [0, 0, 0])
    assert np.allclose(tip, [10, 0, 0])
    assert np.allclose(shaft_end, [9.6, 0, 0])
    assert np.isclose(head_length, 0.4)
    assert len(head_faces) == 1
    assert len(head_faces[0]) == 3


def test_plot3d2_line_parser_accepts_point_direction_form():
    line = _parse_line_primitive("point=(0, 0, 0), direction=(1, 2, 3), color=red, lw=2, style=dashed")

    assert line == {
        "point": (0.0, 0.0, 0.0),
        "direction": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["red"],
        "lw": 2.0,
        "style": "dashed",
    }


def test_plot3d2_line_parser_accepts_through_form_and_defaults():
    line = _parse_line_primitive("through=[(-1, 0, 1), (1, 2, 3)]")

    assert line == {
        "point": (-1.0, 0.0, 1.0),
        "direction": (2.0, 2.0, 2.0),
        "color": plotmath.COLORS["blue"],
        "lw": None,
        "style": "solid",
    }


def test_plot3d2_line_parser_rejects_zero_direction():
    assert _parse_line_primitive("point=(1, 2, 3), direction=(0, 0, 0)") is None
    assert _parse_line_primitive("through=[(1, 2, 3), (1, 2, 3)]") is None


def test_plot3d2_line_box_segment_clips_to_plot_ranges():
    line = _parse_line_primitive("point=(0, 0, 0), direction=(1, 1, 1)")
    segment = _line_box_segment(
        line,
        xrange=(-1, 2),
        yrange=(-2, 1),
        zrange=(-3, 3),
    )

    assert segment == ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))


def test_plot3d2_line_shaded_segments_use_camera_depth_gradient():
    line = _parse_line_primitive("point=(0, 0, 0), direction=(1, 1, 1), color=red")
    segment = ((-1.0, -1.0, -1.0), (1.0, 1.0, 1.0))
    segments, colors = _line_shaded_segments(line, segment, elev=22, azim=-55)
    rounded_colors = {
        tuple(round(float(channel), 4) for channel in color)
        for color in colors
    }

    assert len(segments) > 20
    assert len(rounded_colors) > 2


def test_plot3d2_line_segment_parser_accepts_positional_form():
    segment = _parse_line_segment_primitive("(0, 0, 0), (1, 2, 3), red, style=dashed, lw=2")

    assert segment == {
        "start": (0.0, 0.0, 0.0),
        "end": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["red"],
        "lw": 2.0,
        "style": "dashed",
    }


def test_plot3d2_line_segment_parser_accepts_keyword_form_and_defaults():
    segment = _parse_line_segment_primitive("from=(-1, 0, 1), to=(1, 2, 3)")

    assert segment == {
        "start": (-1.0, 0.0, 1.0),
        "end": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["blue"],
        "lw": None,
        "style": "solid",
    }


def test_plot3d2_line_segment_parser_rejects_zero_length_segment():
    assert _parse_line_segment_primitive("(1, 2, 3), (1, 2, 3)") is None


def test_plot3d2_normal_segment_parser_accepts_line_definitions():
    normal_segment = _parse_normal_segment_primitive(
        "point1=(0, 0, 0), direction1=(1, 0, 0), point2=(0, 1, 1), direction2=(0, 1, 0), color=#777777, style=dashed, right-angle-size=0.25"
    )

    assert normal_segment == {
        "kind": "line-line",
        "point1": (0.0, 0.0, 0.0),
        "direction1": (1.0, 0.0, 0.0),
        "point2": (0.0, 1.0, 1.0),
        "direction2": (0.0, 1.0, 0.0),
        "color": "#777777",
        "lw": None,
        "style": "dashed",
        "right_angles": True,
        "right_angle_color": "black",
        "right_angle_size": 0.25,
        "endpoint_points": True,
        "endpoint_color": "black",
    }


def test_plot3d2_normal_segment_points_are_perpendicular_to_both_lines():
    normal_segment = _parse_normal_segment_primitive(
        "point1=(3, 0, 4), direction1=(2, 0, 0.5), point2=(1, 3, 1), direction2=(2, 0, -0.5)"
    )
    foot1, foot2 = _normal_segment_points(normal_segment)
    segment = np.asarray(foot2) - np.asarray(foot1)

    assert np.allclose(foot1, (-4.0, 0.0, 2.25))
    assert np.allclose(foot2, (-4.0, 3.0, 2.25))
    assert abs(float(np.dot(segment, normal_segment["direction1"]))) < 1e-12
    assert abs(float(np.dot(segment, normal_segment["direction2"]))) < 1e-12


def test_plot3d2_normal_segment_parser_accepts_point_plane_normal_form():
    normal_segment = _parse_normal_segment_primitive(
        "point=(1, 2, 3), plane-normal=(0, 0, 1), plane-point=(0, 0, 0), color=#777777, style=dotted, right-angle-size=0.2"
    )

    assert normal_segment == {
        "kind": "point-plane",
        "point": (1.0, 2.0, 3.0),
        "plane_normal": (0.0, 0.0, 1.0),
        "plane_point": (0.0, 0.0, 0.0),
        "color": "#777777",
        "lw": None,
        "style": "dotted",
        "right_angles": True,
        "right_angle_color": "black",
        "right_angle_size": 0.2,
        "endpoint_points": True,
        "endpoint_color": "black",
    }


def test_plot3d2_normal_segment_points_project_point_to_plane():
    normal_segment = _parse_normal_segment_primitive(
        "point=(1, 2, 5), plane=z = 2, color=gray"
    )
    foot, point = _normal_segment_points(normal_segment)

    assert np.allclose(foot, (1.0, 2.0, 2.0))
    assert np.allclose(point, (1.0, 2.0, 5.0))


def test_plot3d2_normal_segment_endpoint_points_can_be_disabled():
    normal_segment = _parse_normal_segment_primitive(
        "point=(1, 2, 5), plane=z = 2, points=off"
    )

    assert normal_segment["endpoint_points"] is False


def test_plot3d2_right_angle_parser_accepts_direction_form():
    right_angle = _parse_right_angle_primitive(
        "at=(0, 0, 0), dir1=(1, 0, 0), dir2=(0, 1, 0), size=0.4, color=red, lw=2"
    )

    assert right_angle == {
        "at": (0.0, 0.0, 0.0),
        "dir1": (1.0, 0.0, 0.0),
        "dir2": (0.0, 1.0, 0.0),
        "clamp_to_targets": False,
        "size": 0.4,
        "color": plotmath.COLORS["red"],
        "lw": 2.0,
    }


def test_plot3d2_right_angle_parser_accepts_to_form_and_defaults():
    right_angle = _parse_right_angle_primitive("at=(1, 1, 1), to1=(2, 1, 1), to2=(1, 1, 3)")

    assert right_angle == {
        "at": (1.0, 1.0, 1.0),
        "dir1": (1.0, 0.0, 0.0),
        "dir2": (0.0, 0.0, 2.0),
        "clamp_to_targets": True,
        "size": 0.35,
        "color": "black",
        "lw": None,
    }


def test_plot3d2_right_angle_points_are_orthogonalized():
    right_angle = _parse_right_angle_primitive(
        "at=(0, 0, 0), dir1=(1, 0, 0), dir2=(1, 1, 0), size=0.5"
    )
    points = _right_angle_points(right_angle)

    assert np.allclose(points, [(0.5, 0, 0), (0.5, 0.5, 0), (0, 0.5, 0)])


def test_plot3d2_right_angle_to_form_terminates_on_short_normal_segment():
    right_angle = _parse_right_angle_primitive(
        "at=(0, 0, 0), to1=(1, 0, 0), to2=(0, 0.2, 0), size=0.5"
    )
    points = _right_angle_points(right_angle)

    assert np.allclose(points, [(0.5, 0, 0), (0.5, 0.2, 0), (0, 0.2, 0)])


def test_plot3d2_angle_parser_accepts_direction_form():
    angle = _parse_angle_primitive(
        "dir1=(1, 0, 0), dir2=(0, 1, 0), radius=0.5, color=red, lw=2"
    )

    assert angle == {
        "at": (0.0, 0.0, 0.0),
        "dir1": (1.0, 0.0, 0.0),
        "dir2": (0.0, 1.0, 0.0),
        "radius": 0.5,
        "color": plotmath.COLORS["red"],
        "lw": 2.0,
        "samples": 64,
    }


def test_plot3d2_angle_arc_points_span_dirs_from_anchor():
    angle = _parse_angle_primitive(
        "at=(1, 2, 3), dir1=(2, 0, 0), dir2=(0, 3, 0), radius=0.5, samples=9"
    )
    points = _angle_arc_points(angle, elev=22, azim=-55)

    assert points is not None
    assert np.allclose(points[0], [1.5, 2.0, 3.0])
    assert np.allclose(points[-1], [1.0, 2.5, 3.0])


def test_plot3d2_angle_arc_antiparallel_uses_camera_facing_plane():
    angle = _parse_angle_primitive("dir1=(1, 0, 0), dir2=(-1, 0, 0), radius=1, samples=17")
    points = _angle_arc_points(angle, elev=90, azim=0)

    assert points is not None
    assert np.allclose(points[0], [1.0, 0.0, 0.0])
    assert np.allclose(points[-1], [-1.0, 0.0, 0.0], atol=1e-12)
    assert np.max(np.abs(points[:, 2])) < 1e-12
    assert np.max(np.abs(points[:, 1])) > 0.9


def test_plot3d2_point_parser_uses_plotmath_blue_by_default():
    point = _parse_point_primitive("(1, 2, 3)")

    assert point == {
        "coords": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["blue"],
    }


def test_plot3d2_point_parser_accepts_optional_color():
    point = _parse_point_primitive("(1, 2, 3), red")

    assert point == {
        "coords": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["red"],
    }


def test_plot3d2_curve_parser_accepts_parametric_form():
    curve = _parse_curve_primitive(
        "x=cos(t), y=sin(t), z=t/2, trange=(0, 2*pi), color=red, lw=2, samples=64"
    )

    assert curve == {
        "x": "cos(t)",
        "y": "sin(t)",
        "z": "t/2",
        "trange": (0.0, 2 * np.pi),
        "color": plotmath.COLORS["red"],
        "lw": 2.0,
        "samples": 64,
        "arrows": True,
        "arrow_count": 3,
    }


def test_plot3d2_curve_parser_uses_defaults():
    curve = _parse_curve_primitive("x=t, y=t^2, z=0")

    assert curve == {
        "x": "t",
        "y": "t^2",
        "z": "0",
        "trange": (-5.0, 5.0),
        "color": plotmath.COLORS["blue"],
        "lw": None,
        "samples": 300,
        "arrows": True,
        "arrow_count": 3,
    }


def test_plot3d2_curve_parser_accepts_t_range_alias():
    curve = _parse_curve_primitive("x=sin(t), y=sin(t), z=t, t=(0, 4*pi), color=blue, lw=2")
    xs, ys, zs = _curve_points(curve)

    assert curve["trange"] == (0.0, 4 * np.pi)
    assert np.allclose([xs[0], ys[0], zs[0]], [0, 0, 0])


def test_plot3d2_curve_points_evaluate_parametric_expressions():
    curve = _parse_curve_primitive("x=t, y=t^2, z=0, trange=(-1, 1), samples=3")
    xs, ys, zs = _curve_points(curve)

    assert np.allclose(xs, [-1, 0, 1])
    assert np.allclose(ys, [1, 0, 1])
    assert np.allclose(zs, [0, 0, 0])


def test_plot3d2_macros_expand_repeat_and_let_for_points():
    expanded, macro_ctx = parse_plot_macros(
        [
            "let: h = 2",
            "repeat: n=1..2; point: (n, 0, h)",
        ]
    )

    with _plot3d2_macro_context(macro_ctx.sympy_locals):
        points = [
            _parse_point_primitive(line.split(":", 1)[1].strip())
            for line in expanded
        ]

    assert expanded == ["point: (1, 0, h)", "point: (2, 0, h)"]
    assert [point["coords"] for point in points] == [
        (1.0, 0.0, 2.0),
        (2.0, 0.0, 2.0),
    ]


def test_plot3d2_macros_support_defs_in_curve_expressions():
    expanded, macro_ctx = parse_plot_macros(
        [
            "let: h = 3",
            "def: scale(t) = h*t",
            "curve: x=scale(t), y=0, z=t, t=(0, 1), samples=2",
        ]
    )

    with _plot3d2_macro_context(macro_ctx.sympy_locals):
        curve = _parse_curve_primitive(expanded[0].split(":", 1)[1].strip())
        xs, ys, zs = _curve_points(curve)

    assert np.allclose(xs, [0, 3])
    assert np.allclose(ys, [0, 0])
    assert np.allclose(zs, [0, 1])


def test_plot3d2_macros_expand_macro_use_for_ngon():
    expanded, macro_ctx = parse_plot_macros(
        [
            "macro: face(s, c)",
            "   ngon: [(0, 0, 0), (s, 0, 0), (0, s, s)], color=c",
            "endmacro",
            "use: face(2, #13579b)",
        ]
    )

    with _plot3d2_macro_context(macro_ctx.sympy_locals):
        ngon = _parse_ngon_primitive(expanded[0].split(":", 1)[1].strip())

    assert expanded == ["ngon: [(0, 0, 0), (2, 0, 0), (0, 2, 2)], color=#13579b"]
    assert ngon["vertices"] == [
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (0.0, 2.0, 2.0),
    ]
    assert ngon["color"] == "#13579b"


def test_plot3d2_curve_segments_split_front_and_back():
    curve = _parse_curve_primitive("x=sin(t), y=sin(t), z=t, t=(0, 4*pi), samples=64")
    front_segments, back_segments = _curve_front_back_segments(curve, elev=22, azim=-55)
    view_direction = np.array(
        [
            np.cos(np.radians(22)) * np.cos(np.radians(-55)),
            np.cos(np.radians(22)) * np.sin(np.radians(-55)),
            np.sin(np.radians(22)),
        ]
    )
    xs, ys, zs = _curve_points(curve)
    points = np.column_stack([xs, ys, zs])
    finite = np.all(np.isfinite(points), axis=1)
    depths = points[finite] @ view_direction
    depth_cutoff = float(np.min(depths) + np.ptp(depths) / 2)

    assert front_segments
    assert back_segments
    assert all(len(segment) >= 2 for segment in front_segments + back_segments)
    assert all(
        np.mean(segment @ view_direction) >= depth_cutoff - 1e-9
        for segment in front_segments
    )
    assert all(
        np.mean(segment @ view_direction) <= depth_cutoff + 1e-9
        for segment in back_segments
    )


def test_plot3d2_curve_segments_use_xy_quadrant_styles_and_local_shading():
    curve = _parse_curve_primitive("x=cos(t), y=sin(t), z=t, t=(0, 4*pi), samples=64")
    segment_groups = _curve_segment_collections(
        curve,
        elev=22,
        azim=-55,
    )
    rounded = {
        tuple(round(float(channel), 4) for channel in color)
        for group in segment_groups
        for color in group["colors"]
    }
    style_names = {group["name"] for group in segment_groups}

    assert {"solid", "dashdot", "dashed"}.issubset(style_names)
    assert len(rounded) > 2


def test_plot3d2_curve_linestyle_uses_xy_quadrants():
    assert _curve_xy_style_index(1, -1) == 2
    assert _curve_xy_style_index(1, 1) == 1
    assert _curve_xy_style_index(-1, 1) == 1
    assert _curve_xy_style_index(-1, -1) == 0
    assert _curve_xy_style_index(0, -1, fallback=2) == 2
    assert _curve_xy_style_index(1, 0, fallback=0) == 0
    assert _curve_xy_style_index(0, 0) == 1


def test_plot3d2_curve_shading_uses_local_depth_contrast():
    curve = _parse_curve_primitive("x=3*cos(t), y=3*sin(t), z=t/10, t=(0, 6*pi), samples=240")
    xs, ys, zs = _curve_points(curve)
    points = np.column_stack([xs, ys, zs])
    finite = np.all(np.isfinite(points), axis=1)

    global_weights = _curve_depth_weights(points, finite, elev=22, azim=-55)
    local_weights = _curve_local_depth_weights(
        points,
        finite,
        elev=22,
        azim=-55,
        global_weights=global_weights,
    )
    globally_far = global_weights < 0.35

    assert np.ptp(local_weights[globally_far]) > np.ptp(global_weights[globally_far])


def test_plot3d2_curve_arrow_faces_have_tip_on_curve():
    curve = _parse_curve_primitive("x=cos(t), y=sin(t), z=t, t=(0, 4*pi), samples=64")
    faces, colors = _curve_arrow_faces(curve, elev=22, azim=-55)
    xs, ys, zs = _curve_points(curve)
    sampled_points = np.column_stack([xs, ys, zs])
    extent = float(np.max(np.ptp(sampled_points, axis=0)))

    assert len(faces) == 3
    assert len(colors) == 3
    for face in faces:
        tip = np.asarray(face[0], dtype=float)
        base_center = (np.asarray(face[1], dtype=float) + np.asarray(face[2], dtype=float)) / 2
        tip_idx = int(np.argmin(np.linalg.norm(sampled_points - tip, axis=1)))
        tangent = sampled_points[tip_idx + 1] - sampled_points[tip_idx - 1]
        tangent = tangent / np.linalg.norm(tangent)
        arrow_axis = tip - base_center
        arrow_axis_length = float(np.linalg.norm(arrow_axis))
        arrow_axis = arrow_axis / arrow_axis_length
        arrow_width = float(np.linalg.norm(np.asarray(face[1], dtype=float) - np.asarray(face[2], dtype=float)))

        assert np.linalg.norm(sampled_points[tip_idx] - tip) < 1e-12
        assert np.dot(tangent, arrow_axis) > 0.999
        assert arrow_axis_length < 0.05 * extent
        assert arrow_width < 0.03 * extent


def test_plot3d2_text_parser_accepts_quoted_value_with_comma():
    text_item = _parse_text_primitive(
        'at=(1, 2, 3), value="A, B", color=teal, fontsize=14, offset=(0.1, 0.2, 0.3), ha=left, va=bottom'
    )

    assert text_item == {
        "at": (1.0, 2.0, 3.0),
        "value": "A, B",
        "color": plotmath.COLORS["teal"],
        "fontsize": 14.0,
        "offset": (0.1, 0.2, 0.3),
        "ha": "left",
        "va": "bottom",
    }


def test_plot3d2_text_parser_uses_defaults():
    text_item = _parse_text_primitive('at=(1, 2, 3), label="P"')

    assert text_item == {
        "at": (1.0, 2.0, 3.0),
        "value": "P",
        "color": "black",
        "fontsize": None,
        "offset": (0.0, 0.0, 0.0),
        "ha": "center",
        "va": "center",
    }


def test_plot3d2_plane_parser_accepts_equation_form():
    plane = _parse_plane_primitive(
        "equation=z = 2*x - y + 1, xrange=(-2, 2), yrange=(-3, 3), color=green, alpha=0.25"
    )

    assert plane == {
        "kind": "equation",
        "equation": "z = 2*x - y + 1",
        "xrange": (-2.0, 2.0),
        "yrange": (-3.0, 3.0),
        "color": plotmath.COLORS["green"],
        "alpha": 0.25,
    }


def test_plot3d2_plane_parser_accepts_normal_point_form():
    plane = _parse_plane_primitive("normal=(1, 1, 1), point=(0, 0, 1), span=(4, 2)")

    assert plane == {
        "kind": "normal-point",
        "normal": (1.0, 1.0, 1.0),
        "point": (0.0, 0.0, 1.0),
        "span": (4.0, 2.0),
        "color": plotmath.COLORS["blue"],
        "alpha": 0.35,
    }


def test_plot3d2_pyramid_parser_accepts_explicit_base_form():
    pyramid = _parse_pyramid_primitive(
        "base=[(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)], apex=(1, 1, 3), color=purple, alpha=0.5"
    )

    assert pyramid == {
        "base": [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 2.0, 0.0),
            (0.0, 2.0, 0.0),
        ],
        "apex": (1.0, 1.0, 3.0),
        "color": plotmath.COLORS["purple"],
        "base_color": plotmath.COLORS["purple"],
        "side_color": plotmath.COLORS["purple"],
        "edgecolor": "black",
        "alpha": 0.5,
    }


def test_plot3d2_pyramid_parser_accepts_regular_ngon_form():
    pyramid = _parse_pyramid_primitive(
        "center=(0, 0, 0), radius=2, sides=4, apex=(0, 0, 3), color=green"
    )

    assert pyramid["apex"] == (0.0, 0.0, 3.0)
    assert pyramid["color"] == plotmath.COLORS["green"]
    assert pyramid["base_color"] == plotmath.COLORS["green"]
    assert pyramid["side_color"] == plotmath.COLORS["green"]
    assert pyramid["alpha"] == 0.45
    assert len(pyramid["base"]) == 4
    assert np.allclose(
        pyramid["base"],
        [
            (2.0, 0.0, 0.0),
            (0.0, 2.0, 0.0),
            (-2.0, 0.0, 0.0),
            (0.0, -2.0, 0.0),
        ],
    )


def test_plot3d2_pyramid_parser_accepts_base_and_side_colors():
    pyramid = _parse_pyramid_primitive(
        "base=[(0, 0, 0), (1, 0, 0), (0, 1, 0)], apex=(0, 0, 1), base-color=green, side-color=none"
    )

    assert pyramid["color"] is None
    assert pyramid["base_color"] == plotmath.COLORS["green"]
    assert pyramid["side_color"] is None


def test_plot3d2_pyramid_color_overrides_base_and_side_colors():
    pyramid = _parse_pyramid_primitive(
        "base=[(0, 0, 0), (1, 0, 0), (0, 1, 0)], apex=(0, 0, 1), color=purple, base-color=green, side-color=none"
    )

    assert pyramid["color"] == plotmath.COLORS["purple"]
    assert pyramid["base_color"] == plotmath.COLORS["purple"]
    assert pyramid["side_color"] == plotmath.COLORS["purple"]


def test_plot3d2_ngon_parser_accepts_explicit_vertices():
    ngon = _parse_ngon_primitive(
        "[(0, 0, 0), (2, 0, 0), (2, 1, 1), (0, 1, 1)], color=green, alpha=0.5"
    )

    assert ngon == {
        "vertices": [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 1.0, 1.0),
            (0.0, 1.0, 1.0),
        ],
        "color": plotmath.COLORS["green"],
        "edgecolor": "black",
        "alpha": 0.5,
    }


def test_plot3d2_ngon_parser_accepts_points_keyword_and_defaults():
    ngon = _parse_ngon_primitive("points=[(0, 0, 0), (1, 0, 0), (0, 1, 0)]")

    assert ngon == {
        "vertices": [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        ],
        "color": plotmath.COLORS["blue"],
        "edgecolor": "black",
        "alpha": 0.45,
    }


def test_plot3d2_prism_parser_accepts_explicit_base_vector_form():
    prism = _parse_prism_primitive(
        "base=[(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)], vector=(0, 0, 3), color=yellow, alpha=0.5"
    )

    assert prism == {
        "base": [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 2.0, 0.0),
            (0.0, 2.0, 0.0),
        ],
        "top": [
            (0.0, 0.0, 3.0),
            (2.0, 0.0, 3.0),
            (2.0, 2.0, 3.0),
            (0.0, 2.0, 3.0),
        ],
        "color": plotmath.COLORS["yellow"],
        "edgecolor": "black",
        "alpha": 0.5,
    }


def test_plot3d2_prism_parser_accepts_regular_ngon_height_form():
    prism = _parse_prism_primitive(
        "center=(0, 0, 0), radius=2, sides=4, height=3, color=green"
    )

    assert prism["color"] == plotmath.COLORS["green"]
    assert prism["alpha"] == 0.45
    assert len(prism["base"]) == 4
    assert np.allclose(
        prism["base"],
        [
            (2.0, 0.0, 0.0),
            (0.0, 2.0, 0.0),
            (-2.0, 0.0, 0.0),
            (0.0, -2.0, 0.0),
        ],
    )
    assert np.allclose(
        prism["top"],
        [
            (2.0, 0.0, 3.0),
            (0.0, 2.0, 3.0),
            (-2.0, 0.0, 3.0),
            (0.0, -2.0, 3.0),
        ],
    )


def test_plot3d2_sphere_parser_uses_defaults():
    sphere = _parse_sphere_primitive("")

    assert sphere == {
        "center": (0.0, 0.0, 0.0),
        "radius": 1.0,
        "color": plotmath.COLORS["blue"],
        "alpha": 0.55,
        "resolution": 48,
    }


def test_plot3d2_sphere_parser_accepts_options():
    sphere = _parse_sphere_primitive(
        "center=(1, 2, 3), radius=1.5, color=green, alpha=0.4, resolution=16"
    )

    assert sphere == {
        "center": (1.0, 2.0, 3.0),
        "radius": 1.5,
        "color": plotmath.COLORS["green"],
        "alpha": 0.4,
        "resolution": 16,
    }


def test_plot3d2_sphere_surface_grids_match_center_and_radius():
    sphere = _parse_sphere_primitive("center=(1, 2, 3), radius=2, resolution=16")
    x_grid, y_grid, z_grid, facecolors = _sphere_surface_grids(
        sphere,
        elev=22,
        azim=-55,
    )
    distances = np.sqrt((x_grid - 1) ** 2 + (y_grid - 2) ** 2 + (z_grid - 3) ** 2)
    rounded = {
        tuple(round(float(channel), 4) for channel in facecolor)
        for row in facecolors
        for facecolor in row
    }
    alpha_values = facecolors[..., 3]

    assert np.allclose(distances, 2)
    assert facecolors.shape == (*x_grid.shape, 4)
    assert len(rounded) > 1
    assert float(np.max(alpha_values) - np.min(alpha_values)) < 1e-9


def test_plot3d2_sphere_guides_split_front_and_back_segments():
    sphere = _parse_sphere_primitive("center=(1, 2, 3), radius=2, resolution=16")
    front_segments, back_segments = _sphere_guide_segments(
        sphere,
        elev=22,
        azim=-55,
    )

    assert front_segments
    assert back_segments
    assert all(len(segment) >= 2 for segment in front_segments + back_segments)


def test_plot3d2_poly_faces_split_into_front_and_back_groups():
    faces = [
        [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)],
        [(0, 0, 0), (2, 0, 0), (1, 1, 3)],
        [(2, 0, 0), (2, 2, 0), (1, 1, 3)],
        [(2, 2, 0), (0, 2, 0), (1, 1, 3)],
        [(0, 2, 0), (0, 0, 0), (1, 1, 3)],
    ]

    front_faces, back_faces = _front_back_poly_faces(
        faces,
        elev=22,
        azim=-55,
    )

    assert front_faces
    assert back_faces
    assert len(front_faces) + len(back_faces) == len(faces)


def test_plot3d2_front_back_face_fill_varies_with_side_orientation():
    faces = [
        [(0, 0, 0), (2, 0, 0), (1, 1, 3)],
        [(2, 0, 0), (2, 2, 0), (1, 1, 3)],
        [(2, 2, 0), (0, 2, 0), (1, 1, 3)],
    ]

    facecolors = _front_back_poly_facecolors(
        faces,
        color=plotmath.COLORS["purple"],
        alpha=0.45,
        elev=22,
        azim=-55,
        front=True,
    )
    rounded = {
        tuple(round(float(channel), 4) for channel in facecolor)
        for facecolor in facecolors
    }
    brightness_values = [
        sum(float(channel) for channel in facecolor[:3]) / 3
        for facecolor in facecolors
    ]

    assert len(facecolors) == 3
    assert len(rounded) > 1
    assert max(brightness_values) - min(brightness_values) > 0.08


def test_plot3d2_equation_plane_grids_satisfy_equation():
    plane = _parse_plane_primitive(
        "equation=z = 2*x - y + 1, xrange=(-2, 2), yrange=(-3, 3)"
    )
    x_grid, y_grid, z_grid = _plane_surface_grids(
        plane,
        xrange=(-5, 5),
        yrange=(-5, 5),
        zrange=(-5, 5),
    )

    assert np.allclose(z_grid, 2 * x_grid - y_grid + 1)


def test_plot3d2_implicit_vertical_plane_grids_satisfy_equation():
    plane = _parse_plane_primitive("equation=x = 2, yrange=(-3, 3), zrange=(-1, 1)")
    x_grid, y_grid, z_grid = _plane_surface_grids(
        plane,
        xrange=(-5, 5),
        yrange=(-5, 5),
        zrange=(-5, 5),
    )

    assert np.allclose(x_grid, 2)
    assert np.allclose(y_grid, [[-3, 3], [-3, 3]])
    assert np.allclose(z_grid, [[-1, -1], [1, 1]])


def test_plot3d2_normal_point_plane_grids_are_perpendicular_to_normal():
    plane = _parse_plane_primitive("normal=(1, 1, 1), point=(0, 0, 1), span=(4, 2)")
    x_grid, y_grid, z_grid = _plane_surface_grids(
        plane,
        xrange=(-5, 5),
        yrange=(-5, 5),
        zrange=(-5, 5),
    )
    coords = np.stack([x_grid, y_grid, z_grid], axis=-1)
    offsets = coords - np.array([0.0, 0.0, 1.0])

    assert np.allclose(offsets @ np.array([1.0, 1.0, 1.0]), 0)


def test_plot3d2_solid_of_revolution_parser_uses_plotmath_blue_by_default():
    solid = _parse_solid_of_revolution_primitive("sqrt(x), (0, 4)")

    assert solid == {
        "expr": "sqrt(x)",
        "xrange": (0.0, 4.0),
        "color": plotmath.COLORS["blue"],
    }


def test_plot3d2_renderer_draws_centered_axes_labels_and_ticks():
    fig, ax = _render_plot3d2(
        xrange=(-2, 2),
        yrange=(-3, 3),
        zrange=(-1, 1),
        xlabel="X-axis",
        ylabel="Y-axis",
        zlabel="Z-axis",
        xstep=1,
        ystep=1,
        zstep=1,
    )
    try:
        labels = {text.get_text() for text in ax.texts}

        assert "X-axis" in labels
        assert "Y-axis" in labels
        assert "Z-axis" in labels
        assert {"-1", "1"}.issubset(labels)
        assert "-3" not in labels
        assert "3" not in labels
        assert len(ax.lines) >= 3
        assert len(ax.collections) >= 3

        x_label = next(text for text in ax.texts if text.get_text() == "X-axis")
        assert x_label.get_position_3d() == (2, -0.312, 0)

        z_label = next(text for text in ax.texts if text.get_text() == "Z-axis")
        assert z_label.get_position_3d() == (-0.10400000000000001, 0, 1)

        x_axis = ax.lines[0]
        xs, ys, zs = x_axis.get_data_3d()
        assert list(xs) == [-2, 2]
        assert list(ys) == [0, 0]
        assert list(zs) == [0, 0]
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_suppresses_centered_axes_with_axis_off():
    point = _parse_point_primitive("(1, 2, 3), red")
    fig, ax = _render_plot3d2(
        axis=False,
        points=[point],
        xlabel="X-axis",
        ylabel="Y-axis",
        zlabel="Z-axis",
    )
    try:
        labels = {text.get_text() for text in ax.texts}
        point_collections = [
            collection
            for collection in ax.collections
            if hasattr(collection, "_offsets3d")
        ]

        assert labels == set()
        assert len(ax.lines) == 0
        assert point_collections
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_xy_grid_without_centered_axes():
    fig, ax = _render_plot3d2(
        axis=False,
        grid=True,
        xrange=(-1, 1),
        yrange=(-2, 2),
        zrange=(-3, 3),
        xstep=1,
        ystep=2,
    )
    try:
        grid_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and collection.get_zorder() == 1
        ]

        assert len(ax.lines) == 0
        assert grid_collections
        segments = grid_collections[0]._segments3d
        assert len(segments) == 6

        points = np.asarray([point for segment in segments for point in segment], dtype=float)
        assert np.allclose(points[:, 2], 0.0)
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_suppresses_axis_labels_with_none():
    fig, ax = _render_plot3d2(
        ticks=False,
        xlabel="X-axis",
        ylabel="none",
        zlabel="NoNe",
    )
    try:
        labels = {text.get_text() for text in ax.texts}

        assert "X-axis" in labels
        assert "none" not in labels
        assert "NoNe" not in labels
        assert "$y$" not in labels
        assert "$z$" not in labels
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_uses_math_axis_label_defaults():
    fig, ax = _render_plot3d2(ticks=False)
    try:
        labels = {text.get_text() for text in ax.texts}

        assert {"$x$", "$y$", "$z$"}.issubset(labels)
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_curve():
    curve = _parse_curve_primitive(
        "x=cos(t), y=sin(t), z=t/2, trange=(0, 2*pi), color=red, lw=2, samples=64"
    )
    fig, ax = _render_plot3d2(curves=[curve], ticks=False)
    try:
        line_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and float(collection.get_linewidths()[0]) >= 2.0
        ]
        arrow_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Poly3DCollection"
            and len(collection.get_facecolors()) == 3
        ]
        assert len(line_collections) >= 4
        assert arrow_collections
        line_widths = [float(collection.get_linewidths()[0]) for collection in line_collections]
        assert 2.0 in line_widths
        assert max(line_widths) > 2.0
        linestyles = [collection.get_linestyle() for collection in line_collections]
        assert any(linestyle == [(0.0, None)] for linestyle in linestyles)
        assert any(linestyle != [(0.0, None)] for linestyle in linestyles)
        curve_colors = {
            tuple(round(float(channel), 4) for channel in color)
            for collection in line_collections
            for color in collection.get_colors()
        }
        assert len(curve_colors) > 2
        assert any(len(collection.get_facecolors()) == 3 for collection in arrow_collections)
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_clipped_line():
    line = _parse_line_primitive("point=(0, 0, 0), direction=(1, 1, 1), color=red, lw=2, style=dashdot")
    fig, ax = _render_plot3d2(
        lines=[line],
        xrange=(-1, 2),
        yrange=(-2, 1),
        zrange=(-3, 3),
        ticks=False,
    )
    try:
        line_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and float(collection.get_linewidths()[0]) == 2.0
            and len(collection.get_colors()) > 2
        ]
        assert line_collections
        rendered = line_collections[-1]
        segments = rendered._segments3d
        endpoints = np.concatenate([segments[0], segments[-1]], axis=0)
        colors = {
            tuple(round(float(channel), 4) for channel in color)
            for color in rendered.get_colors()
        }

        assert np.allclose(np.min(endpoints, axis=0), [-1.0, -1.0, -1.0], atol=0.05)
        assert np.allclose(np.max(endpoints, axis=0), [1.0, 1.0, 1.0], atol=0.05)
        assert len(segments) < 95
        assert len(colors) > 2
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_line_segment_between_endpoints():
    line_segment = _parse_line_segment_primitive("(0, 0, 0), (1, 1, 1), red, style=dashed, lw=2")
    fig, ax = _render_plot3d2(line_segments=[line_segment], ticks=False)
    try:
        segment_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and float(collection.get_linewidths()[0]) == 2.0
            and len(collection.get_colors()) > 2
        ]
        assert segment_collections
        rendered = segment_collections[-1]
        segments = rendered._segments3d
        endpoints = np.concatenate([segments[0], segments[-1]], axis=0)
        colors = {
            tuple(round(float(channel), 4) for channel in color)
            for color in rendered.get_colors()
        }

        assert np.allclose(np.min(endpoints, axis=0), [0.0, 0.0, 0.0], atol=0.02)
        assert np.allclose(np.max(endpoints, axis=0), [1.0, 1.0, 1.0], atol=0.02)
        assert len(segments) < 95
        assert len(colors) > 2
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_normal_segment_with_right_angle_markers():
    normal_segment = _parse_normal_segment_primitive(
        "point1=(0, 0, 0), direction1=(1, 0, 0), point2=(0, 1, 1), direction2=(0, 1, 0), color=#777777, style=dashed, right-angle-size=0.25"
    )
    fig, ax = _render_plot3d2(normal_segments=[normal_segment], ticks=False)
    try:
        normal_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and collection.get_zorder() == 12
        ]
        marker_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and collection.get_zorder() == 35
        ]

        assert normal_collections
        assert len(marker_collections) == 2
        assert all(len(collection._segments3d) == 2 for collection in marker_collections)
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_point_plane_normal_marker_with_segment_direction():
    normal_segment = _parse_normal_segment_primitive(
        "point=(1, 2, 3), plane-normal=(0, 0, 1), plane-point=(0, 0, 0), color=#777777, style=dashed, right-angle-size=0.25"
    )
    fig, ax = _render_plot3d2(normal_segments=[normal_segment], ticks=False)
    try:
        marker_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and collection.get_zorder() == 35
        ]

        assert len(marker_collections) == 1
        marker_segments = marker_collections[0]._segments3d
        marker_points = np.concatenate(marker_segments, axis=0)
        marker_vectors = [np.asarray(segment[1]) - np.asarray(segment[0]) for segment in marker_segments]
        endpoint_collections = [
            collection
            for collection in ax.collections
            if hasattr(collection, "_offsets3d")
            and to_hex(collection.get_facecolors()[0]) == to_hex("black")
        ]

        assert np.isclose(np.min(marker_points[:, 2]), 0.0)
        assert np.isclose(np.max(marker_points[:, 2]), 0.25)
        assert any(np.allclose(vector[:2], (0.0, 0.0)) for vector in marker_vectors)
        assert any(
            np.isclose(abs(vector[0]), 0.25)
            and np.isclose(vector[1], 0.0)
            and np.isclose(vector[2], 0.0)
            for vector in marker_vectors
        )
        assert len(endpoint_collections) == 2
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_right_angle_marker():
    right_angle = _parse_right_angle_primitive(
        "at=(0, 0, 0), dir1=(1, 0, 0), dir2=(0, 1, 0), size=0.5, color=red, lw=2"
    )
    fig, ax = _render_plot3d2(right_angles=[right_angle], ticks=False)
    try:
        marker_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and float(collection.get_linewidths()[0]) == 2.0
            and to_hex(collection.get_colors()[0]) == to_hex(plotmath.COLORS["red"])
        ]

        assert marker_collections
        assert marker_collections[-1].get_zorder() == 35
        assert len(marker_collections[-1]._segments3d) == 2
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_angle_arc_with_depth_shading():
    angle = _parse_angle_primitive(
        "dir1=(1, 0, 0), dir2=(0, 1, 1), radius=0.5, color=purple, lw=2"
    )
    fig, ax = _render_plot3d2(angles=[angle], ticks=False)
    try:
        angle_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and collection.get_zorder() == 35
            and float(collection.get_linewidths()[0]) == 2.0
            and len(collection.get_colors()) > 2
        ]

        assert angle_collections
        assert len(angle_collections[-1]._segments3d) == angle["samples"] - 1
        assert len(
            {
                tuple(round(float(channel), 4) for channel in color)
                for color in angle_collections[-1].get_colors()
            }
        ) > 1
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_layers_vectors_and_points_above_lines():
    line = _parse_line_primitive("point=(0, 0, 0), direction=(1, 1, 1), color=blue")
    vector = _parse_vector_primitive("(0, 0, 0), (1, 1, 1), red")
    point = _parse_point_primitive("(1, 1, 1), green")
    fig, ax = _render_plot3d2(lines=[line], vectors=[vector], points=[point], ticks=False)
    try:
        line_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and len(collection.get_colors()) > 2
        ]
        vector_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Line3DCollection"
            and len(collection.get_colors()) == 1
            and to_hex(collection.get_colors()[0]) == to_hex(plotmath.COLORS["red"])
        ]
        point_collections = [
            collection
            for collection in ax.collections
            if hasattr(collection, "_offsets3d")
            and to_hex(collection.get_facecolors()[0]) == to_hex(plotmath.COLORS["green"])
        ]

        assert ax.computed_zorder is False
        assert line_collections
        assert vector_collections
        assert point_collections
        assert max(collection.get_zorder() for collection in line_collections) < min(
            collection.get_zorder() for collection in vector_collections
        )
        assert max(collection.get_zorder() for collection in vector_collections) < min(
            collection.get_zorder() for collection in point_collections
        )
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_point():
    point = _parse_point_primitive("(1, 2, 3), red")
    fig, ax = _render_plot3d2(points=[point])
    try:
        fig.canvas.draw()
        scatter_collections = [
            collection
            for collection in ax.collections
            if hasattr(collection, "_offsets3d")
        ]
        assert scatter_collections
        xs, ys, zs = scatter_collections[-1]._offsets3d
        assert list(xs) == [1.0]
        assert list(ys) == [2.0]
        assert list(zs) == [3.0]
        assert to_hex(scatter_collections[-1].get_facecolors()[0]) == to_hex(
            plotmath.COLORS["red"]
        )
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_text():
    text_item = _parse_text_primitive(
        'at=(1, 2, 3), value="A, B", color=teal, fontsize=14, offset=(0.1, 0.2, 0.3), ha=left, va=bottom'
    )
    fig, ax = _render_plot3d2(texts=[text_item], fontsize=10)
    try:
        rendered = [item for item in ax.texts if item.get_text() == "A, B"]
        assert rendered
        label = rendered[0]
        assert to_hex(label.get_color()) == to_hex(plotmath.COLORS["teal"])
        assert label.get_fontsize() == 14.0
        assert label.get_ha() == "left"
        assert label.get_va() == "bottom"
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_matplotlib_text_context_enforces_latex_font_and_restores():
    import matplotlib

    old_values = {
        key: matplotlib.rcParams.get(key)
        for key in ("text.usetex", "font.family", "font.serif")
    }
    matplotlib.rcParams["text.usetex"] = False
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.serif"] = ["DejaVu Serif"]

    try:
        with _plot3d2_matplotlib_text_context(matplotlib, use_usetex=True):
            assert matplotlib.rcParams["text.usetex"] is True
            assert matplotlib.rcParams["font.family"] == ["serif"]
            assert matplotlib.rcParams["font.serif"][0] == "Computer Modern Roman"

        assert matplotlib.rcParams["text.usetex"] is False
        assert matplotlib.rcParams["font.family"] == ["sans-serif"]
        assert matplotlib.rcParams["font.serif"] == ["DejaVu Serif"]
    finally:
        for key, value in old_values.items():
            matplotlib.rcParams[key] = value


def test_plot3d2_renderer_draws_plane():
    plane = _parse_plane_primitive("equation=x + y + z = 3, color=green")
    fig, ax = _render_plot3d2(planes=[plane])
    try:
        fig.canvas.draw()
        surface_collections = [
            collection
            for collection in ax.collections
            if collection.get_alpha() == 0.35 and len(collection.get_facecolors()) >= 1
        ]
        assert surface_collections
        assert to_hex(surface_collections[0].get_facecolors()[0]) == to_hex(
            plotmath.COLORS["green"]
        )
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_pyramid():
    pyramid = _parse_pyramid_primitive(
        "base=[(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)], apex=(1, 1, 3), color=purple"
    )
    fig, ax = _render_plot3d2(pyramids=[pyramid])
    try:
        fig.canvas.draw()
        pyramid_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Poly3DCollection"
        ]
        assert len(pyramid_collections) >= 2
        assert sum(len(collection.get_facecolors()) for collection in pyramid_collections) == 5
        alpha_values = {
            round(float(facecolor[-1]), 4)
            for collection in pyramid_collections
            for facecolor in collection.get_facecolors()
        }
        assert len(alpha_values) > 1
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_pyramid_with_transparent_side_faces():
    pyramid = _parse_pyramid_primitive(
        "base=[(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)], apex=(1, 1, 3), base-color=green, side-color=none"
    )
    fig, ax = _render_plot3d2(pyramids=[pyramid])
    try:
        fig.canvas.draw()
        pyramid_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Poly3DCollection"
        ]
        face_alphas = [
            round(float(facecolor[-1]), 4)
            for collection in pyramid_collections
            for facecolor in collection.get_facecolors()
        ]
        visible_facecolors = [
            facecolor
            for collection in pyramid_collections
            for facecolor in collection.get_facecolors()
            if float(facecolor[-1]) > 0
        ]

        assert 0.0 in face_alphas
        assert any(alpha > 0 for alpha in face_alphas)
        assert any(
            float(facecolor[1]) > float(facecolor[0])
            and float(facecolor[1]) > float(facecolor[2])
            for facecolor in visible_facecolors
        )
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_ngon():
    ngon = _parse_ngon_primitive(
        "[(0, 0, 0), (2, 0, 0), (2, 1, 1), (0, 1, 1)], color=green"
    )
    fig, ax = _render_plot3d2(ngons=[ngon])
    try:
        fig.canvas.draw()
        ngon_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Poly3DCollection"
            and len(collection.get_facecolors()) == 1
        ]
        assert ngon_collections
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_prism():
    prism = _parse_prism_primitive(
        "base=[(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)], vector=(0, 0, 3), color=yellow"
    )
    fig, ax = _render_plot3d2(prisms=[prism])
    try:
        fig.canvas.draw()
        prism_collections = [
            collection
            for collection in ax.collections
            if collection.__class__.__name__ == "Poly3DCollection"
        ]
        assert len(prism_collections) >= 2
        assert sum(len(collection.get_facecolors()) for collection in prism_collections) == 6
        alpha_values = {
            round(float(facecolor[-1]), 4)
            for collection in prism_collections
            for facecolor in collection.get_facecolors()
        }
        assert len(alpha_values) > 1
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_sphere():
    sphere = _parse_sphere_primitive("center=(1, 2, 3), radius=1.5, color=green")
    fig, ax = _render_plot3d2(spheres=[sphere], ticks=False)
    try:
        fig.canvas.draw()
        surface_collections = [
            collection
            for collection in ax.collections
            if len(collection.get_facecolors()) > 10
        ]
        assert surface_collections
        rounded = {
            tuple(round(float(channel), 4) for channel in facecolor)
            for facecolor in surface_collections[0].get_facecolors()
        }
        assert len(rounded) > 1
        assert len(ax.lines) > 3
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_renderer_draws_solid_of_revolution_surface():
    fig, ax = _render_plot3d2(
        xrange=(0, 4),
        yrange=(-3, 3),
        zrange=(-3, 3),
        solids_of_revolution=[
            _parse_solid_of_revolution_primitive("sqrt(x), (0, 4), red")
        ],
    )
    try:
        # 3 axis arrow quivers + 1 surface collection, plus any tick collections.
        assert len(ax.collections) >= 4
        fig.canvas.draw()
        unique_facecolor_counts = []
        for collection in ax.collections:
            facecolors = collection.get_facecolors()
            if len(facecolors) <= 1:
                continue
            rounded = {
                tuple(round(float(channel), 4) for channel in facecolor)
                for facecolor in facecolors
            }
            unique_facecolor_counts.append(len(rounded))
        assert any(count > 1 for count in unique_facecolor_counts)
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)


def test_plot3d2_svg_export_uses_full_tight_canvas(tmp_path: Path):
    fig, _ax = _render_plot3d2()
    svg_path = tmp_path / "plot3d2.svg"
    try:
        _save_plot3d2_svg(fig, svg_path)
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)

    svg = svg_path.read_text(encoding="utf8")
    match = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    assert match is not None
    width, height = (float(value) for value in match.groups())
    assert 350 <= width <= 365
    assert 350 <= height <= 365


def test_plot3d2_directive_enforces_usetex_font_before_render(tmp_path: Path, monkeypatch):
    import matplotlib
    import matplotlib.pyplot as plt

    captured: dict[str, object] = {}

    def fake_render_plot3d2(**params):
        captured["use_usetex"] = params["use_usetex"]
        captured["text_usetex"] = matplotlib.rcParams["text.usetex"]
        captured["font_family"] = list(matplotlib.rcParams["font.family"])
        captured["font_serif"] = list(matplotlib.rcParams["font.serif"])
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        return fig, ax

    def fake_save_plot3d2_svg(fig, path):
        Path(path).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
            "<text>ok</text></svg>",
            encoding="utf8",
        )

    monkeypatch.setattr(plot3d2_module, "_render_plot3d2", fake_render_plot3d2)
    monkeypatch.setattr(plot3d2_module, "_save_plot3d2_svg", fake_save_plot3d2_svg)

    old_values = {
        key: matplotlib.rcParams.get(key)
        for key in ("text.usetex", "font.family", "font.serif")
    }
    matplotlib.rcParams["text.usetex"] = False
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.serif"] = ["DejaVu Serif"]

    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    try:
        (src / "conf.py").write_text(
            """
project = 'plot3d2-usetex-test'
extensions = ['munchboka_edutools.directives.plot3d_2']
html_theme = 'basic'
plot_default_usetex = False
""".lstrip(),
            encoding="utf8",
        )
        (src / "index.rst").write_text(
            """
Plot3d 2 usetex test
====================

.. plot3d-2::

   usetex: true
   text: at=(0, 0, 0), value="$x$"
""".lstrip(),
            encoding="utf8",
        )

        app = Sphinx(
            srcdir=str(src),
            confdir=str(src),
            outdir=str(build),
            doctreedir=str(doctree),
            buildername="html",
            warningiserror=False,
            freshenv=True,
        )
        app.build()

        assert captured["use_usetex"] is True
        assert captured["text_usetex"] is True
        assert captured["font_family"] == ["serif"]
        assert captured["font_serif"][0] == "Computer Modern Roman"
        assert matplotlib.rcParams["text.usetex"] is False
        assert matplotlib.rcParams["font.family"] == ["sans-serif"]
        assert matplotlib.rcParams["font.serif"] == ["DejaVu Serif"]
    finally:
        for key, value in old_values.items():
            matplotlib.rcParams[key] = value


def test_plot3d2_directive_renders_inline_svg(tmp_path: Path):
    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        """
project = 'plot3d2-test'
extensions = ['munchboka_edutools']
html_theme = 'basic'
plot_default_usetex = False
""".lstrip(),
        encoding="utf8",
    )
    (src / "index.rst").write_text(
        """
Plot3d 2 test
==============

.. plot3d-2::
   :width: 55%

   xrange: (-2, 2)
   yrange: (-2, 2)
   zrange: (-1, 3)
   axis: off
   xlabel: X-axis
   ylabel: none
   zlabel: Z-axis
   xstep: 1
   ystep: 1
   zstep: 1
   let: h = 2
   def: lift(n) = h + n / 10
   macro: raised_point(n, c)
      point: (n, 0, lift(n)), c
   endmacro
   repeat: n=1..2; use: raised_point(n, #13579b)
   curve: x=cos(t), y=sin(t), z=t/3, trange=(0, 2*pi), color=red, samples=64
   line: point=(0, 0, 0), direction=(1, -1, 1), color=#2468ac, style=dashed
   line-segment: (-1, 0, 0), (0, 1, 1), color=#8642aa, style=dotted
   normal-segment: point1=(0, 0, 0), direction1=(1, 0, 0), point2=(0, 1, 1), direction2=(0, 1, 0), color=#777777, style=dashed, right-angle-size=0.25
   normal-segment: point=(1, 1, 2), plane=z = 0, color=#777777, style=dotted, right-angle-size=0.2
   right-angle: at=(0, 0, 0), dir1=(1, 0, 0), dir2=(0, 1, 0), size=0.35, color=red
   angle: dir1=(1, 0, 0), dir2=(0, 1, 1), radius=0.45, color=#123abc, lw=2
   vector: (0, 0, 0), (1, 1, 2)
   point: (1, 0, 2), red
   plane: equation=z = x + y, xrange=(-1, 1), yrange=(-1, 1), color=orange, alpha=0.3
   ngon: [(0, 0, 0), (1, 0, 0), (0, 1, 1)], color=green, alpha=0.4
   prism: center=(0, 0, 0), radius=0.7, sides=4, height=1.5, color=yellow, alpha=0.35
   pyramid: base=[(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], apex=(0, 0, 2), color=purple
   sphere: center=(-1, 1, 1), radius=0.5, color=skyblue, alpha=0.6, resolution=16
   text: at=(0, 0, 2), value="A, B", color=teal, offset=(0, 0, 0.2)
   solid-of-revolution: sqrt(x), (0, 2), green

   En enkel 3D-figur.
""".lstrip(),
        encoding="utf8",
    )

    app = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=False,
        freshenv=True,
    )
    app.build()

    html = (build / "index.html").read_text(encoding="utf8")

    assert '<svg' in html
    assert 'graph-inline-svg' in html
    assert 'aria-label="3D-koordinatsystem"' in html
    assert "Y-axis" not in html
    assert "X-axis" not in html
    assert "Z-axis" not in html
    assert to_hex(plotmath.COLORS["blue"]) in html
    assert to_hex(plotmath.COLORS["red"]) in html
    assert to_hex(plotmath.COLORS["orange"]) in html
    assert to_hex(plotmath.COLORS["teal"]) in html
    assert "#13579b" in html
    assert "A, B" in html
    assert "En enkel 3D-figur." in html
