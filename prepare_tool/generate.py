import subprocess
import yaml
import pystache
import brotli
from logzero import logger
import zopfli.zlib as zopfli
import zopfli.gzip as gzip
from io import BytesIO
from tarfile import TarFile
from shutil import copyfile
from tempfile import TemporaryDirectory, mkstemp
from itertools import chain
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from faker import Faker
from css_html_js_minify import css_minify
from fontTools.subset import Options, Subsetter, load_font, save_font, parse_unicodes
from fontTools.ttLib import TTFont
from fontTools.ttLib.sfnt import WOFFFlavorData
from fontTools.ttLib.woff2 import WOFF2FlavorData

from .const import ROOT_DIR_PATH

FAMILY_RELATED_IDS = dict(
    LEGACY_FAMILY=1,
    TRUETYPE_UNIQUE_ID=3,
    FULL_NAME=4,
    POSTSCRIPT_NAME=6,
    PREFERRED_FAMILY=16,
    WWS_FAMILY=21,
)

COPYRIGHT_ID = 0

WEIGHT_NUMBERS = dict(
    thin='100',
    extraLight='200',
    light='300',
    normal='400',
    medium='500',
    semiBold='600',
    bold='700',
    extraBold='800',
    black='900',
)

UNICODE_TEXT_DIR = ROOT_DIR_PATH.joinpath('./groups').resolve()
LICENSE_TEMPLATE_DIR = ROOT_DIR_PATH.joinpath('./templates/licenses').resolve()
METADATA_TEMPLATE_DIR = ROOT_DIR_PATH.joinpath('./templates/metadata').resolve()
STYLESHEETS_TEMPLATE_DIR = ROOT_DIR_PATH.joinpath('./templates/stylesheets').resolve()


def saveFonts(font_fileinfo_dict: dict, output_dir: Path, info):
    with TemporaryDirectory() as tmp_dir_pathstr:
        tmp_dir = Path(tmp_dir_pathstr)

        license_template_path = LICENSE_TEMPLATE_DIR.joinpath(f"./{info['license']['id']}.txt")
        if not license_template_path.exists():
            raise Exception(f"{info['license']['id']} is invalid license id.")
        with open(license_template_path, 'r', encoding='utf-8') as file:
            license_text = pystache.render(file.read(), info)
        with open(tmp_dir.joinpath('LICENSE'), 'w', encoding='utf-8') as license_fd:
            license_fd.write(license_text)

        for weight, font_fileinfo in font_fileinfo_dict.items():
            ext = font_fileinfo['path'].suffix
            copyfile(font_fileinfo['path'], tmp_dir.joinpath(f"{info['id']}-{weight}{ext}"))

        with BytesIO() as stream:
            with TarFile.open(mode='w', fileobj=stream) as archive:
                for file_path in tmp_dir.glob('*'):
                    archive.add(file_path, arcname=file_path.name, recursive=False)
            archive_file = output_dir.joinpath(f"./{info['id']}.tar.gz")
            with open(archive_file, 'wb') as file:
                file.write(gzip.compress(stream.getvalue()))
                logger.info(f"Saved {archive_file}")


def generateOpenTypeFont(font_path: Path, number=None):
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
        sTypoAscender = font['OS/2'].sTypoAscender
        for glyphName in font['vmtx'].metrics.keys():
            font['vmtx'].metrics[glyphName] = (
                font['vmtx'].metrics[glyphName][0],
                sTypoAscender - font['vmtx'].metrics[glyphName][1],
            )
        font.save(tmp_file)

    return tmp_file


