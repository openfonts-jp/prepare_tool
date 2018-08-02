import cgi
import requests
from pathlib import Path
from urllib.parse import urlparse


def downloadFile(url: str, outDir: Path):
    res = requests.get(url)
    _, params = cgi.parse_header(res.headers.get('content-disposition', ''))
    file_name = params.get('filename', Path(urlparse(res.url).path).name)
    file_path = outDir.joinpath(file_name)
    with open(file_path, 'wb') as file:
        file.write(res.content)

    return file_path
