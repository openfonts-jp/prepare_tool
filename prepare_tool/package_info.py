from dataclasses import dataclass, fields
from typing import Optional, List


@dataclass
class LicenseInfo():
    id: str


@dataclass
class FontFileInfo():
    name: str
    number: Optional[int] = None


@dataclass
class FontWeightInfo():
    thin: Optional[FontFileInfo] = None
    extraLight: Optional[FontFileInfo] = None
    light: Optional[FontFileInfo] = None
    normal: Optional[FontFileInfo] = None
    medium: Optional[FontFileInfo] = None
    semiBold: Optional[FontFileInfo] = None
    bold: Optional[FontFileInfo] = None
    extraBold: Optional[FontFileInfo] = None
    black: Optional[FontFileInfo] = None

    def __post_init__(self):
        for propName, value in vars(self).items():
            if value is not None:
                setattr(self, propName, FontFileInfo(**value))


@dataclass
class ArchiveFileInfo():
    url: str
    fonts: FontWeightInfo

    def __post_init__(self):
        self.fonts = FontWeightInfo(**self.fonts)  # pylint: disable=not-a-mapping


@dataclass
class PackageInfo():
    id: str
    name: str
    version: str
    categories: List[str]
    characters: List[str]
    owners: List[str]
    files: List[ArchiveFileInfo]
    license: LicenseInfo
    copyrights: List[str]
    website: str
    fallback: Optional[str] = None

    def __post_init__(self):
        self.files = list(map(lambda args: ArchiveFileInfo(**args), self.files))
        self.license = LicenseInfo(**self.license)  # pylint: disable=not-a-mapping
