import subprocess
import pystache
import yaml
import zopfli.gzip as gzip
from typing import BinaryIO, Optional
from io import BytesIO
from shutil import copyfile
from pathlib import Path
from tarfile import TarFile
from tempfile import TemporaryDirectory, mkstemp

from prepare_tool.core import FontInfo, FontWeightPaths
from prepare_tool.package_info import PackageInfo
from prepare_tool.generate import FontInfo, FontWeightPaths
from prepare_tool.generate.const import FILE_DIR


def generateArchive(font_weight_paths: FontWeightPaths, output_dir: Path, package_info: PackageInfo):
    with TemporaryDirectory() as tmp_dir_pathstr:  # type: str
        tmp_dir = Path(tmp_dir_pathstr)

        license_template_path: Path = FILE_DIR.LICENSE_TEMPLATE.joinpath(f"./{package_info.license.id}.txt")
        if not license_template_path.exists():
            raise Exception(f"{package_info.license.id} is invalid license id.")

        with open(license_template_path, 'r', encoding='utf-8') as license_read_io:
            license_text: str = pystache.render(license_read_io.read(), package_info)
        with open(tmp_dir.joinpath('LICENSE'), 'w', encoding='utf-8') as license_write_io:
            license_write_io.write(license_text)

        for weight, font_info in vars(font_weight_paths).items():  # type: str, FontInfo
            if font_info is None:
                continue
            ext = font_info.path.suffix
            copyfile(font_info.path, tmp_dir.joinpath(f"{package_info.id}-{weight}{ext}"))

        with BytesIO() as stream:  # type: BytesIO
            with TarFile.open(mode='w', fileobj=stream) as archive:
                for file_path in tmp_dir.glob('*'):  # type: Path
                    archive.add(str(file_path), arcname=file_path.name, recursive=False)
            archive_file: Path = output_dir.joinpath(f"./{package_info.id}.tar.gz")
            with open(archive_file, 'wb') as archive_io:  # type: BinaryIO
                archive_io.write(gzip.compress(stream.getvalue()))
