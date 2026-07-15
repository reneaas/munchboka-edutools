from munchboka_edutools.directives._plot_common import (
    augment_svg_root,
    prepare_inline_svg,
    rewrite_svg_ids,
    strip_root_svg_size,
)


def test_strip_root_svg_size_removes_width_and_height_only_from_root():
    svg = '<svg width="432pt" height="288pt" viewBox="0 0 432 288"><rect width="5"/></svg>'

    stripped = strip_root_svg_size(svg)

    assert stripped.startswith('<svg viewBox="0 0 432 288">')
    assert '<rect width="5"/>' in stripped


def test_rewrite_svg_ids_updates_url_and_href_references():
    svg = (
        '<svg><defs><path id="marker_1"/></defs>'
        '<use xlink:href="#marker_1"/>'
        '<path style="clip-path: url(#marker_1)"/>'
        '<path id="DejaVuSans-41"/></svg>'
    )

    rewritten = rewrite_svg_ids(svg, "pfx_")

    assert 'id="pfx_marker_1"' in rewritten
    assert 'xlink:href="#pfx_marker_1"' in rewritten
    assert "url(#pfx_marker_1)" in rewritten
    assert 'id="DejaVuSans-41"' in rewritten


def test_augment_svg_root_adds_class_accessibility_and_width():
    svg = '<svg viewBox="0 0 10 10"><path/></svg>'

    augmented = augment_svg_root(svg, alt="Testfigur", width="60%")

    assert 'class="graph-inline-svg"' in augmented
    assert 'role="img"' in augmented
    assert 'aria-label="Testfigur"' in augmented
    assert "width:60%" in augmented


def test_prepare_inline_svg_runs_standard_pipeline():
    svg = (
        '<svg width="10pt" height="10pt" viewBox="0 0 10 10">'
        '<defs><path id="a"/></defs><use href="#a"/></svg>'
    )

    prepared = prepare_inline_svg(svg, content_hash="abc123", alt="Alt", width="42")

    assert 'width="10pt"' not in prepared
    assert 'height="10pt"' not in prepared
    assert 'class="graph-inline-svg"' in prepared
    assert 'aria-label="Alt"' in prepared
    assert "width:42px" in prepared
    assert 'id="cpl_abc123_' in prepared
    assert 'href="#cpl_abc123_' in prepared
