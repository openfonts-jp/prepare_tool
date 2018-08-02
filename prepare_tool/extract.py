from tarfile import TarFile
from zipfile import ZipFile
from pathlib import Path

ZIP_FILENAME_UTF8_FLAG = 0x800


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
        for info in archive.filelist:
            if info.is_dir():
                continue

            filename = info.filename
            if info.flag_bits & ZIP_FILENAME_UTF8_FLAG == 0:
                # Redecode as cp932 (Shift-JIS)
                filename = filename.encode('cp437').decode('cp932')

            export_filepath = export_dir.joinpath(filename)
            export_filepath.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as file, open(export_filepath, mode='wb') as export:
                export.write(file.read())
    return


def extractTarXz(file_path: Path, export_dir: Path):
    with TarFile.open(file_path, mode='r:xz') as archive:
        archive.extractall(export_dir)
    return
