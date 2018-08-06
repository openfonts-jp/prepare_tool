import sys
import json
from logzero import logger
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from .download import downloadFile
from .extract import extractFile
from .generate import saveFonts, saveSubsettedFont, generateCss, saveCss


def cli():
    parser = argparse.ArgumentParser(prog='prepare_tool')
    parser.add_argument('json_file', metavar='json_file', type=Path, help='JSON file')
    parser.add_argument('--output-dir', dest='output_dir', type=Path, required=True, help='Output directory')

    args = vars(parser.parse_args())
    return main(**args)


def main(json_file: Path, output_dir: Path):
    if (json_file.is_file() != True):
        logger.error(f"{json_file} is not found.")
        sys.exit(1)

    with open(json_file, 'r', encoding='utf-8') as file:
        font_info = json.loads(file.read())

    with TemporaryDirectory(prefix='typeface-') as tmp_dir_pathstr:
        download_dir = Path(tmp_dir_pathstr)
        fonts_dir = output_dir.joinpath('./fonts')
        subset_dir = output_dir.joinpath(f"./webfonts/{font_info['id']}")

        output_dir.mkdir(parents=True, exist_ok=True)
        download_dir.mkdir(parents=True, exist_ok=True)
        fonts_dir.mkdir(parents=True, exist_ok=True)
        subset_dir.mkdir(parents=True, exist_ok=True)

        font_fileinfo_dict = dict()
        for file_info in font_info['files']:
            logger.info(f"Downloading from {file_info['from']}")
            archive_file = downloadFile(file_info['from'], download_dir)
            logger.info(f"Extracting files")
            extractFile(archive_file, download_dir)

            for weight, font_fileinfo in file_info['fonts'].items():
                if font_fileinfo is None:
                    continue
                if not isinstance(font_fileinfo, dict):
                    font_fileinfo = dict(name=font_fileinfo)
                matched_filepath_list = list(download_dir.glob(f"**/{font_fileinfo['name']}"))
                if len(matched_filepath_list) == 0:
                    raise Exception(f"{font_fileinfo['name']} is not found.")
                elif len(matched_filepath_list) != 1:
                    raise Exception(f"2 or more files with same name as {font_fileinfo['name']} are found.")

                if 'number' in font_fileinfo:
                    font_fileinfo_dict[weight] = dict(path=matched_filepath_list[0], number=font_fileinfo['number'])
                else:
                    font_fileinfo_dict[weight] = dict(path=matched_filepath_list[0])

        logger.info(f"Packing files")
        saveFonts(font_fileinfo_dict, fonts_dir, info=font_info)

        css = ''
        fallbackCss = ''
        for weight, font_fileinfo in font_fileinfo_dict.items():
            logger.info(f"Creating subset fonts (weight: {weight})")
            saveSubsettedFont(font_fileinfo, subset_dir, weight=weight, info=font_info)
            css += generateCss(
                font_info['name'],
                font_fileinfo,
                weight=weight,
                info=font_info,
            )
            if 'fallback' in font_info:
                fallbackCss += generateCss(
                    font_info['name'],
                    font_fileinfo,
                    weight=weight,
                    info=font_info,
                    fallback=font_info['fallback'],
                )

        logger.info(f"Creating CSS")
        saveCss(subset_dir, css, 'style')
        if 'fallback' in font_info:
            saveCss(subset_dir, fallbackCss, 'style.fallback')
