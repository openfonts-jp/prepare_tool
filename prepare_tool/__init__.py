import sys
import yaml
import logging
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from .download import downloadFile
from .extract import extractFile
from .generate import saveFonts, saveSubsettedFont, generateCss, saveCss

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


def main():
    parser = argparse.ArgumentParser(prog='prepare_tool')
    parser.add_argument('yaml_file', metavar='yaml_file', type=Path, help='YAML file')
    parser.add_argument('--output-dir', dest='output_dir', type=Path, required=True, help='Output directory')

    args = vars(parser.parse_args())
    yaml_file = args['yaml_file']
    output_dir = args['output_dir']

    if (yaml_file.is_file() != True):
        logger.error(f"{yaml_file} is not found.")
        sys.exit(1)

    with open(yaml_file, 'r', encoding='utf-8') as file:
        font_info = yaml.load(file.read())

    with TemporaryDirectory(prefix='typeface-') as tmp_dir_pathstr:
        download_dir = Path(tmp_dir_pathstr)
        fonts_dir = output_dir.joinpath('./fonts')
        subset_dir = output_dir.joinpath(f"./webfonts/{font_info['id']}")

        output_dir.mkdir(parents=True, exist_ok=True)
        download_dir.mkdir(parents=True, exist_ok=True)
        fonts_dir.mkdir(parents=True, exist_ok=True)
        subset_dir.mkdir(parents=True, exist_ok=True)

        font_filepath_dict = dict()
        for file_info in font_info['files']:
            archive_file = downloadFile(file_info['from'], download_dir)
            extractFile(archive_file, download_dir)

            for weight, font_filename in file_info['fonts'].items():
                if font_filename is None:
                    continue
                matched_filepath_list = list(download_dir.glob(f"**/{font_filename}"))
                if len(matched_filepath_list) == 0:
                    raise Exception(f"{font_filename} is not found.")
                elif len(matched_filepath_list) != 1:
                    raise Exception(f"2 or more files with same name as {font_filename} are found.")
                font_filepath_dict[weight] = matched_filepath_list[0]

        saveFonts(font_filepath_dict, fonts_dir, info=font_info)

        css = ''
        fallbackCss = ''
        for weight, font_filepath in font_filepath_dict.items():
            saveSubsettedFont(font_filepath, subset_dir, weight=weight, info=font_info)
            css += generateCss(
                font_info['name'],
                font_filepath,
                weight=weight,
                info=font_info,
            )
            if 'fallback' in font_info:
                fallbackCss += generateCss(
                    font_info['name'],
                    font_filepath,
                    weight=weight,
                    info=font_info,
                    fallback=font_info['fallback'],
                )

        saveCss(subset_dir, css, 'style')
        if 'fallback' in font_info:
            saveCss(subset_dir, fallbackCss, 'style.fallback')
