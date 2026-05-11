import json
import pathlib
import os
import sys
import re
import difflib
import colorama
import typing

from ansible_collections.nhsd.apigee.plugins.module_utils.models.manifest import meta
from ansible_collections.nhsd.apigee.plugins.module_utils.models.manifest.manifest import (
    Manifest,
)

SCHEMA_VERSION_REGEX = re.compile(r"^([1-9][0-9]*)\.([0-9]+)\.([0-9]+)$")


class SchemaString:

    def __init__(self, schema_or_major: typing.Union[str, int], minor=None, patch=None):

        if isinstance(schema_or_major, str):
            schema_version = schema_or_major
            match = re.match(SCHEMA_VERSION_REGEX, schema_version)
            if not match:
                raise ValueError(f"Invalid SchemaString {schema_version}")
            self.major, self.minor, self.patch = [
                int(match.group(x)) for x in range(1, 4)
            ]
        elif isinstance(schema_or_major, int):
            if not isinstance(minor, int) and isinstance(patch, int):
                raise ValueError("SchemaString.__init__ requires major, minor, patch")
            self.major = schema_or_major
            self.minor = minor
            self.patch = patch
        else:
            raise TypeError("Invalid arguments to SchemaString.__init__")

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other):
        return (
            self.major == other.major
            and self.minor == other.minor
            and self.patch == other.patch
        )

    def __lt__(self, other):
        return (
            self.major < other.major
            or (self.major == other.major and self.minor < other.minor)
            or (
                self.major == other.major
                and self.minor == other.minor
                and self.patch < other.patch
            )
        )

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        return not self <= other

    def __ge__(self, other):
        return not self < other

    def valid_increments(self):
        return [
            SchemaString(self.major + 1, 0, 0),
            SchemaString(self.major, self.minor + 1, 0),
            SchemaString(self.major, self.minor, self.patch + 1),
        ]


def main():
    """ """
    UPDATED_SCHEMA_VERSION = SchemaString(meta.SCHEMA_VERSION)

    script_dir = pathlib.Path(__file__).parent
    relative_schema_dir = script_dir.joinpath(
        "../tests/unit/plugins/module_utils/models/manifest/schema_versions/"
    )

    schema_dir_glob = relative_schema_dir.glob("v*.json")

    SCHEMA_VERSION = SchemaString("1.0.0")
    SCHEMA_FILE_NAME_PATTERN = re.compile(r"v([1-9][0-9]*\.[0-9]+\.[0-9]+)\.json$")
    for schema_file in schema_dir_glob:
        match = re.match(SCHEMA_FILE_NAME_PATTERN, schema_file.name)
        schema_version = SchemaString(match.group(1))

        if schema_version >= SCHEMA_VERSION:
            SCHEMA_VERSION = schema_version

    new_schema = Manifest.schema_json(indent=2)
    with open(relative_schema_dir.joinpath(f"v{SCHEMA_VERSION}.json")) as f:
        last_schema_ = json.loads(f.read())
        last_schema = json.dumps(last_schema_, indent=2)

    deltas = difflib.unified_diff(
        last_schema.split("\n"),
        new_schema.split("\n"),
        fromfile=str(SCHEMA_VERSION),
        tofile=str(UPDATED_SCHEMA_VERSION),
    )
    deltas = [delta for delta in deltas]

    if not deltas:
        raise ValueError(
            f"No difference between proposed {UPDATED_SCHEMA_VERSION} schema and current {meta.SCHEMA_VERSION}"
        )

    if UPDATED_SCHEMA_VERSION not in SCHEMA_VERSION.valid_increments():
        raise ValueError(
            f"""{UPDATED_SCHEMA_VERSION} is invalid increment after current {SCHEMA_VERSION}.
Please increment major, minor or patch integer, e.g:
"""
            + "\n".join(str(x) for x in SCHEMA_VERSION.valid_increments())
        )

    print("-" * 50)
    for delta in deltas:
        if delta.startswith("+"):
            col = colorama.Fore.GREEN
        elif delta.startswith("-"):
            col = colorama.Fore.RED
        else:
            col = ""
        print(col + delta, end="")
        print(colorama.Fore.RESET)

    _input = None
    print("-" * 50)
    print("Confirm spec changes? ", end="")
    while _input not in ["y", "n"]:
        if _input is not None:
            print("Please enter y or n. ", end="")
        print("(y/n): ", end="")
        _input = input().lower()

    if _input != "y":
        print("Did not update schema.")
        return

    new_schema_file_name = f"v{UPDATED_SCHEMA_VERSION}.json"
    new_schema_file = os.path.join(relative_schema_dir, new_schema_file_name)

    with open(new_schema_file, "w") as f:
        f.write(new_schema)
    print(f"""Wrote {new_schema_file}"
Validate this file by executing
$ make test
in {script_dir.parent}""")


if __name__ == "__main__":

    try:
        main()
    except ValueError as e:
        print(f"Error! {e}", file=sys.stderr)
        sys.exit(2)
