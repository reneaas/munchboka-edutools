import plotmath
import matplotlib.pyplot as plt
import numpy as np


def main(dirname, save):

    fig, ax = plt.subplots()

    ax.hlines(y=6, xmin=0, xmax=10, color="black", ls="-", lw=2.5)

    ax.vlines(x=0, ymin=6, ymax=2, color="gray", ls="--", lw=2.5)

    ax.vlines(x=10, ymin=6, ymax=0, color="gray", ls="--", lw=2.5)

    B = (0, 2)
    A = (3, 6)
    C = (10, 0)
    ax.plot(*B, "ko", ms=10)
    ax.plot(*A, "ko", ms=10)
    ax.plot(*C, "ko", ms=10)

    ax.plot([B[0], A[0]], [B[1], A[1]], "k-", lw=2.5)
    ax.plot([A[0], C[0]], [A[1], C[1]], "k-", lw=2.5)

    fontsize = 20
    ax.text(
        A[0] - 0.3,
        A[1] + 0.3,
        r"$B$",
        fontsize=fontsize,
        ha="center",
        va="center",
    )

    ax.text(
        B[0] + 0.3,
        B[1] - 0.3,
        r"$A$",
        fontsize=fontsize,
        ha="center",
        va="center",
    )

    ax.text(
        C[0] - 0.4,
        C[1] - 0.3,
        r"$C$",
        fontsize=fontsize,
        ha="center",
        va="center",
    )

    plotmath.make_bar(xy=(0, 6.7), length=10, orientation="horizontal")
    ax.text(
        x=5,
        y=7,
        s="$10$",
        fontsize=fontsize,
        ha="center",
        va="center",
    )

    plotmath.make_bar(xy=(-0.35, 2), length=4, orientation="vertical")
    ax.text(
        x=-0.7,
        y=4,
        s="$4$",
        fontsize=fontsize,
        ha="center",
        va="center",
    )

    plotmath.make_bar(xy=(10.35, 0), length=6, orientation="vertical")
    ax.text(
        x=10.7,
        y=3,
        s="$6$",
        fontsize=fontsize,
        ha="center",
        va="center",
    )

    ax.axis("off")
    ax.axis("equal")

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
