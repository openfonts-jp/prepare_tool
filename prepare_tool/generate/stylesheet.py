import pystache
from typing import Optional, Set, List
from pathlib import Path
from fontTools.ttLib import TTFont
from css_html_js_minify import css_minify

from prepare_tool.core import Core
from prepare_tool.models import Package, Font
from prepare_tool.const import NAME_ID, FILE_DIR, WEIGHT_NUMBER

with open(FILE_DIR.STYLESHEETS_TEMPLATE.joinpath('./base.css'), 'r', encoding='utf-8') as base_template_read_io:
    BASE_TEMPLATE = pystache.parse(base_template_read_io.read())
with open(FILE_DIR.STYLESHEETS_TEMPLATE.joinpath('./local.css'), 'r', encoding='utf-8') as local_template_read_io:
    LOCAL_TEMPLATE = pystache.parse(local_template_read_io.read())


class StyleSheetGenerator():
    def __init__(self, core: Core) -> None:
        self.__core = core

    def generate(self) -> None:
        package = self.__core.package
        output_dir = self.__core.directories.webfonts

        license_template_path = FILE_DIR.STYLESHEETS_TEMPLATE.joinpath(f"./{package.license}.css")
        if not license_template_path.exists():
            raise Exception(f"{package.license} is invalid license id.")
        with open(license_template_path, 'r', encoding='utf-8') as license_template_read_io:
            license_template = pystache.parse(license_template_read_io.read())

        generated_style = ''
        for source in package.sources:
            weight: str
            font: Font
            for weight, font in source.fonts:
                if font is None:
                    continue
                generated_style += self.__generateStyleForWeight(weight=weight, font=font)

        with open(output_dir.joinpath('./style.min.css'), 'wb') as style_io:
            minified = pystache.render(license_template, {'css': css_minify(generated_style)})
            style_io.write(minified.encode('utf-8'))

    def __generateStyleForWeight(self, weight: str, font: Font) -> str:
        style = ''
        package = self.__core.package
        weight_number = getattr(WEIGHT_NUMBER, weight)
        local_name_list = self.__getLocalFamilyName(font)

        style += pystache.render(
            LOCAL_TEMPLATE,
            {
                'package': package,
                'weight_number': weight_number,
                'local_src': ','.join(map(lambda n: f"local('{n}')", local_name_list)),
            },
        )

        for unicodes_file in FILE_DIR.UNICODE_TEXT.glob('./**/*.txt'):
            idx = unicodes_file.stem
            with open(unicodes_file, 'r') as fd:
                style += pystache.render(
                    BASE_TEMPLATE,
                    {
                        'package': package,
                        'weight_number': weight_number,
                        'unicodes': fd.read().replace('\n', ','),
                        'font_base_path': f"./{package.version}/{weight}/{idx}",
                    },
                )
        return style

    def __getLocalFamilyName(self, font: Font) -> List[str]:
        family_name_set: Set[str] = set()
        font_path = self.__core.findFontfilePath(font)

        with TTFont(file=font_path, lazy=True, fontNumber=font.number) as ttfont:

            def getName(name_id):
                return ttfont['name'].getName(
                    nameID=name_id,
                    platformID=3,
                    platEncID=1,
                    langID=0x409,
                )

            name_record = getName(NAME_ID.LEGACY_FAMILY)
            weight_record = getName(NAME_ID.LEGACY_SUBFAMILY)
            if name_record is not None and weight_record is not None:
                family_name_set.add(f"{name_record.toUnicode()} {weight_record.toUnicode()}")
                family_name_set.add(f"{name_record.toUnicode()}-{weight_record.toUnicode()}")

            name_record = getName(NAME_ID.POSTSCRIPT_NAME)
            if name_record is not None:
                family_name_set.add(name_record.toUnicode())
            name_record = getName(NAME_ID.FULL_NAME)
            if name_record is not None:
                family_name_set.add(name_record.toUnicode())

        return list(family_name_set)
