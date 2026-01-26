import matplotlib


def test_signchart2_rational_poles_render_as_crosses():
    # Force headless backend for CI/test runs
    matplotlib.use("Agg")

    from munchboka_edutools.directives.signchart2 import plot

    fig, ax = plot(
        f="(x**2 - 1)/(x**2 - 4)",
        include_factors=True,
        color=False,
    )

    try:
        # The directive draws markers using matplotlib text objects.
        texts = [t.get_text() for t in ax.texts]
        # Matplotlib stores the TeX marker with a single backslash in the value.
        times_count = sum(1 for t in texts if t == "$\\times$")

        # Expect poles at x = ±2 to be rendered as crosses, and only on the f(x)
        # sign line (factor rows should still show 0 at their own roots).
        assert times_count == 2
    finally:
        import matplotlib.pyplot as plt

        plt.close(fig)