def saveSubsettedFont(font_fileinfo: dict, output_dir: Path, weight: str, info):
    output_dir = output_dir.joinpath(f"./{info['version']}/{weight}")
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = generateMetadata(info).encode('utf-8')

    fake = Faker()
    fake.seed(info['id'])
    subset_fontname = fake.slug()  # pylint: disable=no-member

    options = Options()
    options.layout_features = ['*']
    options.obfuscate_names = True

    tmp_otf_path = None
    if font_fileinfo['path'].suffix != '.otf':
        tmp_otf_path = generateOpenTypeFont(font_fileinfo['path'], font_fileinfo.get('number', None))

    for idx, unicodes_file in enumerate(UNICODE_TEXT_DIR.glob('./**/*.txt')):
        unicodes = []
        with open(unicodes_file, 'r') as fd:
            for line in fd.readlines():
                unicodes.extend(parse_unicodes(line.split('#')[0]))

        with load_font(tmp_otf_path or font_fileinfo['path'], options) as font:
            subsetter = Subsetter(options=options)
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(font)

            for record in font['name'].names:
                if record.nameID in FAMILY_RELATED_IDS.values():
                    record.string = subset_fontname
                elif record.nameID == COPYRIGHT_ID:
                    record.string = '\n'.join(info['copyrights'])

            woff_file = output_dir.joinpath(f'{idx}.woff')
            with open(woff_file, 'wb') as woff_fd:
                options.flavor = 'woff'
                font.flavorData = WOFFFlavorData()
                font.flavorData.metaData = metadata
                save_font(font, woff_fd, options)
                logger.info(f"Saved {woff_file}")
            woff2_file = output_dir.joinpath(f'{idx}.woff2')
            with open(woff2_file, 'wb') as woff2_fd:
                options.flavor = 'woff2'
                font.flavorData = WOFF2FlavorData()
                font.flavorData.metaData = metadata
                save_font(font, woff2_fd, options)
                logger.info(f"Saved {woff2_file}")

    if tmp_otf_path is not None:
        tmp_otf_path.unlink()


def generateCss(css_family_name: str, font_fileinfo: dict, weight: str, info, fallback=False):
    if fallback is not False:
        return f"""
            @font-face {{
                font-family: '{css_family_name}';
                src: local('{fallback}');
                font-weight: {WEIGHT_NUMBERS[weight]};
            }}
        """

    family_name, postscript_name = None, None
    with TTFont(font_fileinfo['path'], fontNumber=font_fileinfo.get('number', -1), lazy=True) as font:
        family_name_record = font['name'].getName(
            nameID=FAMILY_RELATED_IDS['LEGACY_FAMILY'],
            platformID=3,
            platEncID=1,
            langID=0x409,
        )
        if family_name_record is not None:
            family_name = family_name_record.toUnicode()

        postscript_name_record = font['name'].getName(
            nameID=FAMILY_RELATED_IDS['LEGACY_FAMILY'],
            platformID=3,
            platEncID=1,
            langID=0x409,
        )
        if postscript_name_record is not None:
            postscript_name = postscript_name_record.toUnicode()

    has_postscript_name = family_name != postscript_name and postscript_name is not None

    css = ''
    for idx, unicodes_file in enumerate(UNICODE_TEXT_DIR.glob('./**/*.txt')):
        with open(unicodes_file, 'r') as fd:
            unicodes = fd.read().replace('\n', ',')
        css += f"""
            @font-face {{
                font-family: '{css_family_name}';
                src:
                    local('{family_name}'),
                    {f"local('{postscript_name}')," if has_postscript_name else ""}
                    url(./{info['version']}/{weight}/{idx}.woff2) format('woff2'),
                    url(./{info['version']}/{weight}/{idx}.woff) format('woff');
                font-weight: {WEIGHT_NUMBERS[weight]};
                font-display: swap;
                unicode-range: {unicodes};
            }}
        """

    template_path = STYLESHEETS_TEMPLATE_DIR.joinpath(f"./{info['license']['id']}.css")
    if not template_path.exists():
        raise Exception(f"{info['license']['id']} is invalid license id.")
    with open(template_path, 'r', encoding='utf-8') as file:
        rendered = pystache.render(file.read(), dict(css=css_minify(css)))
    return rendered


def saveCss(output_dir: Path, css: str, basename: str):
    encoded = css.encode('utf-8')
    css_file = output_dir.joinpath(f"./{basename}.min.css")
    with open(css_file, 'wb') as file:
        file.write(encoded)
        logger.info(f"Saved {css_file}")


def generateMetadata(info):
    yaml_path = METADATA_TEMPLATE_DIR.joinpath(f"./{info['license']['id']}.yml")
    if not yaml_path.exists():
        raise Exception(f"{info['license']['id']} is invalid license id.")
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.load(pystache.render(file.read(), info))
    xml = tostring(__generateXMLElement(data['metadata'], 'metadata'), encoding='unicode')
    return f'<?xml version="1.0" encoding="utf-8" standalone="yes"?>{xml}'.replace('\r\n', '\n').replace('\n', '\r\n')


def __generateXMLElement(props, tagname: str):
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
