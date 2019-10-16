import json
from typing import List
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from prepare_tool.models import Package, Font


@dataclass()
class Directories():
    tmp: Path
    output: Path
    archives: Path
    webfonts: Path


class Core:
    def __init__(self, json_file: Path, output_dir: Path) -> None:
        if (json_file.is_file() != True):
            raise FileNotFoundError(f"{json_file} is not found.")

        with open(json_file, 'r', encoding='utf-8') as file:
            json_dict = json.loads(file.read())
            self.package = Package(**json_dict)

        self.__tmp_directory = TemporaryDirectory(prefix='openfontsjp-')
        self.directories = Directories(
            tmp=Path(self.__tmp_directory.name),
            output=output_dir,
            archives=output_dir.joinpath('./archives'),
            webfonts=output_dir.joinpath(f"./webfonts/{self.package.id}"),
        )

        for dir_path in vars(self.directories).values():  # type: Path
            dir_path.mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cleanup()

    def cleanup(self) -> None:
        self.__tmp_directory.cleanup()

    def findFontfilePath(self, font: Font) -> Path:
        matched: List[Path] = list(self.directories.tmp.glob(f"**/{font.filename}"))
        if len(matched) == 0:
            raise Exception(f"{font.filename} is not found.")
        elif len(matched) != 1:
            raise Exception(f"2 or more files with same name as {font.filename} are found.")
        return matched[0]
