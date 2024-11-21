import argparse
from conductor.envs.maestro import ConductorMaestro


def main():
    """
    This is the main entry point for the Conductor Maestro daemon.
    """
    parser = argparse.ArgumentParser(description="Start the Conductor Maestro daemon.")
    parser.add_argument("--root", type=str, help="The root directory for the Maestro daemon.")
    args = parser.parse_args()

    maestro = ConductorMaestro(maestro_root=args.root)
    maestro.start()


if __name__ == "__main__":
    main()
