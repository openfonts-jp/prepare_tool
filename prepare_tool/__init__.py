import sys
import json
from logzero import logger
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from prepare_tool.core import PrepareTool
from prepare_tool.models import Package


def cli():
    parser = argparse.ArgumentParser(prog='prepare_tool', add_help=False)
    parser.add_argument('--help', action='help')

    subparsers = parser.add_subparsers(dest='command', metavar='command')

    schema_command_parser = subparsers.add_parser('schema', help='Print OpenFonts.jp package JSON schema.')

    generate_command_parser = subparsers.add_parser('generate', help='Generate webfonts.')
    generate_command_parser.add_argument('json_path', metavar='json_file', type=Path, help='JSON file')
    generate_command_parser.add_argument(
        '--output-dir', dest='output_dir', type=Path, required=True, help='Output directory'
    )
    generate_command_parser.add_argument('--no-generate-archive', dest='generate_archive', action='store_false')
    generate_command_parser.add_argument('--no-generate-webfonts', dest='generate_webfonts', action='store_false')
    generate_command_parser.add_argument('--no-generate-css', dest='generate_css', action='store_false')

    args = vars(parser.parse_args())
    return main(parser=parser, **args)


def print_schema():
    print(Package.schema_json(indent=2, sort_keys=True))


def generate(json_path: Path, output_dir: Path, **options):
    with PrepareTool(json_path, output_dir) as prepare_tool:
        prepare_tool.downloadFonts()
        if options['generate_archive'] is True:
            prepare_tool.generateArchive()
        if options['generate_webfonts'] is True:
            prepare_tool.generateWebFonts()
        if options['generate_css'] is True:
            prepare_tool.generateStyleSheets()


def main(parser: argparse.ArgumentParser, command: str, **args):
    if command == 'schema':
        print_schema()
    elif command == 'generate':
        generate(**args)
    else:
        parser.print_help()
