import djclick as click

from demoprovider.config import get_setting
from demoprovider.image_providers import init_providers


@click.command()
def init_demo():
    keywords = [p.strip() for p in get_setting("IMAGE_PROVIDER_DEFAULT_KEYWORDS").split(",")]
    init_providers(get_setting("IMAGE_PROVIDER_IMAGE_COUNT_PER_KEYWORD", 10), *keywords)
