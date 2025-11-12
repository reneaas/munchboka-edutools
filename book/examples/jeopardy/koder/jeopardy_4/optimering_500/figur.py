import plotmath
import numpy as np
import matplotlib.pyplot as plt


def main(dirname, save):
    #
    # Define functions

    def f(x):
        return 1 - x**2

    def make_tangent_fn(a):
        slope = -2 * a
        intercept = f(a) - slope * a

        def tangent_fn(x):
            return slope * x + intercept

        return tangent_fn

    # List of functions and their labels.
    functions = [f]

    fig, ax = plotmath.plot(
        functions=functions,
        fn_labels=True,
        xmin=-0.1,
        xmax=1.4,
        ymin=-0.1,
        ymax=1.4,
        ticks=False,
        xstep=1,
        ystep=1,
        grid=True,
        lw=2.5,
        alpha=None,
        domain=(0, 1),
        fontsize=20,
        figsize=None,
    )

    a = 0.5
    tangent_fn = make_tangent_fn(a=a)
    x = np.linspace(-100, 100, 2**20)
    y = tangent_fn(x)
    ax.plot(x, y, color=plotmath.COLORS.get("red"), lw=2.5)

    ax.plot(a, f(a), "ko", ms=10, alpha=0.8)
    A = (0, tangent_fn(0))
    B = ((a**2 + 1) / (2 * a), 0)

    ax.plot(*A, "ko", ms=10, alpha=0.8)
    ax.plot(*B, "ko", ms=10, alpha=0.8)

    ax.text(
        x=A[0] + 0.02,
        y=A[1],
        s="$A$",
        fontsize=20,
        ha="left",
        va="bottom",
    )

    ax.text(
        x=B[0],
        y=B[1] + 0.05,
        s="$B$",
        fontsize=20,
        ha="left",
        va="bottom",
    )

    ax.text(
        x=a + 0.02,
        y=f(a),
        s="$P(a, f(a))$",
        fontsize=20,
        ha="left",
        va="bottom",
    )

    ax.plot(0, 0, "ko", ms=10, alpha=0.8)
    ax.text(
        x=+0.02,
        y=0,
        s="$O$",
        fontsize=20,
        ha="left",
        va="bottom",
    )

    # NOTE: Select an appropriate `dirname` to save the figure.
    # The directory `dirname` will be created automatically if it does not exist already.
    if save:
        fname = __file__.split("/")[-1].replace(".py", ".svg")
        plotmath.savefig(
            dirname=dirname, fname=fname
        )  # Lagrer figuren i `dirname`-directory

    if not save:

        plotmath.show()


if __name__ == "__main__":

    import pathlib

    # Get the directory where the script is located
    current_dir = str(pathlib.Path(__file__).resolve().parent)

    parts = current_dir.split("/")
    for i in range(len(parts)):
        if parts[~i] == "koder":
            parts[~i] = "figurer"
            break

    dirname = "/".join(parts)

    # NOTE: Set `save=True` to save figure. `save=False` to display figure.
    main(dirname=dirname, save=True)
