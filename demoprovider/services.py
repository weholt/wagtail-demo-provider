import json
import logging
import os
import random
from dataclasses import dataclass
from io import BytesIO
from typing import Union

import willow
from django.core.files import File
from django.core.files.images import ImageFile
from wagtail.images import get_image_model
from wagtail.models import Collection

from .config import SUPPORTED_IMAGE_FORMATS, get_setting
from .utils import find_files

Image = get_image_model()
TARGET_FOLDER = get_setting("DEMO-PROVIDER-TARGET-FOLDER", os.path.join(os.getcwd(), "image-repo"))
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


@dataclass
class DemoImage:
    filename: str
    metadata: dict

    def get(self, key: str) -> str:
        return self.metadata.get(key, "")

    @property
    def is_valid(self) -> bool:
        return os.path.exists(self.filename)


class ImageService:
    def __init__(self, folder: str = TARGET_FOLDER):
        self.folder = folder
        self.images = {}
        self.filename_cache: dict[str, None] | None = None
        self.url_cache: dict[str, None] | None = None

    def info(self):
        return {keyword: len(items) for keyword, items in self.images.items()}

    def init(self) -> None:
        for file in find_files(self.folder, extensions=SUPPORTED_IMAGE_FORMATS):
            self.add_file(file)

    def add_file(self, filename: str) -> None:
        try:
            metadata = json.loads(open(filename + ".json").read())
        except json.decoder.JSONDecodeError:
            metadata = {}

        for keyword in metadata.get("keywords", "default"):
            self.images.setdefault(keyword, []).append(DemoImage(filename=filename, metadata=metadata))

    def get_keyword(self, *keywords: str) -> list[DemoImage]:
        result = []
        for keyword in keywords:
            result.extend(self.images.get(keyword, []))
        return result

    @classmethod
    def assign_filename_to_image_field(cls, filename, image_field) -> None:
        image_field.save(os.path.basename(filename), File(open(filename, "rb")))

    @classmethod
    def save_image(cls, filename, name: str | None = None) -> Image:  # type: ignore NOQA
        name = name or ImageService.pretty_title_from_filename(os.path.basename(filename))
        img_bytes = open(filename, "rb").read()
        img_file = ImageFile(BytesIO(img_bytes), name=name)

        im = willow.Image.open(img_file)
        width, height = im.get_size()

        img_obj = Image(title=name, file=img_file, width=width, height=height)
        img_obj.save()
        return img_obj

    @classmethod
    def add_images_to_collection(cls, images: list[DemoImage], collection_name: str, root_collection_name: str | None = None) -> None:
        root_collection = root_collection_name and Collection.objects.get(name=root_collection_name) or Collection.get_first_root_node()
        background_collection = root_collection.add_child(name=collection_name)
        for filename in images:
            img = cls.save_image(filename)
            img.collection = background_collection
            img.save()

    @classmethod
    def pretty_title_from_filename(cls, filename: str) -> str:
        return os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").capitalize()

    def get_random_image(self, *keywords: str) -> DemoImage:
        return random.choice(self.get_keyword(*keywords))

    def get_random_images(self, *keywords: str, count: int = 10) -> list[DemoImage]:
        if not keywords:
            keywords = random.choices(self.images.keys(), k=3)  # type: ignore NOQA
        return random.choices(self.get_keyword(*keywords), k=count)

    def init_cache(self):
        if self.filename_cache:
            return

        self.filename_cache: dict[str, None] = {}
        self.url_cache: dict[str, None] = {}

        for keyword in self.images:
            for image in self.images[keyword]:
                self.filename_cache[image.filename] = None
                if url := image.get("url"):
                    self.url_cache[url] = None

    def file_exists(self, filename: str, url: Union[str, None] = None) -> bool:
        self.init_cache()
        return filename in self.filename_cache or (url and url in self.url_cache)  # type: ignore NOQA
