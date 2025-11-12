import plotmath


def main(dirname, save):
    #
    # Define functions
    def f(x):
        return 8 / (x**2 + 4)

    # List of functions and their labels.
    functions = [f]

    fig, ax = plotmath.plot(
        functions=functions,
        fn_labels=True,
        xmin=-1,
        xmax=9,
        ymin=-0.1,
        ymax=2.2,
        ticks=False,
        xstep=1,
        ystep=1,
        grid=True,
        lw=2.5,
        alpha=None,
        domain=(0, 50),
        fontsize=20,
        figsize=None,
    )

    k = 3
    A = (0, 0)
    B = (k, 0)
    C = (k, f(k))
    D = (0, f(k))

    plotmath.plot_polygon(A, B, C, D)

    ax.plot(*A, "ko", ms=8)
    ax.plot(*B, "ko", ms=8)
    ax.plot(*C, "ko", ms=8)
    ax.plot(*D, "ko", ms=8)

    ax.text(
        x=C[0] + 0.2,
        y=C[1] + 0.02,
        s="$(k, f(k))$",
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
