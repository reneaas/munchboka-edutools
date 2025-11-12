import matplotlib.pyplot as plt
import plotmath

plt.rc("text", usetex=True)


def main(dirname, save):

    L = 12
    x = 5
    A = (0, 8)
    B = (x, 0)
    D = (L, 0)
    C = (L, -1)

    plt.plot(*D, "ko", markersize=8, alpha=0.7)
    plt.text(
        x=D[0],
        y=D[-1] - 0.5,
        s="Hytte",
        fontsize=16,
        ha="center",
        va="top",
    )
    plt.text(
        x=0 - 1,
        y=0.5 * A[-1],
        s="$8 \\, \\mathrm{km}$",
        fontsize=16,
        ha="right",
        va="center",
    )

    plt.plot(*A, "ko", markersize=8, alpha=0.7)
    plt.text(
        x=A[0],
        y=A[-1] + 0.5,
        s="Holme",
        fontsize=16,
        ha="center",
        va="bottom",
    )
    plt.plot([A[0], B[0]], [A[1], B[1]], color=plotmath.COLORS.get("blue"), lw=2)

    plt.text(
        x=0.5 * (A[0] + B[0]),
        y=0.5 * (A[-1] + B[-1]),
        s="Robåt",
        fontsize=16,
        ha="left",
        va="bottom",
        color="blue",
    )

    plt.annotate(
        "",
        xy=(A[0] - 0.8, 0),
        xycoords="data",
        xytext=(A[0] - 0.8, A[-1]),
        textcoords="data",
        arrowprops=dict(arrowstyle="|-|,widthA=0.5,widthB=0.5", color="black"),
    )

    plt.hlines(y=0, xmin=-20, xmax=20, color="black")

    plt.hlines(y=0, xmin=x, xmax=L, color=plotmath.COLORS.get("red"), lw=2)
    plt.text(
        x=0.5 * (x + L),
        y=-0.5,
        s="Til fots",
        fontsize=16,
        ha="center",
        va="top",
        color="red",
    )

    plt.text(
        x=0.5 * B[0],
        y=-0.2,
        s="$x$",
        fontsize=16,
        ha="center",
        va="top",
    )

    plt.annotate(
        "",
        xy=(0 - 0.02, -0.3),
        xycoords="data",
        xytext=(x + 0.02, -0.3),
        textcoords="data",
        arrowprops=dict(arrowstyle="|-|,widthA=0.5,widthB=0.5", color="black"),
    )

    plt.vlines(x=0, ymin=0, ymax=A[-1], linestyle="--", color="black")

    plt.annotate(
        "",
        xy=(0 - 0.02, -1.2),
        xycoords="data",
        xytext=(L + 0.02, -1.2),
        textcoords="data",
        arrowprops=dict(arrowstyle="|-|,widthA=0.5,widthB=0.5", color="black"),
    )

    plt.text(
        x=0.5 * L,
        y=-1.6,
        s="$12 \\, \\mathrm{km}$",
        fontsize=16,
        ha="center",
        va="center",
    )

    plt.ylim(-2, 1.5)

    plt.axis("off")
    plt.axis("equal")
    plt.xlim(-1, L + 1)

    # NOTE: Select an appropriate `dirname` to save the figure.
    # The directory `dirname` will be created automatically if it does not exist already.
    if save:
        fname = __file__.split("/")[-1].replace(".py", ".svg")
        plotmath.savefig(
            dirname=dirname,
            fname=fname,
        )

    if not save:

        plt.show()


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
