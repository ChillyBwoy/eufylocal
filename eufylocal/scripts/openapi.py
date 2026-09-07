import argparse
import json
import sys

from uvicorn.importer import import_from_string

parser = argparse.ArgumentParser(prog="openapi.py")
parser.add_argument(
    "--app", help='App import string. Eg. "main:app"', default="api.main:app"
)
parser.add_argument("--app-dir", help="Directory containing the app", default="./")
parser.add_argument(
    "--out", help="Output file ending in .json or .yaml", default="openapi.json"
)

args = parser.parse_args()


def extract_openapi():
    """
    Extracts the OpenAPI specification from the specified app and writes it to a file.

    Raises:
        ImportError: If the specified app cannot be imported.
        KeyError: If the OpenAPI specification does not contain expected fields.
        ValueError: If the output file path does not end in `.json` or `.yaml`.
    """
    if args.app_dir is not None:
        sys.path.insert(0, args.app_dir)

    app = import_from_string(args.app)
    content = app.openapi()

    with open(args.out, "w") as f:
        json.dump(content, f, indent=2)


if __name__ == "__main__":
    extract_openapi()
