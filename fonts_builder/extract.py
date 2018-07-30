from tarfile import TarFile
from zipfile import ZipFile
from pathlib import Path


def extractFile(file_path: Path, export_dir: Path):
    ext = file_path.suffixes

    if len(ext) == 1:
        if ext[-1] == ".zip":
            return extractZip(file_path, export_dir)
    elif len(ext) == 2:
        if ext[-1] == ".xz" and ext[-2] == ".tar":
            return extractTarXz(file_path, export_dir)

    raise Exception(f"{file_path} is unsupported archive file.")


def extractZip(file_path: Path, export_dir: Path):
    with ZipFile(file_path, mode='r') as archive:
        archive.extractall(export_dir)
    return


def extractTarXz(file_path: Path, export_dir: Path):
    with TarFile.open(file_path, mode='r:xz') as archive:
        archive.extractall(export_dir)
    return
