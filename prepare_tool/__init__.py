import sys
import json
from logzero import logger
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from prepare_tool.core import PrepareTool


def cli():
    parser = argparse.ArgumentParser(prog='prepare_tool')
    parser.add_argument('json_path', metavar='json_file', type=Path, help='JSON file')
    parser.add_argument('--output-dir', dest='output_dir', type=Path, required=True, help='Output directory')
    parser.add_argument('--no-generate-archive', dest='generate_archive', action='store_false')
    parser.add_argument('--no-generate-webfonts', dest='generate_webfonts', action='store_false')
    parser.add_argument('--no-generate-css', dest='generate_css', action='store_false')

    args = vars(parser.parse_args())
    return main(**args)


def main(json_path: Path, output_dir: Path, **options):
    with PrepareTool(json_path, output_dir) as prepare_tool:
        prepare_tool.downloadFonts()
        if options['generate_archive'] is True:
            prepare_tool.generateArchive()
        if options['generate_webfonts'] is True:
            prepare_tool.generateWebFonts()
        if options['generate_css'] is True:
            prepare_tool.generateStyleSheets()
