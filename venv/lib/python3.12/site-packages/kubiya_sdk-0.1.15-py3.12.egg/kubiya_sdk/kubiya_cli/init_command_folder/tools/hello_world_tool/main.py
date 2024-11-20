import argparse


def hello_world(name: str):
    print(f"Hello, {name}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print hello {name}!")
    parser.add_argument("name", help="Name to say hello to")

    # Parse command-line arguments
    args = parser.parse_args()

    # Get coordinates for the given city
    name = args.name

    hello_world(name)
