import subprocess
import pystache
import yaml
from typing import List
from pathlib import Path
from tempfile import mkstemp
from xml.etree.ElementTree import Element, SubElement, tostring as toXMLString
from faker import Faker
from fontTools.subset import Options, Subsetter, load_font, save_font, parse_unicodes
from fontTools.ttLib import TTFont
from fontTools.ttLib.sfnt import WOFFFlavorData
from fontTools.ttLib.woff2 import WOFF2FlavorData

from prepare_tool.core import FontInfo, FontWeightPaths
from prepare_tool.package_info import PackageInfo
from prepare_tool.generate import FontInfo, FontWeightPaths
from prepare_tool.generate.const import FILE_DIR, NAME_ID, WEIGHT_NUMBER


def generateWebFonts(font_weight_paths: FontWeightPaths, output_dir: Path, package_info: PackageInfo):
    for weight, font_info in vars(font_weight_paths).items():  # type: str, FontInfo
        if font_info is None:
            continue
        __generateWebFontsForWeight(
            font_info=font_info,
            weight=weight,
            output_dir=output_dir.joinpath(f"./{package_info.version}/{weight}"),
            package_info=package_info,
        )


def __generateWebFontsForWeight(font_info: FontInfo, weight: str, output_dir: Path, package_info: PackageInfo):
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata: bytes = __generateMetadata(package_info).encode('utf-8')

    fake = Faker()
    fake.seed(package_info.id)
    subset_fontname: str = fake.slug()  # pylint: disable=no-member

    options = Options()
    options.desubroutinize = True
    options.layout_features = ['*']
    options.obfuscate_names = True

    tmp_otf_path = None
    if not str(font_info).endswith('.otf'):
        tmp_otf_path = __generateOpenTypeFont(font_info)

    for unicodes_file in FILE_DIR.UNICODE_TEXT.glob('./**/*.txt'):  # type: Path
        idx = unicodes_file.stem
        unicodes: List[str] = []
        with open(unicodes_file, 'r') as unicode_read_io:
            for line in unicode_read_io.readlines():
                unicodes.extend(parse_unicodes(line.split('#')[0]))

        with load_font(tmp_otf_path or font_info.path, options) as font:
            subsetter = Subsetter(options=options)
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(font)

            for record in font['name'].names:
                if record.nameID == NAME_ID.COPYRIGHT:
                    record.string = '\n'.join(package_info.copyrights)
                elif record.nameID in vars(NAME_ID).values():
                    record.string = subset_fontname

            woff_file = output_dir.joinpath(f"{idx}.woff")
            with open(woff_file, 'wb') as woff_write_io:
                options.flavor = 'woff'
                font.flavorData = WOFFFlavorData()
                font.flavorData.metaData = metadata
                save_font(font, woff_write_io, options)

            woff2_file = output_dir.joinpath(f"{idx}.woff2")
            with open(woff2_file, 'wb') as woff2_write_io:
                options.flavor = 'woff2'
                font.flavorData = WOFF2FlavorData()
                font.flavorData.metaData = metadata
                save_font(font, woff2_write_io, options)

    if tmp_otf_path is not None:
        tmp_otf_path.unlink()


def __generateOpenTypeFont(font_info: FontInfo) -> Path:
    font_path = font_info.path
    number = font_info.number
    if number is None:
        number = 0

    tmp_file = Path(mkstemp(suffix='.otf')[1])
    subprocess.run(
        [
            'fontforge',
            '-lang=ff',
            '-c',
            'Open($1);Generate($2);',
            f"{font_path}({number})",
            tmp_file,
        ],
        check=True,
    )

    # Fix vmtx (fontforge calcs wrong vmtx tbs)
    with TTFont(tmp_file) as font:
        if 'vmtx' in font:
            sTypoAscender = font['OS/2'].sTypoAscender
            for glyphName in font['vmtx'].metrics.keys():
                font['vmtx'].metrics[glyphName] = (
                    font['vmtx'].metrics[glyphName][0],
                    sTypoAscender - font['vmtx'].metrics[glyphName][1],
                )
            font.save(tmp_file)

    return tmp_file


def __generateMetadata(package_info: PackageInfo) -> str:
    yaml_path = FILE_DIR.METADATA_TEMPLATE.joinpath(f"./{package_info.license.id}.yml")
    if not yaml_path.exists():
        raise Exception(f"{package_info.license.id} is invalid license id.")
    with open(yaml_path, 'r', encoding='utf-8') as yaml_read_io:
        data = yaml.load(pystache.render(yaml_read_io.read(), package_info))
    xml = toXMLString(__generateXMLElement(data['metadata'], 'metadata'), encoding='unicode')
    return f'<?xml version="1.0" encoding="utf-8" standalone="yes"?>{xml}'.replace('\r\n', '\n').replace('\n', '\r\n')


def __generateXMLElement(props, tagname: str) -> Element:
    el = Element(tagname)
    if '_text' in props:
        el.text = props['_text']
    if '_attributes' in props:
        el.attrib = props['_attributes']
    for child_tagname, child_props_or_list in props.items():
        if child_tagname.startswith('_'):
            continue
        if not isinstance(child_props_or_list, list):
            child_props_list = [child_props_or_list]
        else:
            child_props_list = child_props_or_list
        for child_props in child_props_list:
            child_el = __generateXMLElement(child_props, child_tagname)
            el.append(child_el)
    return el
