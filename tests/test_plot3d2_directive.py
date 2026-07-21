import re
from pathlib import Path

import numpy as np
import plotmath
from matplotlib.colors import to_hex
from sphinx.application import Sphinx

from munchboka_edutools.directives.plot3d_2 import (
    _curve_arrow_faces,
    _curve_depth_weights,
    _curve_front_back_segments,
    _curve_local_depth_weights,
    _curve_points,
    _curve_segment_collections,
    _parse_curve_primitive,
    _parse_point_primitive,
    _parse_plane_primitive,
    _parse_prism_primitive,
    _parse_pyramid_primitive,
    _parse_sphere_primitive,
    _parse_solid_of_revolution_primitive,
    _parse_text_primitive,
    _parse_vector_primitive,
    _front_back_poly_facecolors,
    _front_back_poly_faces,
    _plane_surface_grids,
    _render_plot3d2,
    _save_plot3d2_svg,
    _sphere_guide_segments,
    _sphere_surface_grids,
    _tick_values,
)


def test_plot3d2_tick_values_exclude_axis_endpoints_and_origin():
    assert _tick_values(-2, 2, 1) == [-1, 1]
    assert _tick_values(-3, 3, 1) == [-2, -1, 1, 2]


def test_plot3d2_vector_parser_uses_plotmath_blue_by_default():
    vector = _parse_vector_primitive("(0, 0, 0), (1, 2, 3)")

    assert vector == {
        "start": (0.0, 0.0, 0.0),
        "end": (1.0, 2.0, 3.0),
        "color": plotmath.COLORS["blue"],
    }


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


def test_plot3d2_curve_segments_use_camera_depth_gradient():
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

    assert len(segment_groups) >= 4
    assert any(group["linestyle"] == "solid" for group in segment_groups)
    assert any(group["linestyle"] != "solid" for group in segment_groups)
    assert len(rounded) > 2


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
        "edgecolor": "black",
        "alpha": 0.5,
    }


def test_plot3d2_pyramid_parser_accepts_regular_ngon_form():
    pyramid = _parse_pyramid_primitive(
        "center=(0, 0, 0), radius=2, sides=4, apex=(0, 0, 3), color=green"
    )

    assert pyramid["apex"] == (0.0, 0.0, 3.0)
    assert pyramid["color"] == plotmath.COLORS["green"]
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

        x_axis = ax.lines[0]
        xs, ys, zs = x_axis.get_data_3d()
        assert list(xs) == [-2, 2]
        assert list(ys) == [0, 0]
        assert list(zs) == [0, 0]
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
   xlabel: X-axis
   ylabel: Y-axis
   zlabel: Z-axis
   xstep: 1
   ystep: 1
   zstep: 1
   curve: x=cos(t), y=sin(t), z=t/3, trange=(0, 2*pi), color=red, samples=64
   vector: (0, 0, 0), (1, 1, 2)
   point: (1, 0, 2), red
   plane: equation=z = x + y, xrange=(-1, 1), yrange=(-1, 1), color=orange, alpha=0.3
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
    assert "X-axis" in html
    assert "Y-axis" in html
    assert "Z-axis" in html
    assert to_hex(plotmath.COLORS["blue"]) in html
    assert to_hex(plotmath.COLORS["red"]) in html
    assert to_hex(plotmath.COLORS["orange"]) in html
    assert to_hex(plotmath.COLORS["teal"]) in html
    assert "A, B" in html
    assert "En enkel 3D-figur." in html
