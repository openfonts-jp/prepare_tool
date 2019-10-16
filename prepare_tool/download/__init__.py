import cgi
import requests
from pathlib import Path
from urllib.parse import urlparse
from tarfile import TarFile
from zipfile import ZipFile

from prepare_tool.core import Core
from prepare_tool.models import Package

ZIP_FILENAME_UTF8_FLAG = 0x800


class Downloader():
    def __init__(self, core: Core) -> None:
        self.__core = core

    def download(self) -> None:
        self.__fetch()

    def __fetch(self) -> None:
        package = self.__core.package
        tmp_dir = self.__core.directories.tmp

        for source in package.sources:
            res = requests.get(source.url, headers={'Referer': package.homepage})
            _, params = cgi.parse_header(res.headers.get('content-disposition', ''))
            file_name = params.get('filename', Path(urlparse(res.url).path).name)
            file_path = tmp_dir.joinpath(file_name)

            with open(file_path, 'wb') as file:
                file.write(res.content)

            if file_name.endswith('.tar.xz'):
                return self.__extractTarXz(file_path)
            elif file_name.endswith('.zip'):
                return self.__extractZip(file_path)
            elif file_name.endswith('.ttf') or file_name.endswith('.otf'):
                return None
            else:
                raise Exception(f"{file_name} is unsupported file.")

    def __extractZip(self, file_path: Path) -> None:
        tmp_dir = self.__core.directories.tmp
        with ZipFile(file_path, mode='r') as archive:
            for info in archive.filelist:
                if info.is_dir():
                    continue

                filename = info.filename
                if (info.flag_bits & ZIP_FILENAME_UTF8_FLAG) == 0:
                    # Redecode as cp932 (Shift-JIS)
                    filename = filename.encode('cp437').decode('cp932')

                export_filepath = tmp_dir.joinpath(filename)
                export_filepath.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as file, open(export_filepath, mode='wb') as export:
                    export.write(file.read())

    def __extractTarXz(self, file_path: Path) -> None:
        tmp_dir = self.__core.directories.tmp
        with TarFile.open(file_path, mode='r:xz') as archive:
            archive.extractall(tmp_dir)
