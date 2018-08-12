import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from prepare_tool.package_info import PackageInfo, ArchiveFileInfo, FontFileInfo
from prepare_tool.download import downloadFileFromUrl
from prepare_tool.extract import extractFilesFromArchive
from prepare_tool.generate import FontInfo, FontWeightPaths
from prepare_tool.generate.archive import generateArchive
from prepare_tool.generate.webfonts import generateWebFonts
from prepare_tool.generate.stylesheets import generateStyleSheets


@dataclass()
class Options():
    only_css: bool = False


@dataclass()
class DirPaths():
    tmp: Path
    output: Path
    fonts: Path
    webfonts: Path


class PrepareTool:
    def __init__(self, json_file: Path, output_dir: Path, options: dict) -> None:
        if (json_file.is_file() != True):
            raise FileNotFoundError(f"{json_file} is not found.")

        with open(json_file, 'r', encoding='utf-8') as file:
            json_dict = json.loads(file.read())
            del json_dict['$schema']
            self.package_info = PackageInfo(**json_dict)
        print(self.package_info)

        self.__tmp = TemporaryDirectory(prefix='typeface-')
        self.options = Options(**options)
        self.dir_paths = DirPaths(
            tmp=Path(self.__tmp.name),
            output=output_dir,
            fonts=output_dir.joinpath('./fonts'),
            webfonts=output_dir.joinpath(f"./webfonts/{self.package_info.id}"),
        )
        self.font_weight_paths = FontWeightPaths()

        for dir_path in vars(self.dir_paths).values():  # type: Path
            dir_path.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def cleanup(self):
        self.__tmp.cleanup()

    def downloadFonts(self):
        for archive_info in self.package_info.files:  # type: ArchiveFileInfo
            archive_file = downloadFileFromUrl(archive_info.url, self.dir_paths.tmp)
            extractFilesFromArchive(archive_file, self.dir_paths.tmp)

            for weight, file_info in vars(archive_info.fonts).items():  # type: str, FontFileInfo
                if file_info is None:
                    continue
                matched_filepath_list = list(self.dir_paths.tmp.glob(f"**/{file_info.name}"))
                if len(matched_filepath_list) == 0:
                    raise Exception(f"{file_info.name} is not found.")
                elif len(matched_filepath_list) != 1:
                    raise Exception(f"2 or more files with same name as {file_info.name} are found.")

                setattr(
                    self.font_weight_paths,
                    weight,
                    FontInfo(path=matched_filepath_list[0], number=file_info.number),
                )

    def generateArchive(self):
        generateArchive(self.font_weight_paths, output_dir=self.dir_paths.fonts, package_info=self.package_info)

    def generateWebFonts(self):
        generateWebFonts(self.font_weight_paths, output_dir=self.dir_paths.webfonts, package_info=self.package_info)

    def generateStyleSheets(self):
        is_fallback = self.package_info.fallback is not None
        generateStyleSheets(
            self.font_weight_paths,
            output_dir=self.dir_paths.webfonts,
            package_info=self.package_info,
            fallback=is_fallback,
        )
