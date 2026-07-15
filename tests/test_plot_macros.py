from munchboka_edutools.directives._plot_macros import parse_plot_macros
from munchboka_edutools.directives.plot import _parse_plot_macros as parse_legacy_plot_macros


def test_parse_plot_macros_records_let_and_def_context():
    lines = [
        "let: L = 3",
        "def: s(x) = L*(1 + x)",
        "function: s(x), s",
        "",
        "Caption",
    ]

    expanded, ctx = parse_plot_macros(lines)

    assert expanded == ["function: s(x), s", "", "Caption"]
    assert "L" in ctx.sympy_locals
    assert "s" in ctx.sympy_locals
    assert ctx.numeric_functions["s"](2) == 9
    assert ctx.raw_bindings == ("def:s(x)=L*(1 + x)", "let:L=3")


def test_parse_plot_macros_expands_repeat():
    expanded, _ = parse_plot_macros(
        [
            "repeat: n=1..3; point: (n, n**2)",
            "",
            "Caption",
        ]
    )

    assert expanded == [
        "point: (1, 1**2)",
        "point: (2, 2**2)",
        "point: (3, 3**2)",
        "",
        "Caption",
    ]


def test_parse_plot_macros_preserves_fenced_front_matter():
    expanded, ctx = parse_plot_macros(
        [
            "---",
            "let: a = 2",
            "repeat: n=1..2; point: (n, a*n)",
            "---",
            "",
            "Caption",
        ]
    )

    assert expanded == [
        "---",
        "point: (1, a*1)",
        "point: (2, a*2)",
        "---",
        "",
        "Caption",
    ]
    assert ctx.raw_bindings == ("let:a=2",)


def test_parse_plot_macros_renames_macro_local_let_and_def_per_use():
    expanded, _ = parse_plot_macros(
        [
            "macro: scopedseg(i, color)",
            "    let: d = i / 10",
            "    def: px(x) = x + d",
            "    line-segment: (px(0), i / 5), (px(1/5), i / 5), solid, color",
            "endmacro",
            "use: scopedseg(1, #aa0000)",
            "use: scopedseg(2, #00aa00)",
            "",
            "Caption",
        ]
    )

    assert expanded == [
        "line-segment: (__mb_macro_scopedseg_1_px(0), 1 / 5), (__mb_macro_scopedseg_1_px(1/5), 1 / 5), solid, #aa0000",
        "line-segment: (__mb_macro_scopedseg_2_px(0), 2 / 5), (__mb_macro_scopedseg_2_px(1/5), 2 / 5), solid, #00aa00",
        "",
        "Caption",
    ]


def test_parse_plot_macros_matches_legacy_parser_for_representative_block():
    lines = [
        "let: L = 3",
        "def: s(x) = L*(1 - 2**(-x))",
        "repeat: n=1..2; point: (n, s(n))",
        "macro: marker(i, color)",
        "    let: d = i / 10",
        "    point: (i + d, s(i)), color",
        "endmacro",
        "use: marker(3, #123456)",
        "",
        "Caption",
    ]

    expanded, ctx = parse_plot_macros(lines)
    legacy_expanded, legacy_ctx = parse_legacy_plot_macros(lines)

    assert expanded == legacy_expanded
    assert ctx.raw_bindings == legacy_ctx.raw_bindings
    assert sorted(ctx.numeric_functions) == sorted(legacy_ctx.numeric_functions)
    assert ctx.numeric_functions["s"](2) == legacy_ctx.numeric_functions["s"](2)
