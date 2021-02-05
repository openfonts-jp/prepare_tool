import subprocess
import yaml
from typing import List
from pathlib import Path
from tempfile import mkstemp
from xml.etree.ElementTree import Element, tostring as to_xml_string
from faker import Faker
from fontTools.subset import Options, Subsetter, load_font, save_font, parse_unicodes
from fontTools.ttLib import TTFont
from fontTools.ttLib.sfnt import WOFFFlavorData
from fontTools.ttLib.woff2 import WOFF2FlavorData

from prepare_tool.core import Core
from prepare_tool.models import Font
from prepare_tool.const import FILE_DIR, NAME_ID, FAMILY_RELATED_NAME_ID


class WebFontGenerator():
    def __init__(self, core: Core) -> None:
        self.__core = core

    def generate(self) -> None:
        package = self.__core.package

        for source in package.sources:
            for weight, font in source.fonts:
                if font is None:
                    continue
                self.__generateForWeight(weight=weight, font=font)

    def __generateForWeight(self, weight: str, font: Font) -> None:
        package = self.__core.package
        base_dir = self.__core.directories.webfonts
        output_dir = base_dir.joinpath(f"./{package.version}/{weight}")
        font_path = self.__core.findFontfilePath(font)

        output_dir.mkdir(parents=True, exist_ok=True)
        metadata = self.__generateMetadata()

        Faker.seed(package.id)
        fake = Faker()
        subset_fontname: str = fake.name()

        tmp_otf_font_path = None
        if not font_path.name.endswith('.otf'):
            tmp_otf_font_path = self.__generateOpenTypeFont(font)

        options = Options()
        options.font_number = font.number
        options.hinting = False
        options.desubroutinize = True
        options.drop_tables += [
            'FFTM', 'PfEd', 'TeX', 'BDF', 'cvt', 'fpgm', 'prep', 'gasp', 'VORG', 'CBDT', 'CBLC', 'sbix'
        ]
        for ignored in ['rvrn', 'locl']:
            options.layout_features.remove(ignored)

        for unicodes_file in FILE_DIR.UNICODE_TEXT.glob('./**/*.txt'):
            idx = unicodes_file.stem
            unicodes: List[str] = []

            with open(unicodes_file, 'r') as unicode_read_io:
                for line in unicode_read_io.readlines():
                    unicodes.extend(parse_unicodes(line.split('#')[0]))

            with load_font(tmp_otf_font_path, options) as ttfont:
                subsetter = Subsetter(options=options)
                subsetter.populate(unicodes=unicodes)
                subsetter.subset(ttfont)

                for record in ttfont['name'].names:
                    if record.nameID == NAME_ID.COPYRIGHT:
                        record.string = '\n'.join(package.copyrights)
                    elif record.nameID in FAMILY_RELATED_NAME_ID:
                        record.string = subset_fontname

                woff_file = output_dir.joinpath(f"{idx}.woff")
                with open(woff_file, 'wb') as woff_write_io:
                    options.flavor = 'woff'
                    ttfont.flavorData = WOFFFlavorData()
                    ttfont.flavorData.metaData = metadata
                    save_font(ttfont, woff_write_io, options)

                woff2_file = output_dir.joinpath(f"{idx}.woff2")
                with open(woff2_file, 'wb') as woff2_write_io:
                    options.flavor = 'woff2'
                    ttfont.flavorData = WOFF2FlavorData()
                    ttfont.flavorData.metaData = metadata
                    save_font(ttfont, woff2_write_io, options)

    def __generateMetadata(self) -> bytes:
        package = self.__core.package
        yaml_path = FILE_DIR.METADATA_TEMPLATE.joinpath(f"./{package.license}.yml")
        if not yaml_path.exists():
            raise Exception(f"{package.license} is invalid license id.")

        with open(yaml_path, 'r', encoding='utf-8') as yaml_read_io:
            data = yaml.safe_load(yaml_read_io.read())

        root_el = self.__generateXMLElement(data['metadata'], 'metadata')
        copyright_el = self.__generateXMLElement({}, 'copyright')
        for copyright_text in package.copyrights:
            copyright_el.append(self.__generateXMLElement({'_text': copyright_text}, 'text'))
        root_el.append(copyright_el)

        xml = to_xml_string(root_el, encoding='unicode')
        return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{xml}'.encode('utf-8')

    def __generateXMLElement(self, props: dict, tagname: str) -> Element:
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
                child_el = self.__generateXMLElement(child_props, child_tagname)
                el.append(child_el)
        return el

    def __generateOpenTypeFont(self, font: Font) -> Path:
        font_path = self.__core.findFontfilePath(font)
        number = font.number
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
        with TTFont(font_path, fontNumber=number) as ttf_font, TTFont(tmp_file) as otf_font:
            self.__copyVMTXTable(source=ttf_font, target=otf_font).save(tmp_file)

        return tmp_file

    def __copyVMTXTable(self, source: TTFont, target: TTFont) -> TTFont:
        if not ('vmtx' in source and 'vmtx' in target):
            return target

        target_reversed_cmap = target['cmap'].buildReversed()
        source_cmap = source['cmap'].getBestCmap()

        for target_glyph_name in target['vmtx'].metrics.keys():
            source_glyph_name = None

            if target_glyph_name in target_reversed_cmap:
                cid = target_reversed_cmap[target_glyph_name].pop()
                source_glyph_name = source_cmap[cid]
            else:
                gid = target.getGlyphID(target_glyph_name)
                source_glyph_name = source.getGlyphName(gid)

            target['vmtx'].metrics[target_glyph_name] = source['vmtx'].metrics[source_glyph_name]

        return target
