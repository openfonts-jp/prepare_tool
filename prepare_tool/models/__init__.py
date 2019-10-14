from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, AnyUrl


class License(str, Enum):
    MIT = 'MIT'
    IPA = 'IPA'
    OFL_1_1 = 'OFL-1.1'
    APACHE_2_0 = 'Apache-2.0'
    BSD_3_CLAUSE = 'BSD-3-Clause'
    MPLUS = 'Mplus'


class Font(BaseModel):
    filename: str
    sha256: str
    number: int = Field(0)


class FontWeight(BaseModel):
    thin: Optional[Font] = Field(None)
    extraLight: Optional[Font] = Field(None)
    light: Optional[Font] = Field(None)
    normal: Optional[Font] = Field(None)
    medium: Optional[Font] = Field(None)
    semiBold: Optional[Font] = Field(None)
    bold: Optional[Font] = Field(None)
    extraBold: Optional[Font] = Field(None)
    black: Optional[Font] = Field(None)


class Source(BaseModel):
    url: AnyUrl
    fonts: FontWeight


class Features(BaseModel):
    vert: Optional[bool] = Field(False)


class Category(str, Enum):
    MINCHO = 'Mincho'
    GOTHIC = 'Gothic'
    MARU_GOTHIC = 'MaruGothic'
    BRASH = 'Brash'
    HAND_WRITING = 'HandWriting'
    ARTISTIC = 'Artistic'
    OTHERS = 'Others'


class Character(str, Enum):
    ALPHABET = 'Alphabet'
    HIRAGANA = 'Hiragana'
    KATAKANA = 'Katakana'
    KANJI = 'Kanji'


class Package(BaseModel):
    '''
    OpenFonts.jp font package schema generated by pydantic.
    '''
    id: str = Field(..., regex='^[a-z][a-z-]*$')
    name: str
    version: str
    description: Optional[str]
    homepage: AnyUrl
    license: License
    authors: List[str] = Field(..., min_items=1)
    sources: List[Source] = Field(..., min_items=1)
    features: Features
    category: Category
    characters: List[Character] = Field(..., min_items=1)
    copyrights: List[str] = Field(..., min_items=1)

    class Config:
        schema_extra = {
            '$schema': 'https://json-schema.org/draft-07/schema',
        }
