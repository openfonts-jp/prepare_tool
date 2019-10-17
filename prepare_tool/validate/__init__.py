import hashlib

from prepare_tool.core import Core
from prepare_tool.models import Font


class Validator():
    def __init__(self, core: Core):
        self.__core = core

    def validate(self) -> bool:
        package = self.__core.package

        for source in package.sources:
            weight: str
            font: Font
            for weight, font in source.fonts:
                if font is None:
                    continue
                self.__validateFont(font)

        return True

    def __validateFont(self, font: Font) -> None:
        font_path = self.__core.findFontfilePath(font)
        with open(font_path, 'rb') as fd:
            hash_hex = hashlib.sha256(fd.read()).hexdigest()
        if font.sha256 != hash_hex:
            raise Exception(f'SHA256 of "{font_path.name}" is not matched.')
