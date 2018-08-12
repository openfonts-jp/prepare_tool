from tarfile import TarFile
from zipfile import ZipFile
from pathlib import Path

ZIP_FILENAME_UTF8_FLAG = 0x800


def extractFilesFromArchive(archive_path: Path, export_dir: Path):
    archive_name = archive_path.name

    if archive_name.endswith('.tar.xz'):
        return extractFilesFromTarXz(archive_path, export_dir)
    elif archive_name.endswith('.zip'):
        return extractFilesFromZip(archive_path, export_dir)

    raise Exception(f"{archive_name} is unsupported archive file.")


def extractFilesFromZip(file_path: Path, export_dir: Path):
    with ZipFile(file_path, mode='r') as archive:
        for info in archive.filelist:
            if info.is_dir():  # type: ignore
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


def extractFilesFromTarXz(file_path: Path, export_dir: Path):
    with TarFile.open(file_path, mode='r:xz') as archive:
        archive.extractall(export_dir)
    return
