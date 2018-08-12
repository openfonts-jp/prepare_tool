import pystache
from dataclasses import dataclass
from pathlib import Path
from fontTools.ttLib import TTFont
from css_html_js_minify import css_minify

from prepare_tool.core import FontInfo, FontWeightPaths
from prepare_tool.package_info import PackageInfo
from prepare_tool.generate import FontInfo, FontWeightPaths
from prepare_tool.generate.const import NAME_ID, FILE_DIR, WEIGHT_NUMBER

with open(FILE_DIR.STYLESHEETS_TEMPLATE.joinpath('./base.css'), 'r', encoding='utf-8') as base_template_read_io:
    BASE_TEMPLATE = pystache.parse(base_template_read_io.read())
with open(FILE_DIR.STYLESHEETS_TEMPLATE.joinpath('./fallback.css'), 'r', encoding='utf-8') as base_template_read_io:
    FALLBACK_TEMPLATE = pystache.parse(base_template_read_io.read())


@dataclass()
class __GeneratedStyleSheetsStore():
    default: str = ''
    local: str = ''
    fallback: str = ''


def generateStyleSheets(
    font_weight_paths: FontWeightPaths,
    output_dir: Path,
    package_info: PackageInfo,
    fallback=False,
):
    license_template_path = FILE_DIR.STYLESHEETS_TEMPLATE.joinpath(f"./{package_info.license.id}.css")
    if not license_template_path.exists():
        raise Exception(f"{package_info.license.id} is invalid license id.")
    with open(license_template_path, 'r', encoding='utf-8') as license_template_read_io:
        license_template = pystache.parse(license_template_read_io.read())

    generated = __GeneratedStyleSheetsStore()
    for weight, font_info in vars(font_weight_paths).items():  # type: str, FontInfo
        if font_info is None:
            continue
        __generateStyleSheetsWithWeight(
            store=generated,
            font_info=font_info,
            weight=weight,
            output_dir=output_dir,
            package_info=package_info,
        )

    if fallback is True:
        with open(output_dir.joinpath('./fallback.min.css'), 'wb') as fallback_file_write_io:
            minified = css_minify(generated.fallback)
            fallback_file_write_io.write(minified.encode('utf-8'))

    with open(output_dir.joinpath('./local-first.min.css'), 'wb') as local_file_write_io:
        minified = pystache.render(license_template, {'css': css_minify(generated.local)})
        local_file_write_io.write(minified.encode('utf-8'))

    with open(output_dir.joinpath('./style.min.css'), 'wb') as default_file_write_io:
        minified = pystache.render(license_template, {'css': css_minify(generated.default)})
        default_file_write_io.write(minified.encode('utf-8'))


def __generateStyleSheetsWithWeight(
    store: __GeneratedStyleSheetsStore,
    font_info: FontInfo,
    weight: str,
    output_dir: Path,
    package_info: PackageInfo,
):
    weight_number = getattr(WEIGHT_NUMBER, weight)

    local_name_list = __getLocalFamilyNameList(font_info)
    render_options = {
        'package_info': package_info,
        'weight_number': weight_number,
    }

    store.fallback += pystache.render(FALLBACK_TEMPLATE, render_options)

    for unicodes_file in FILE_DIR.UNICODE_TEXT.glob('./**/*.txt'):  # type: Path
        idx = unicodes_file.stem
        font_base_path = f"./{package_info.version}/{weight}/{idx}"
        with open(unicodes_file, 'r') as fd:
            unicodes = fd.read().replace('\n', ',')

        store.default += pystache.render(
            BASE_TEMPLATE,
            {
                **render_options,
                'unicodes': unicodes,
                'font_base_path': font_base_path,
            },
        )
        store.local += pystache.render(
            BASE_TEMPLATE,
            {
                **render_options,
                'unicodes': unicodes,
                'font_base_path': font_base_path,
                'local_name_list': local_name_list,
            },
        )


def __getLocalFamilyNameList(font_info: FontInfo):
    family_name_set = set()
    local_name_id_list = [
        NAME_ID.LEGACY_FAMILY,
        NAME_ID.POSTSCRIPT_NAME,
        NAME_ID.PREFERRED_FAMILY,
    ]

    options = dict(
        file=font_info.path,
        lazy=True,
    )
    if font_info.number is not None:
        options['fontNumber'] = font_info.number

    with TTFont(**options) as font:
        for nameID in local_name_id_list:
            name_record = font['name'].getName(
                nameID=nameID,
                platformID=3,
                platEncID=1,
                langID=0x409,
            )
            if name_record is not None:
                family_name_set.add(name_record.toUnicode())
    return list(family_name_set)
