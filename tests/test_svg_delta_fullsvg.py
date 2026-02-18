from munchboka_edutools.directives.svg_delta import compute_svg_deltas, _prepare_svg_for_deltas


def _wrap_svg(body: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
        f"{body}"
        "</svg>"
    )


def test_compute_svg_deltas_falls_back_to_fullsvg_on_structure_mismatch() -> None:
    base = _wrap_svg(
        '<g id="axes_1"><g id="patch_1"><path d="M 0 0 L 1 1"/></g></g>'
        '<defs><clipPath id="pabc123"><rect x="0" y="0" width="1" height="1"/></clipPath></defs>'
    )
    # Non-volatile id mismatch (patch_1 -> patch_2) should trigger fullSvg.
    frame = _wrap_svg(
        '<g id="axes_1"><g id="patch_2"><path d="M 0 0 L 2 2"/></g></g>'
        '<defs><clipPath id="pdef456"><rect x="0" y="0" width="1" height="1"/></clipPath></defs>'
    )

    _base_svg, deltas = compute_svg_deltas([base, frame])

    assert len(deltas) == 2
    assert "fullSvg" in deltas[1]
    assert "<svg" in deltas[1]["fullSvg"]


def test_compute_svg_deltas_does_not_fallback_for_volatile_id_only() -> None:
    base = _wrap_svg(
        '<g id="axes_1"><g id="patch_1"><path d="M 0 0 L 1 1"/></g></g>'
        '<defs><clipPath id="pabc123"><rect x="0" y="0" width="1" height="1"/></clipPath></defs>'
    )
    # Only clipPath id changes (volatile p...) should not force fullSvg.
    frame = _wrap_svg(
        '<g id="axes_1"><g id="patch_1"><path d="M 0 0 L 1 1"/></g></g>'
        '<defs><clipPath id="pdef456"><rect x="0" y="0" width="1" height="1"/></clipPath></defs>'
    )

    _base_svg, deltas = compute_svg_deltas([base, frame])

    assert len(deltas) == 2
    assert "fullSvg" not in deltas[1]
    # With only volatile-id differences, we expect no meaningful changes.
    assert deltas[1].get("changes") == {}


def test_compute_svg_deltas_falls_back_on_major_region_mismatch() -> None:
    # Same id appears under a different major region (axes_* vs legend_*)
    # between frames; this indicates numeric id reuse.
    base = _wrap_svg(
        '<g id="axes_1"><path id="path_1" d="M 0 0 L 1 0"/></g>'
        '<g id="legend_1"><path id="patch_1" d="M 0 0 L 1 1"/></g>'
    )
    frame = _wrap_svg(
        '<g id="axes_1"><path id="patch_1" d="M 0 0 L 1 0"/></g>'
        '<g id="legend_1"><path id="path_1" d="M 0 0 L 1 1"/></g>'
    )

    _base_svg, deltas = compute_svg_deltas([base, frame])

    assert len(deltas) == 2
    assert "fullSvg" in deltas[1]


def test_compute_svg_deltas_falls_back_on_owner_group_mismatch() -> None:
    # Same element id stays under the same major region, but moves between
    # different Matplotlib artist groups (line2d_* vs patch_*). This indicates
    # numeric id reuse inside the region.
    base = _wrap_svg(
        '<g id="axes_1">'
        '  <g id="legend_1">'
        '    <g id="line2d_1"><path id="path_1" d="M 0 0 L 1 1"/></g>'
        "  </g>"
        "</g>"
    )
    frame = _wrap_svg(
        '<g id="axes_1">'
        '  <g id="legend_1">'
        '    <g id="patch_1"><path id="path_1" d="M 0 0 L 2 2"/></g>'
        "  </g>"
        "</g>"
    )

    _base_svg, deltas = compute_svg_deltas([base, frame])

    assert len(deltas) == 2
    assert "fullSvg" in deltas[1]


def test_compute_svg_deltas_falls_back_on_legend_local_id_churn() -> None:
    # Global id-set mismatch ratio can be small even when the legend is unstable.
    # Ensure legend-local id churn triggers fullSvg.
    many_axes_paths = "".join(f'<path id="path_{i}" d="M 0 0 L 1 1"/>' for i in range(100))

    base = _wrap_svg(
        f'<g id="axes_1">{many_axes_paths}</g>'
        '<g id="legend_1">'
        '  <path id="path_200" d="M 0 0 L 1 0"/>'
        "</g>"
    )
    frame = _wrap_svg(
        f'<g id="axes_1">{many_axes_paths}</g>'
        '<g id="legend_1">'
        '  <path id="path_201" d="M 0 0 L 1 0"/>'
        "</g>"
    )

    _base_svg, deltas = compute_svg_deltas([base, frame])

    assert len(deltas) == 2
    assert "fullSvg" in deltas[1]


def test_prepare_svg_for_deltas_does_not_collide_with_existing_ids() -> None:
    # If the input SVG already contains Matplotlib-like ids (`path_0`, `path_1`, ...),
    # auto-assigning ids as `path_{i}` would collide and corrupt delta matching.
    svg = _wrap_svg('<path id="path_0" d="M 0 0 L 1 1"/>' '<path d="M 0 0 L 2 2"/>')
    prepared = _prepare_svg_for_deltas(svg)
    assert 'id="path_0"' in prepared
    assert 'id="mb_auto_path_0"' in prepared


def test_compute_svg_deltas_falls_back_on_legend_frame_geometry_blowup() -> None:
    base = _wrap_svg(
        '<g id="axes_1"></g>'
        '<g id="legend_1">'
        '  <path id="legend_frame" style="fill: #ffffff; opacity: 0.8; stroke: #cccccc" '
        '        d="M 1 1 L 3 1 L 3 2 L 1 2 Z"/>'
        "</g>"
    )
    # Same id, but bbox explodes to almost full viewBox width.
    frame = _wrap_svg(
        '<g id="axes_1"></g>'
        '<g id="legend_1">'
        '  <path id="legend_frame" style="fill: #ffffff; opacity: 0.8; stroke: #cccccc" '
        '        d="M 0 0 L 9 0 L 9 9 L 0 9 Z"/>'
        "</g>"
    )

    _base_svg, deltas = compute_svg_deltas([base, frame])

    assert len(deltas) == 2
    assert "fullSvg" in deltas[1]
