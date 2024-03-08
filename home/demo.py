from django.utils.lorem_ipsum import words
from wagtail.models import Page

from demoprovider.services import ImageService
from home.models import HomePage

srv = ImageService(init=True)


def run(*args, **kwargs):
    home_page = HomePage(
        title=words(count=5),
        cover_image=srv.create_wagtail_image(srv.get_random_image().filename),
    )

    root = Page.get_first_root_node()
    root.add_child(instance=home_page)  # type: ignore noqa

    srv.assign_filename_to_image_field(srv.get_random_image().filename, home_page.image)

    for random_background_image in srv.get_images_by_keywords("background", limit=10):
        srv.create_wagtail_image(random_background_image.filename)

    srv.add_images_to_collection(srv.get_images_by_keywords("blogging", limit=10), collection_name="Some new collection")
