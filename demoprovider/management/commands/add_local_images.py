import os

import djclick as click

from demoprovider.config import get_setting
from demoprovider.services import ImageService

LOCAL_IMAGES_FOLDER = get_setting("local-images", os.path.join(os.getcwd(), "local-images"))


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Print more output.")
def add_local_images(verbose: bool = False):
    if os.path.exists(LOCAL_IMAGES_FOLDER):
        ImageService().add_local_folder(LOCAL_IMAGES_FOLDER)
