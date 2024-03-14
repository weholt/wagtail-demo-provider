from typing import Protocol

from .unsplash import UnsplashImageProvider


class ImageProvider(Protocol):
    def query(self, query, image_count):
        ...


def init_providers(image_count=10, *keywords):
    for provider in [UnsplashImageProvider.factory()]:
        if provider:
            for keyword in keywords:
                provider.query(query=keyword, count=image_count)
