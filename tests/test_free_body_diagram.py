"""Pure-geometry tests for the free-body-diagram directive (no Sphinx needed)."""
import math

import pytest

from munchboka_edutools.directives._free_body_geometry import (
    _assign_draw_points,
    _collinear_groups,
    axis_indicator_lines,
    build_force_lines,
    build_object,
    compile_scene,
    default_attachment,
    parse_direction,
    parse_force,
    parse_object,
    parse_velocity,
)


def test_parse_object_defaults_and_overrides():
    spec = parse_object("ball, size=2, position=(1, 3), color=teal, alpha=0.4")
    assert spec == dict(kind="ball", size=2.0, position=(1.0, 3.0), color="teal", alpha=0.4)
    assert parse_object("square")["size"] == 1.0


def test_parse_object_rejects_unknown_kind_and_options():
    with pytest.raises(ValueError, match="Unknown object"):
        parse_object("sphere")
    with pytest.raises(ValueError, match="Unsupported object options"):
        parse_object("ball, radius=2")


@pytest.mark.parametrize("kind", ["ball", "square"])
def test_ball_and_square_contact_sit_directly_below_centroid(kind):
    obj = build_object(kind, size=2.0, position=(0.0, 5.0), color="black", alpha=None)
    assert obj.centroid == (0.0, 5.0)
    assert obj.contact[0] == pytest.approx(0.0)
    assert obj.contact[1] < obj.centroid[1]
    assert obj.radius > 0


def test_toy_car_contact_sits_on_a_wheel_not_the_gap_between_them():
    obj = build_object("toy-car", size=2.0, position=(0.0, 5.0), color="black", alpha=None)
    assert obj.centroid == (0.0, 5.0)
    assert obj.contact[0] != obj.centroid[0]
    assert obj.contact[1] < obj.centroid[1]


def test_parse_direction_accepts_angle_and_vector():
    ux, uy = parse_direction("90")
    assert ux == pytest.approx(0, abs=1e-9)
    assert uy == pytest.approx(1)
    ux, uy = parse_direction("(3, 4)")
    assert math.hypot(ux, uy) == pytest.approx(1)
    assert ux == pytest.approx(0.6)
    with pytest.raises(ValueError):
        parse_direction("(0, 0)")


def test_parse_velocity_requires_angle_keyword_or_vector():
    assert parse_velocity("angle=0") == pytest.approx((1.0, 0.0))
    assert parse_velocity("(0, 2)") == pytest.approx((0.0, 1.0))
    with pytest.raises(ValueError):
        parse_velocity("30")


