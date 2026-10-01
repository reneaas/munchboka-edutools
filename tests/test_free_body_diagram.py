"""Pure-geometry tests for the free-body-diagram directive (no Sphinx needed)."""
import math

import pytest

from munchboka_edutools.directives._free_body_geometry import (
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


@pytest.mark.parametrize("kind", ["ball", "square", "toy-car"])
def test_object_centroid_and_contact_sit_above_ground(kind):
    obj = build_object(kind, size=2.0, position=(0.0, 5.0), color="black", alpha=None)
    assert obj.centroid == (0.0, 5.0)
    assert obj.contact[0] == pytest.approx(0.0)
    assert obj.contact[1] < obj.centroid[1]
    assert obj.radius > 0


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
    xmin, xmax, ymin, ymax = scene["bounds"]
    assert xmin < 0 < xmax
    assert ymin < 0 < ymax


def test_compile_scene_requires_at_least_one_force():
    with pytest.raises(ValueError, match="at least one force"):
        compile_scene("square, size=1", [])


def test_compile_scene_can_disable_axis_indicator():
    scene = compile_scene(
        "square, size=1",
        ["gravity, length=1"],
        axis_indicator=False,
    )
    assert sum(line.startswith("vector:") for line in scene["lines"]) == 1
