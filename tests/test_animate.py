"""Basic tests for animate directive."""

import pytest
import os
import tempfile
from pathlib import Path


def test_animate_var_parsing():
    """Test parsing of animation variable specification."""
    from munchboka_edutools.directives.animate import _parse_animate_var

    # Basic parsing
    var_name, values = _parse_animate_var("a, 0, 10, 11")
    assert var_name == "a"
    assert len(values) == 11
    assert values[0] == pytest.approx(0.0)
    assert values[-1] == pytest.approx(10.0)

    # With expressions
    var_name, values = _parse_animate_var("t, 0, 2*pi, 10")
    assert var_name == "t"
    assert len(values) == 10
    assert values[-1] == pytest.approx(6.283185307, rel=1e-6)


def test_variable_substitution():
    """Test variable substitution in content."""
    from munchboka_edutools.directives.animate import _substitute_variable

    content = "function: sin(a*x)\npoint: a, f(a)"
    result = _substitute_variable(content, "a", 2.5)

    assert "2.5" in result
    assert "sin(2.5*x)" in result or "sin( 2.5*x)" in result

    # Should not replace variable in middle of identifier
    content = "variable: alpha"
    result = _substitute_variable(content, "a", 1.0)
    assert "alpha" in result  # Should remain unchanged


def test_eval_expr():
    """Test expression evaluation."""
    from munchboka_edutools.directives.animate import _eval_expr

    assert _eval_expr("0") == pytest.approx(0.0)
    assert _eval_expr("pi") == pytest.approx(3.14159265, rel=1e-6)
    assert _eval_expr("2*pi") == pytest.approx(6.28318530, rel=1e-6)
    assert _eval_expr("sqrt(2)") == pytest.approx(1.41421356, rel=1e-6)
    assert _eval_expr("sin(pi/2)") == pytest.approx(1.0, abs=1e-10)


def test_parse_bool():
    """Test boolean parsing."""
    from munchboka_edutools.directives.animate import _parse_bool

    assert _parse_bool("true") is True
    assert _parse_bool("True") is True
    assert _parse_bool("yes") is True
    assert _parse_bool("on") is True
    assert _parse_bool("1") is True

    assert _parse_bool("false") is False
    assert _parse_bool("False") is False
    assert _parse_bool("no") is False
    assert _parse_bool("off") is False
    assert _parse_bool("0") is False

    assert _parse_bool("") is True  # Empty string defaults to True
    assert _parse_bool(None, default=False) is False


def test_animate_directive_imports():
    """Test that all required dependencies can be imported."""
    try:
        import PIL
        from PIL import Image

        assert True
    except ImportError:
        pytest.skip("Pillow not installed")

    try:
        import cairosvg

        assert True
    except ImportError:
        pytest.skip("cairosvg not installed")

    try:
        import imageio

        assert True
    except ImportError:
        pytest.skip("imageio not installed")


def test_animate_directive_class():
    """Test that AnimateDirective class exists and has correct structure."""
    from munchboka_edutools.directives.animate import AnimateDirective

    # Check class attributes
    assert AnimateDirective.has_content is True
    assert AnimateDirective.required_arguments == 0

    # Check that it has the required options
    assert "animate-var" in AnimateDirective.option_spec
    assert "fps" in AnimateDirective.option_spec
    assert "format" in AnimateDirective.option_spec
    assert "loop" in AnimateDirective.option_spec

    # Check that it inherits plot options
    assert "xmin" in AnimateDirective.option_spec
    assert "xmax" in AnimateDirective.option_spec
    assert "function" in AnimateDirective.option_spec or "functions" in AnimateDirective.option_spec


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
