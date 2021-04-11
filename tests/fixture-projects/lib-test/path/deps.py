import conductor.lib as cond
from conductor.config import TASK_OUTPUT_DIR_SUFFIX


def main():
    expected_deps = {"one" + TASK_OUTPUT_DIR_SUFFIX, "two" + TASK_OUTPUT_DIR_SUFFIX}
    deps = cond.get_deps_paths()
    assert len(deps) > 0
    for dep_path in deps:
        assert dep_path.name in expected_deps


if __name__ == "__main__":
    main()
