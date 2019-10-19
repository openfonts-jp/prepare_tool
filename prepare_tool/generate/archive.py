import pystache
import gzip
from tempfile import TemporaryDirectory
from pathlib import Path
from shutil import copyfile
from io import BytesIO
from tarfile import TarFile

from prepare_tool.core import Core
from prepare_tool.const import FILE_DIR


class ArchiveGenerator():
    def __init__(self, core: Core) -> None:
        self.__core = core

    def generate(self) -> None:
        package = self.__core.package
        output_dir = self.__core.directories.archives

        with TemporaryDirectory() as tmp_dir_pathstr:
            tmp_dir = Path(tmp_dir_pathstr)
            archive_file = output_dir.joinpath(f"./{package.id}.tar.gz")

            self.__generateLicenseFile(tmp_dir)
            self.__copyFontfile(tmp_dir)
            self.__archive(target_path=tmp_dir, output_path=archive_file)

    def __generateLicenseFile(self, dest_dir: Path) -> None:
        package = self.__core.package

        template_path = FILE_DIR.LICENSE_TEMPLATE.joinpath(f"./{package.license}.txt")
        if not template_path.exists():
            raise Exception(f"{package.license} is invalid license id.")

        with open(template_path, 'r', encoding='utf-8') as read_io:
            license_text: str = pystache.render(read_io.read(), package)
        with open(dest_dir.joinpath('LICENSE'), 'w', encoding='utf-8') as write_io:
            write_io.write(license_text)

    def __copyFontfile(self, dest_dir: Path) -> None:
        package = self.__core.package

        for source in package.sources:
            for weight, font in source.fonts:
                if font is None:
                    continue
                font_path = self.__core.findFontfilePath(font)
                copyfile(font_path, dest_dir.joinpath(font_path.name))

    def __archive(self, target_path: Path, output_path: Path) -> None:
        with BytesIO() as stream, TarFile.open(mode='w', fileobj=stream) as archive:
            for file_path in target_path.glob('*'):
                archive.add(str(file_path), arcname=file_path.name, recursive=False)

            with open(output_path, 'wb') as archive_io:
                archive_io.write(gzip.compress(stream.getvalue()))
