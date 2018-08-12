from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass()
class FontInfo():
    path: Path
    number: Optional[int] = None


@dataclass()
class FontWeightPaths():
    thin: Optional[FontInfo] = None
    extraLight: Optional[FontInfo] = None
    light: Optional[FontInfo] = None
    normal: Optional[FontInfo] = None
    medium: Optional[FontInfo] = None
    semiBold: Optional[FontInfo] = None
    bold: Optional[FontInfo] = None
    extraBold: Optional[FontInfo] = None
    black: Optional[FontInfo] = None
