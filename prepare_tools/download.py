import requests
from pathlib import Path
from urllib.parse import urlparse


def downloadFile(url: str, outDir: Path):
    res = requests.get(url)
    file_name = Path(urlparse(res.url).path).name
    file_path = outDir.joinpath(file_name)
    with open(file_path, 'wb') as file:
        file.write(res.content)

    return file_path
