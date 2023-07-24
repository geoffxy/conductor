import pathlib
import conductor.lib as cond


def main():
    my_file = pathlib.Path("./test.csv")
    file_in_output_dir = cond.in_output_dir(my_file)
    assert file_in_output_dir != my_file

    output_dir = cond.get_output_path()
    assert file_in_output_dir.is_relative_to(output_dir)


if __name__ == "__main__":
    main()
