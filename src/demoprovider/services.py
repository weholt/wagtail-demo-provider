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
TARGET_FOLDER = get_setting("DEMO-PROVIDER-TARGET-FOLDER", os.path.join(os.getcwd(), "demo-images"))
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
    """
    A service for getting random images or as helper methods to create a wagtail image
    or save an image to a django Image-field.
    """

    def __init__(self, folder: str = TARGET_FOLDER, scan_on_creation: bool = False, verbose: bool = False):
        self.folder = folder
        self.verbose = verbose
        if scan_on_creation:
            self.scan()
        else:
            self.reset()

    def info(self):
        return {keyword: len(items) for keyword, items in self.images.items()}

    def log(self, msg: str) -> None:
        if self.verbose:
            logging.info(msg)

    def reset(self) -> None:
        self.images: dict = {}
        self.filename_cache: Union[dict[str, None], None] = None
        self.url_cache: Union[dict[str, None], None] = None

    def scan(self) -> None:
        self.reset()
        for file in find_files(self.folder, extensions=SUPPORTED_IMAGE_FORMATS):
            self.add_file(file)

    def add_file(self, filename: str) -> None:
        metadata = {}
        try:
            if os.path.exists(filename + ".json"):
                metadata = json.loads(open(filename + ".json").read())
        except json.decoder.JSONDecodeError:
            pass

        for keyword in metadata.get("keywords", ["default"]):
            self.images.setdefault(keyword, []).append(DemoImage(filename=filename, metadata=metadata))

    def get_images_by_keywords(self, *keywords: str, limit: int | None = None) -> list[DemoImage]:
        if not keywords:
            keywords = self.get_random_keywords()

        result = []
        for keyword in keywords:
            result.extend(self.images.get(keyword, []))
        return limit and result[:limit] or result

    @classmethod
    def assign_filename_to_image_field(cls, filename, image_field) -> None:
        image_field.save(os.path.basename(filename), File(open(filename, "rb")))

    @classmethod
    def create_wagtail_image(cls, filename, name: str | None = None) -> Image:  # type: ignore NOQA
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
        for image in images:
            img = cls.create_wagtail_image(image.filename)
            img.collection = background_collection
            img.save()

    @classmethod
    def pretty_title_from_filename(cls, filename: str) -> str:
        return os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").capitalize()

    def get_random_keywords(self, count: int = 10) -> tuple[str]:
        return random.choices(tuple(self.images.keys()), k=count)  # type: ignore NOQA

    def get_random_image(self, *keywords: str) -> DemoImage:
        return random.choice(self.get_images_by_keywords(*keywords))

    def get_random_images(self, *keywords: str, count: int = 10) -> list[DemoImage]:
        if not keywords:
            keywords = self.get_random_keywords()
        return random.choices(self.get_images_by_keywords(*keywords), k=count)

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

    def add_local_folder(self, folder: str) -> None:
        """
        Scans a local folder for supported files, adding them as wagtail images,
        and using the folder structure to create collections in the process.
        """
        for filename in find_files(folder, extensions=SUPPORTED_IMAGE_FORMATS):
            try:
                collections = [s.strip() for s in os.path.split(filename)[0].replace(folder, "").split(os.sep) if s.strip()]

                # If the folder starts with an underscore we skip it. Simple way to control what gets
                # add to the database.
                if collections and collections[0][0] == "_":
                    continue

                # We turn subfolders into collections.
                root_coll = None
                if collections:
                    root_coll = Collection.get_first_root_node()
                    for collection in collections:
                        children = [c for c in root_coll.get_children()]
                        if collection not in [c.name for c in children]:
                            root_coll = root_coll.add_child(name=collection)
                            self.log(f"Adding collection '{root_coll}'")
                        else:
                            root_coll = [c for c in children if c.name == collection][0]

                img = ImageService.create_wagtail_image(filename)
                if root_coll:
                    img.collection = root_coll
                    img.save()
                self.log(f"+ Added {filename}")
            except Exception as ex:
                self.log(f"Error adding {filename}: {ex}")
