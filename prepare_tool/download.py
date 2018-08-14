import cgi
import requests
from pathlib import Path
from urllib.parse import urlparse

from prepare_tool.package_info import PackageInfo


def downloadFileFromUrl(url: str, outDir: Path, package_info: PackageInfo):
    res = requests.get(url, headers={'Referer': package_info.website})
    _, params = cgi.parse_header(res.headers.get('content-disposition', ''))
    file_name = params.get('filename', Path(urlparse(res.url).path).name)
    file_path = outDir.joinpath(file_name)
    with open(file_path, 'wb') as file:
        file.write(res.content)

    return file_path
