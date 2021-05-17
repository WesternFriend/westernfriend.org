import html
from io import BytesIO
from urllib.parse import urlparse

from django.core.files import File
from django.core.files.images import ImageFile

from wagtail.documents.models import Document
from wagtail.embeds.embeds import get_embed
from wagtail.images.models import Image

import numpy as np
import requests


def parse_media_blocks(media_urls):
    media_blocks = []

    for url in media_urls.split(", "):
        domain = urlparse(url).netloc

        if domain in ["vimeo.com", "www.youtube.com"]:
            embed = get_embed(url)
            embed_tuple = ("embed", embed)
            media_blocks.append(embed_tuple)
        else:
            # The default should be to fetch a PDF or image file (i.e. from westernfriend.org)
            response = requests.get(url)
            content_type = response.headers["content-type"]
            file_name = html.unescape(url.split("/")[-1])
            file_bytes = BytesIO(response.content)

            if content_type == "application/pdf":
                # Create file
                document_file = File(file_bytes, name=file_name)

                document = Document(title=file_name, file=document_file,)

                document.save()

                document_link_block = ("document", document)

                media_blocks.append(document_link_block)
            elif content_type in ["image/jpeg", "image/png"]:
                # create image
                image_file = ImageFile(file_bytes, name=file_name)

                image = Image(title=file_name, file=image_file,)

                image.save()

                image_block = ("image", image)

                media_blocks.append(image_block)
            else:
                print(url)
                print(content_type)
                print("-----")

    return media_blocks
