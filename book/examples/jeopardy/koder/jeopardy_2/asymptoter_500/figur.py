import plotmath
import numpy as np


def main(dirname, save):
    #
    # Define functions
    @np.vectorize
    def f(x):
        if np.abs(x + 2) > 1e-2 and np.abs(x - 3) > 1e-4:
            return -3 * x + 4 + 1 / (x + 2) - 1 / (x - 3) ** 2
        return np.nan

    # List of functions and their labels.
    functions = [f]
    fontsize = 25
    fig, ax = plotmath.plot(
        functions=functions,
        fn_labels=False,
        xmin=-8,
        xmax=8,
        ymin=-30,
        ymax=30,
        ticks=False,
        xstep=1,
        ystep=1,
        grid=True,
        lw=3,
        alpha=None,
        domain=False,
        fontsize=fontsize,
        figsize=None,
    )

    x = np.linspace(-20, 20, 2**20)
    y = -3 * x + 4
    ax.plot(x, y, ls="--", lw=3, alpha=1, color=plotmath.COLORS.get("red"))
    ax.vlines(
        x=-2,
        ymin=-30,
        ymax=30,
        linestyles="dashed",
        colors=plotmath.COLORS.get("red"),
        lw=2.5,
    )
    ax.vlines(
        x=3,
        ymin=-30,
        ymax=30,
        linestyles="dashed",
        colors=plotmath.COLORS.get("red"),
        lw=3,
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

    # NOTE: Set `save=True` to save
    #  figure. `save=False` to display figure.
    main(dirname=dirname, save=True)
