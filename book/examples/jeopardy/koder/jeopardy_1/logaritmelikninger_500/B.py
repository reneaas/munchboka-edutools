import plotmath
import numpy as np


def main(dirname, save):
    #
    # Define functions

    def f(x):
        return np.exp(-x) * (x - 1) * (x - 2)

    # List of functions and their labels.
    functions = [f]
    fontsize = 25
    fig, ax = plotmath.plot(
        functions=functions,
        fn_labels=False,
        xmin=-1,
        xmax=12,
        ymin=-0.3,
        ymax=0.3,
        ticks=True,
        xstep=1,
        ystep=1,
        grid=False,
        lw=2.5,
        alpha=None,
        domain=False,
        fontsize=fontsize,
        figsize=None,
    )

    ax.set_yticks([])

    ax.text(
        x=10,
        y=0.2,
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
