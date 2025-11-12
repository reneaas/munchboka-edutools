import plotmath
import numpy as np


def main(dirname, save):
    #
    # Define functions
    def f(x):
        return x**2 * ((x - 4) ** 2) ** (1 / 3)

    # List of functions and their labels.
    functions = [f]
    fontsize = 30
    fig, ax = plotmath.plot(
        functions=[],
        fn_labels=False,
        xmin=-3,
        xmax=6,
        ymin=-6,
        ymax=12,
        ticks=False,
        xstep=1,
        ystep=1,
        grid=True,
        lw=2.5,
        alpha=None,
        domain=False,
        fontsize=fontsize,
        figsize=None,
    )

    x = np.linspace(-3, 6, 2**25)
    y = f(x)
    ax.plot(x, y, lw=2.5, alpha=1, color=plotmath.COLORS.get("blue"))

    ax.text(
        x=5,
        y=7,
        s="B",
        fontsize=fontsize,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="black"),
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
