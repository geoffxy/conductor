import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import conductor.lib as cond


def main():
    res = cond.get_deps_paths()[0]
    out = cond.get_output_path()

    df = pd.read_csv(res / "combined.csv")

    fig, ax = plt.subplots()

    isort = df[df["method"] == "isort"]
    msort = df[df["method"] == "msort"]

    xpos = np.arange(len(isort))
    width = 0.3

    ax.bar(xpos - width / 2, isort["run_time_ms"], label="Insertion Sort", width=width)
    ax.bar(xpos + width / 2, msort["run_time_ms"], label="Merge Sort", width=width)

    ax.set_xticks(xpos)
    ax.set_xticklabels(isort["size"])
    ax.legend(edgecolor="#000", fancybox=False)
    ax.set_xlabel("Array Size")
    ax.set_ylabel("Run Time (ms)")

    fig.savefig(out / "compare.pdf")


if __name__ == "__main__":
    main()
