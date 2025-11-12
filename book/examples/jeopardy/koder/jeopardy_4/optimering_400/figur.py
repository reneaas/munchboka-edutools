import plotmath
import matplotlib.pyplot as plt
import numpy as np


def main(dirname, save):

    fig, ax = plt.subplots()

    ax.hlines(y=0, xmin=0, xmax=10, color="black", ls="-", lw=2.5)

    angle = 60  # degrees
    A = (10, 0)
    B = (A[0] + 10 * np.cos(np.radians(angle)), A[1] + 10 * np.sin(np.radians(angle)))
    ax.plot(*zip(A, B), color="black", lw=2.5)

    A = (0, 0)
    B = (-10 * np.cos(np.radians(angle)), 10 * np.sin(np.radians(angle)))
    ax.plot(*zip(A, B), color="black", lw=2.5)

    ax.hlines(
        y=10 * np.sin(np.radians(angle)),
        xmin=-10 * np.cos(np.radians(angle)),
        xmax=10 + 10 * np.cos(np.radians(angle)),
        color="gray",
        ls="--",
        lw=2.5,
    )

    ax.vlines(
        x=0, ymin=0, ymax=10 * np.sin(np.radians(angle)), color="gray", ls="--", lw=2.5
    )

    ax.vlines(
        x=10,
        ymin=0,
        ymax=10 * np.sin(np.radians(angle)),
        color="gray",
        ls="--",
        lw=2.5,
    )

    fontsize = 20
    ax.text(
        x=5,
        y=-0.5,
        s="$10$ cm",
        fontsize=fontsize,
        ha="center",
        va="top",
    )

    ax.text(
        x=10 + 3,
        y=0.5 * 10 * np.sin(np.radians(angle)),
        s="$10$ cm",
        fontsize=fontsize,
        ha="left",
        va="center",
    )

    ax.text(
        x=-0.5 * 10 * np.cos(np.radians(angle)) - 0.5,
        y=0.5 * 10 * np.sin(np.radians(angle)),
        s="$10$ cm",
        fontsize=fontsize,
        ha="right",
        va="center",
    )

    ax.text(
        x=0.5,
        y=0.5 * 10 * np.sin(np.radians(angle)),
        s="$x$",
        fontsize=fontsize,
        ha="left",
        va="center",
    )

    ax.axis("off")
    ax.axis("equal")

    plt.tight_layout()

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
