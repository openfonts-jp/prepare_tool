from dataclasses import dataclass
from pathlib import Path

ROOT_DIR_PATH = Path(__file__).parent.resolve()


@dataclass(init=False, frozen=True)
class __NameId():
    COPYRIGHT = 0
    LEGACY_FAMILY = 1
    LEGACY_SUBFAMILY = 2
    TRUETYPE_UNIQUE_ID = 3
    FULL_NAME = 4
    POSTSCRIPT_NAME = 6
    PREFERRED_FAMILY = 16
    PREFERRED_SUBFAMILY = 17
    WWS_FAMILY = 21


@dataclass(init=False, frozen=True)
class __WeightNumber():
    thin = '100'
    extraLight = '200'
    light = '300'
    normal = '400'
    medium = '500'
    semiBold = '600'
    bold = '700'
    extraBold = '800'
    black = '900'


@dataclass(init=False, frozen=True)
class __FileDir():
    UNICODE_TEXT: Path = ROOT_DIR_PATH.joinpath('./groups')
    LICENSE_TEMPLATE: Path = ROOT_DIR_PATH.joinpath('./templates/licenses')
    METADATA_TEMPLATE: Path = ROOT_DIR_PATH.joinpath('./templates/metadata')
    STYLESHEETS_TEMPLATE: Path = ROOT_DIR_PATH.joinpath('./templates/stylesheets')


NAME_ID = __NameId()
WEIGHT_NUMBER = __WeightNumber()
FILE_DIR = __FileDir()

FAMILY_RELATED_NAME_ID = [
    NAME_ID.LEGACY_FAMILY,
    NAME_ID.TRUETYPE_UNIQUE_ID,
    NAME_ID.FULL_NAME,
    NAME_ID.POSTSCRIPT_NAME,
    NAME_ID.PREFERRED_FAMILY,
    NAME_ID.WWS_FAMILY,
]
