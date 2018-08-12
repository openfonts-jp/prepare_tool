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
    parser.add_argument('--only-css', dest='only_css', action='store_true')

    args = vars(parser.parse_args())
    return main(**args)


def main(json_path: Path, output_dir: Path, **options):
    with PrepareTool(json_path, output_dir, options) as prepare_tool:
        prepare_tool.downloadFonts()
        if options['only_css'] is not True:
            prepare_tool.generateArchive()
            prepare_tool.generateWebFonts()
        prepare_tool.generateStyleSheets()
