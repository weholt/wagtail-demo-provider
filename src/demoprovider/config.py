import os
from typing import Any

from django.conf import settings
from dotenv import load_dotenv

dotenv_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path)


SUPPORTED_IMAGE_FORMATS = [".jpg", ".png", ".avif", ".webp"]


def get_setting(key: str, default: Any | None = None) -> Any:
    return hasattr(settings, key) and getattr(settings, key) or os.environ.get(key, default)
