import os
import pathlib
import conductor.lib as cond


def main():
    my_file = pathlib.Path("./test.csv")
    file_in_output_dir = cond.in_output_dir(my_file)
    assert file_in_output_dir != my_file

    output_dir = cond.get_output_path()
    # Or use pathlib.Path.is_relative_to() on Python 3.9+.
    assert os.path.commonpath([file_in_output_dir, output_dir]) == str(output_dir)


if __name__ == "__main__":
    main()
