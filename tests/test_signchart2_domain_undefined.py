import matplotlib

matplotlib.use("Agg")

from munchboka_edutools.directives.signchart2 import plot


def test_signchart2_log_domain_shows_undefined_region_as_times():
    # log(x, 2) is undefined for x <= 0 over the reals.
    fig, ax = plot("log(x, 2)", include_factors=False)

    times_count = sum(1 for t in ax.texts if t.get_text() == "$\\times$")

    # Expect one \times on the x=0 boundary point and one \times in the (-∞, 0) interval.
    assert times_count == 2

    matplotlib.pyplot.close(fig)
