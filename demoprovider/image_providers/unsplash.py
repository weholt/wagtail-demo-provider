import json
import logging
import os

import requests
from pyunsplash import PyUnsplash

from demoprovider.config import get_setting
from demoprovider.services import ImageService
from demoprovider.utils import filename_from_slug

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)

TARGET_FOLDER = get_setting("DEMO-PROVIDER-TARGET-FOLDER", os.path.join(os.getcwd(), "image-repo"))
UNSPLASH_ACCESS_KEY = get_setting("UNSPLASH_ACCESS_KEY")

if not UNSPLASH_ACCESS_KEY:
    logging.warning("Unsplash API-KEY not found in .env. Unsplash image provider not available.")


class UnsplashImageProvider:
    @classmethod
    def factory(cls):
        return UNSPLASH_ACCESS_KEY and UnsplashImageProvider(api_key=UNSPLASH_ACCESS_KEY, target_folder=TARGET_FOLDER)

    def __init__(self, api_key: str, target_folder: str, verbose: bool = True) -> None:
        self.api_key = api_key
        self.target_folder = target_folder
        self.verbose = verbose
        self.api = PyUnsplash(api_key=self.api_key)
        self.service = ImageService()

    def log(self, msg: str) -> None:
        if self.verbose:
            logging.info(msg)

    def process_photos(self, photos, keywords: list[str] | None, folder: str | None):
        for photo in photos:
            metadata = {
                "title": photo.body.get("slug"),
                "url": photo.url,
                "keywords": keywords,
                "attribution": photo.get_attribution(),
                "unsplash-user": photo.body.get("user", {}).get("username"),
                "portfolio_url": photo.body.get("user", {}).get("portfolio_url"),
            }

            if self.service.file_exists(filename_from_slug(metadata.get("title")), metadata.get("url")):
                continue

            if data := self.download_photo(photo):
                self.save_file(metadata, data, folder)

    def download_photo(self, photo) -> None | bytes:
        try:
            response = requests.get(photo.link_download, allow_redirects=True)
            self.log(f"Downloaded {photo.link_download}")
            return response.content
        except Exception as ex:
            self.log(f"Error downloading {photo.link_download}: {ex}")

    def save_file(self, metadata: dict[str, str], data: bytes, folder: str | None) -> None:
        base_folder = folder and os.path.join(self.target_folder, "unsplash", folder) or os.path.join(self.target_folder, "unsplash")
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)

        filename = os.path.join(base_folder, filename_from_slug(metadata.get("title")))
        try:
            open(filename, "wb").write(data)
            open(filename + ".json", "w").write(json.dumps(metadata))
            self.log(f"Saved {filename}")
            self.service.add_file(filename)
        except Exception as ex:
            self.log(f"Error saving {filename}: {ex}")

    def query(self, query, count=1) -> None:
        self.process_photos(self.api.photos(type_="random", count=count, featured=True, query=query).entries, keywords=[query], folder=query)

    def collections(self, per_page=30) -> None:
        collections = self.api.collections(per_page)
        while collections.has_next:
            for collection in collections.entries:
                self.process_photos(collection.photos())
            collections = collections.get_next_page()
