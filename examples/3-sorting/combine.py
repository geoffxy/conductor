import conductor.lib as cond
import pandas as pd


def main():
    deps = cond.get_deps_paths()
    out = cond.get_output_path()

    results = []

    for dep in deps:
        for exp in dep.iterdir():
            if not exp.is_dir() or exp.name.startswith("."):
                continue
            results.append(pd.read_csv(exp / "results.csv"))

    comb = pd.concat(results)
    comb = comb.sort_values(by=["method", "size"], ignore_index=True)
    comb.to_csv(out / "combined.csv", index=False)


if __name__ == "__main__":
    main()
