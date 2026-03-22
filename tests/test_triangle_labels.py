from munchboka_edutools.directives._triangle import (
    parse_triangle_primitive,
    triangle_angle_label_text,
    triangle_side_label_text,
)


def _eval_num(value):
    import sympy

    return float(sympy.sympify(str(value)))


def test_triangle_angle_label_text_numeric_and_exact():
    tri_numeric = parse_triangle_primitive(
        "svs=(3,60,5), angle-labels=(A=numeric)",
        _eval_num,
        {},
    )
    assert tri_numeric is not None
    assert triangle_angle_label_text(tri_numeric, "A") == "$60^\\circ$"
    assert triangle_angle_label_text(tri_numeric, "B") is None

    tri_exact = parse_triangle_primitive(
        "svs=(3,60,5), angle-labels=(A=exact)",
        _eval_num,
        {},
    )
    assert tri_exact is not None
    assert triangle_angle_label_text(tri_exact, "A") == "$60^\\circ$"

    tri_decimal = parse_triangle_primitive(
        "svs=(3,37.456,5), angle-labels=(A=numeric)",
        _eval_num,
        {},
    )
    assert tri_decimal is not None
    assert triangle_angle_label_text(tri_decimal, "A") == "$37.46^\\circ$"


def test_triangle_side_label_text_numeric_uses_max_two_decimals():
    tri_numeric = parse_triangle_primitive(
        "points=((0,0),(1,0),(0,1)), side-labels=(BC=numeric)",
        _eval_num,
        {},
    )
    assert tri_numeric is not None
    assert triangle_side_label_text(tri_numeric, "AB") is None
    assert triangle_side_label_text(tri_numeric, "CA") is None
    assert triangle_side_label_text(tri_numeric, "BC") == "1.41"