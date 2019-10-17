import sys
import json
import argparse
from logzero import logger
from pathlib import Path
from tempfile import TemporaryDirectory

from prepare_tool.core import Core
from prepare_tool.models import Package
from prepare_tool.download import Downloader
from prepare_tool.validate import Validator
from prepare_tool.generate import ArchiveGenerator, StyleSheetGenerator, WebFontGenerator


def cli():
    parser = argparse.ArgumentParser(prog='prepare_tool', add_help=False)
    parser.add_argument('--help', action='help')

    subparsers = parser.add_subparsers(dest='command', metavar='command')

    schema_command_parser = subparsers.add_parser('schema', help='Print OpenFonts.jp package JSON schema.')

    validate_command_parser = subparsers.add_parser('validate', help='Validate hashes of font.')
    validate_command_parser.add_argument('json_path', metavar='json_file', type=Path, help='JSON file')

    generate_command_parser = subparsers.add_parser('generate', help='Generate webfonts.')
    generate_command_parser.add_argument('json_path', metavar='json_file', type=Path, help='JSON file')
    generate_command_parser.add_argument('--output-dir', dest='output_dir', type=Path, required=True)
    generate_command_parser.add_argument('--no-generate-archive', dest='generate_archive', action='store_false')
    generate_command_parser.add_argument('--no-generate-webfonts', dest='generate_webfonts', action='store_false')
    generate_command_parser.add_argument('--no-generate-css', dest='generate_css', action='store_false')

    args = vars(parser.parse_args())
    return main(parser=parser, **args)


def print_schema():
    print(Package.schema_json(indent=2, sort_keys=True))


def generate(json_path: Path, output_dir: Path, **options):
    with Core(json_path, output_dir) as prepare_tool:
        Downloader(prepare_tool).download()
        Validator(prepare_tool).validate()

        if options['generate_archive'] is True:
            ArchiveGenerator(prepare_tool).generate()
        if options['generate_webfonts'] is True:
            WebFontGenerator(prepare_tool).generate()
        if options['generate_css'] is True:
            StyleSheetGenerator(prepare_tool).generate()


def validate(json_path: Path):
    with Core(json_path, output_dir=Path()) as prepare_tool:
        Downloader(prepare_tool).download()
        Validator(prepare_tool).validate()


def main(parser: argparse.ArgumentParser, command: str, **args):
    if command == 'schema':
        print_schema()
    elif command == 'generate':
        generate(**args)
    elif command == 'validate':
        validate(**args)
    else:
        parser.print_help()
