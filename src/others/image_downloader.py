import re

import requests


def download_image(url: str) -> bool:
    img_tag_regex = r"""<img.*?src="(.*?)"[^\>]+>"""

    response = requests.get(url)
    if response.status_code != 200:
        return False

    text = response.text
    image_links = re.findall(img_tag_regex, text)

    for link in image_links:
        resp = requests.get(link)
        with open(link.replace("https://", "").replace("http://", ""), "wb") as file:
            file.write(resp.content)

    return True
