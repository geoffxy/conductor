import conductor.lib as cond
from conductor.config import TASK_OUTPUT_DIR_SUFFIX


def main():
    output_dir = cond.get_output_path()
    assert output_dir.exists()
    assert output_dir.name == "output_path" + TASK_OUTPUT_DIR_SUFFIX


if __name__ == "__main__":
    main()
