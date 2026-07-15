from munchboka_edutools.directives._plot_build import Plot2BuildContext


def test_plot2_build_context_expands_macros_and_parses_config():
    context = Plot2BuildContext.from_values(
        [
            "let: L = 3",
            "def: f(x) = L*x",
            "repeat: n=1..2; point: (n, f(n))",
            "function: f(x), f",
            "xmin: 0",
            "xmax: L",
            "ticks: false",
            "width: 60%",
            "",
            "Caption text",
        ],
        {"align": "left", "class": ["alpha", "beta"]},
        default_usetex=False,
    )

    assert context.raw_lines[0] == "let: L = 3"
    assert context.expanded_lines == [
        "point: (1, f(1))",
        "point: (2, f(2))",
        "function: f(x), f",
        "xmin: 0",
        "xmax: L",
        "ticks: false",
        "width: 60%",
        "",
        "Caption text",
    ]
    assert context.lists["point"] == ["(1, f(1))", "(2, f(2))"]
    assert context.lists["function"] == ["f(x), f"]
    assert context.scalars["xmin"] == "0"
    assert context.scalars["xmax"] == "L"
    assert context.config.xmin == 0
    # Config scalar parsing is intentionally limited to simple SymPy constants
    # for now; legacy rendering still evaluates macro-aware bounds.
    assert context.config.xmax == 6
    assert context.config.ticks is False
    assert context.config.grid is True
    assert context.config.width == "60%"
    assert context.config.align == "left"
    assert context.config.classes == ["alpha", "beta"]
    assert context.config.use_usetex is False
    assert context.caption_lines == ["Caption text"]
    assert context.macro_ctx.numeric_functions["f"](2) == 6


def test_plot2_build_context_handles_fenced_front_matter_caption_index():
    context = Plot2BuildContext.from_values(
        [
            "---",
            "function: x",
            "xmin: -1",
            "---",
            "",
            "A caption",
        ],
        {},
    )

    assert context.lists["function"] == ["x"]
    assert context.config.xmin == -1
    assert context.caption_lines == ["A caption"]
