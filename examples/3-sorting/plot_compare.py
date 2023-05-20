import matplotlib.pyplot as plt
import pandas as pd
import conductor.lib as cond


def main():
    res = cond.get_deps_paths()[0]
    out = cond.get_output_path()

    df = pd.read_csv(res / "combined.csv")

    fig, ax = plt.subplots()

    isort = df[df["method"] == "isort"]
    msort = df[df["method"] == "msort"]

    linewidth = 1.5
    ax.plot(isort["size"], isort["run_time_ms"], marker="o", label="Insertion Sort", linewidth=linewidth)
    ax.plot(msort["size"], msort["run_time_ms"], marker="o", label="Merge Sort", linewidth=linewidth)

    ax.legend(edgecolor="#000", fancybox=False)
    ax.set_xlabel("Array Size")
    ax.set_ylabel("Run Time (ms)")

    fig.savefig(out / "compare.pdf")


if __name__ == "__main__":
    main()
