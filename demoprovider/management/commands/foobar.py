import os

import djclick as click

from demoprovider.utils import configure_django_environ

configure_django_environ(os.getcwd())
from django.apps import apps  # NOQA


@click.command()
def generate_demo():
    # existing_app = [app for app in apps.get_app_configs()]
    from demoprovider.services import ImageService

    srv = ImageService()
    srv.init()
    print([f.filename for f in srv.get_random_images("blogging")])
    import pprint

    pprint.pprint(srv.info())
