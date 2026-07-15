from munchboka_edutools.directives._plot_config import PlotConfig, parse_figsize


def test_plot_config_defaults_match_legacy_plot_defaults():
    config = PlotConfig.from_values({}, default_usetex=True)

    assert config.xmin == -6
    assert config.xmax == 6
    assert config.ymin == -6
    assert config.ymax == 6
    assert config.xstep == 1
    assert config.ystep == 1
    assert config.fontsize == 20
    assert config.lw == 2.5
    assert config.alpha is None
    assert config.ticks is True
    assert config.grid is True
    assert config.endpoint_markers is False
    assert config.use_usetex is True
    assert config.handdrawn is False
    assert config.align == "center"
    assert config.alt == "Tilpasset figur"


def test_plot_config_grid_and_ticks_default_independently_to_true():
    ticks_off = PlotConfig.from_values({"ticks": "false"})
    grid_off = PlotConfig.from_values({"grid": "false"})

    assert ticks_off.ticks is False
    assert ticks_off.grid is True
    assert grid_off.ticks is True
    assert grid_off.grid is False


def test_plot_config_parses_numeric_expressions_and_figsize():
    config = PlotConfig.from_values(
        {
            "xmin": "-2*pi",
            "xmax": "2*pi",
            "fontsize": "18",
            "lw": "3.5",
            "alpha": "0.25",
            "figsize": "(7, 4.5)",
        }
    )

    assert round(config.xmin, 6) == round(-6.283185307179586, 6)
    assert round(config.xmax, 6) == round(6.283185307179586, 6)
    assert config.fontsize == 18
    assert config.lw == 3.5
    assert config.alpha == 0.25
    assert config.figsize == (7.0, 4.5)


def test_plot_config_handdrawn_forces_usetex_off():
    config = PlotConfig.from_values({"handdrawn": "true"}, default_usetex=True)

    assert config.handdrawn is True
    assert config.use_usetex is False


def test_plot_config_tracks_name_internal_and_cache_flags():
    config = PlotConfig.from_values(
        {
            "name": "visible-name",
            "internal": None,
            "internal-name": "hidden-name",
            "debug": None,
            "nocache": None,
            "class": ["alpha", "beta"],
            "width": "70%",
            "align": "left",
            "alt": "Alt text",
        }
    )

    assert config.explicit_name == "visible-name"
    assert config.internal_mode is True
    assert config.internal_name == "hidden-name"
    assert config.stable_name == "visible-name"
    assert config.debug_mode is True
    assert config.nocache is True
    assert config.classes == ["alpha", "beta"]
    assert config.width == "70%"
    assert config.align == "left"
    assert config.alt == "Alt text"


def test_parse_figsize_accepts_tuple_and_rejects_non_positive_values():
    assert parse_figsize("[6, 3]") == (6.0, 3.0)
    assert parse_figsize("(0, 3)") is None
    assert parse_figsize("not-a-size") is None