def test_default_attachment_gravity_and_normal_ignore_velocity():
    obj = build_object("square", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    point, direction = default_attachment("gravity", obj, None)
    assert point == obj.centroid and direction == (0.0, -1.0)
    point, direction = default_attachment("normal", obj, None)
    assert point == obj.contact and direction == (0.0, 1.0)


def test_default_attachment_friction_and_air_resistance_need_velocity():
    obj = build_object("ball", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    assert default_attachment("friction", obj, None) == (None, None)
    assert default_attachment("air-resistance", obj, None) == (None, None)

    point, direction = default_attachment("friction", obj, (1.0, 0.0))
    assert point == obj.contact and direction == (-1.0, 0.0)
    point, direction = default_attachment("friction", obj, (-1.0, 0.0))
    assert direction == (1.0, 0.0)

    point, direction = default_attachment("air-resistance", obj, (1.0, 0.0))
    assert direction == (-1.0, 0.0)
    assert point[0] > obj.centroid[0]  # projected toward the direction of motion


def test_parse_force_requires_length_and_rejects_unknown_kind():
    obj = build_object("ball", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    with pytest.raises(ValueError, match="requires length"):
        parse_force("gravity, name=\"$G$\"", obj, None)
    with pytest.raises(ValueError, match="Unknown force"):
        parse_force("buoyancy, length=1", obj, None)


def test_parse_force_without_velocity_requires_explicit_override():
    obj = build_object("ball", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    with pytest.raises(ValueError, match="no default attachment point"):
        parse_force("friction, length=0.3", obj, None)
    # An explicit override always works, with or without velocity.
    force = parse_force("friction, length=0.3, point=(0,-1), direction=0", obj, None)
    assert force["point"] == (0.0, -1.0)
    assert force["direction"] == (1.0, 0.0)


def test_parse_force_custom_requires_both_overrides():
    obj = build_object("ball", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    with pytest.raises(ValueError, match="no default attachment point"):
        parse_force("custom, length=1, name=\"$T$\"", obj, None)
    force = parse_force("custom, length=1, name=\"$T$\", point=(0,1), direction=90", obj, None)
    assert force["name"] == "$T$"
    assert force["color"] == "purple"


def test_parse_force_defaults_name_and_color_per_kind():
    obj = build_object("ball", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    force = parse_force("gravity, length=1", obj, None)
    assert force["name"] == r"$\vec G$"
    assert force["color"] == "black"
    force = parse_force("normal, length=1, color=red", obj, None)
    assert force["color"] == "red"


def test_parse_force_offset_defaults_to_none_and_accepts_an_override():
    obj = build_object("ball", size=2.0, position=(0.0, 0.0), color="black", alpha=None)
    assert parse_force("gravity, length=1", obj, None)["offset"] is None
    force = parse_force("gravity, length=1, offset=0", obj, None)
    assert force["offset"] == 0.0
    force = parse_force("gravity, length=1, offset=0.3", obj, None)
    assert force["offset"] == 0.3


def test_collinear_groups_merge_parallel_and_antiparallel_forces_on_one_line():
    forces = [
        dict(point=(0.0, 0.0), direction=(0.0, -1.0)),
        dict(point=(0.0, -0.5), direction=(0.0, 1.0)),
        dict(point=(0.0, -0.5), direction=(1.0, 0.0)),
    ]
    groups = sorted(tuple(sorted(g)) for g in _collinear_groups(forces))
    assert groups == [(0, 1), (2,)]


def test_collinear_groups_keeps_parallel_forces_on_different_lines_apart():
    forces = [
        dict(point=(0.0, 0.0), direction=(0.0, -1.0)),
        dict(point=(1.0, 0.0), direction=(0.0, -1.0)),  # same direction, different line
    ]
    groups = sorted(tuple(sorted(g)) for g in _collinear_groups(forces))
    assert groups == [(0,), (1,)]


def test_assign_draw_points_offsets_collinear_forces_by_increasing_rank():
    forces = [
        dict(point=(0.0, 0.0), direction=(0.0, -1.0)),
        dict(point=(0.0, -0.5), direction=(0.0, 1.0)),
    ]
    _assign_draw_points(forces, spacing=0.1)
    # Offset perpendicular to the shared vertical line, growing with rank so
    # the two members end up at distinct, nonzero, non-overlapping positions.
    assert forces[0]["draw_point"] == pytest.approx((0.1, 0.0))
    assert forces[1]["draw_point"] == pytest.approx((0.2, -0.5))


def test_assign_draw_points_still_offsets_a_lone_force():
    # plot's own point: primitive renders before vector: (which always draws on
    # top), so a point left exactly at its vector's tail would be invisible —
    # every force must be offset, not just ones sharing a line with another.
    forces = [dict(point=(1.0, 2.0), direction=(1.0, 0.0))]
    _assign_draw_points(forces, spacing=0.1)
    dx = forces[0]["draw_point"][0] - 1.0
    dy = forces[0]["draw_point"][1] - 2.0
    assert forces[0]["draw_point"] != (1.0, 2.0)
    assert math.hypot(dx, dy) == pytest.approx(0.1)


def test_assign_draw_points_honors_an_explicit_offset_override():
    forces = [
        dict(point=(0.0, 0.0), direction=(0.0, -1.0), offset=None),
        dict(point=(0.0, -0.5), direction=(0.0, 1.0), offset=0.5),
    ]
    _assign_draw_points(forces, spacing=0.1)
    # The auto-computed member is unaffected by its groupmate's override.
    assert forces[0]["draw_point"] == pytest.approx((0.1, 0.0))
    # The overridden member uses its own offset instead of (rank+1)*spacing.
    assert forces[1]["draw_point"] == pytest.approx((0.5, -0.5))


def test_assign_draw_points_offset_zero_disables_it():
    # A force the author knows is already clearly visible can opt out of the
    # automatic nudge entirely, landing the vector right on its true point.
    forces = [dict(point=(1.0, 2.0), direction=(1.0, 0.0), offset=0.0)]
    _assign_draw_points(forces, spacing=0.1)
    assert forces[0]["draw_point"] == (1.0, 2.0)


def test_build_force_lines_marks_true_point_and_draws_stub_when_offset():
    lines, tip = build_force_lines("red", "$F$", 1.0, (0.0, 0.0), (1.0, 0.0), (0.0, 0.2))
    # point: only ever accepts a bare (x, y) -- a trailing color token makes
    # plot.py's own regex fail to match and the whole line gets silently
    # dropped, so the mark must stay color-less even though the vector isn't.
    assert lines[0] == "point: (0, 0)"
    assert lines[1].startswith("line-segment: (0, 0), (0, 0.2)")
    assert lines[2].startswith("vector: (0, 0.2), (1, 0.2)")
    assert tip == (1.0, 0.2)


def test_build_force_lines_skips_stub_only_when_points_coincide():
    lines, _ = build_force_lines("red", "", 1.0, (0.0, 0.0), (1.0, 0.0), (0.0, 0.0))
    assert not any(line.startswith("line-segment:") for line in lines)
    assert lines[0].startswith("point:")
    assert lines[1].startswith("vector:")


def test_compile_scene_produces_plot_lines_and_bounds():
    scene = compile_scene(
        "ball, size=1, position=(0, 0), color=teal",
        [
            'gravity, length=1, name="$\\vec G$"',
            'normal, length=1, name="$\\vec N$"',
        ],
    )
    lines = scene["lines"]
    assert any(line.startswith("circle:") for line in lines)
    assert sum(line.startswith("vector:") for line in lines) == 2 + 2  # forces + axis indicator
    assert sum(line.startswith("text:") for line in lines) >= 2
    # Gravity and normal are collinear on a ball resting on flat ground, so both
    # get a point marker and an orthogonal leader segment to the offset vector.
    assert sum(line.startswith("point:") for line in lines) == 2
    assert sum(line.startswith("line-segment:") for line in lines) == 2
    xmin, xmax, ymin, ymax = scene["bounds"]
    assert xmin < 0 < xmax
    assert ymin < 0 < ymax


def test_compile_scene_requires_at_least_one_force():
    with pytest.raises(ValueError, match="at least one force"):
        compile_scene("square, size=1", [])


def test_axis_indicator_labels_sit_beyond_their_arrowheads_not_over_them():
    lines = axis_indicator_lines(xmin=0.0, ymin=0.0, extent=1.0, margin=0.5)
    x_vector, x_text, y_vector, y_text = lines
    assert x_vector == "vector: (0.5, 0.5), (1.5, 0.5), black"
    # The x label sits further right than the arrow's own tip (x=1.5), using
    # `center-right` (text extends right of the anchor) rather than
    # `center-left` (which would place it back over the arrow's shaft).
    assert x_text.startswith("text: 1.7")
    assert x_text.endswith('"$x$", center-right')
    assert y_vector == "vector: (0.5, 0.5), (0.5, 1.5), black"
    # Likewise the y label sits above its tip (y=1.5) via `top-center` (text
    # extends upward), not `bottom-center` (which would overlap the shaft).
    assert y_text.startswith("text: 0.5, 1.7")
    assert y_text.endswith('"$y$", top-center')


def test_compile_scene_can_disable_axis_indicator():
    scene = compile_scene(
        "square, size=1",
        ["gravity, length=1"],
        axis_indicator=False,
    )
    lines = scene["lines"]
    assert sum(line.startswith("vector:") for line in lines) == 1
    assert sum(line.startswith("point:") for line in lines) == 1
    # Even a lone force is offset from its true point (so the dot isn't hidden
    # under the vector's own tail), so it still gets a leader stub.
    assert sum(line.startswith("line-segment:") for line in lines) == 1
