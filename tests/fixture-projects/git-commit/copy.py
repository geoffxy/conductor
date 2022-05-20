import shutil
import conductor.lib as cond


def main():
    out = cond.get_output_path()
    deps = cond.get_deps_paths()
    for dep_path in deps:
        task_name = dep_path.name.split(".")[0]
        shutil.copy2(dep_path / "out.txt", out / "{}.txt".format(task_name))


if __name__ == "__main__":
    main()
