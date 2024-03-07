import os

import djclick as click
from wagtail.models import Collection

from demoprovider.config import SUPPORTED_IMAGE_FORMATS, get_setting
from demoprovider.services import ImageService
from demoprovider.utils import configure_django_environ, find_files

LOCAL_IMAGES_FOLDER = get_setting("LOCAL_IMAGES", os.path.join(os.getcwd(), "LOCAL_IMAGES"))


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Print more output.")
def add_local_images(verbose: bool = False):
    configure_django_environ(os.getcwd())
    if not os.path.exists(LOCAL_IMAGES_FOLDER):
        os.makedirs(LOCAL_IMAGES_FOLDER)

    failed = []

    for filename in find_files(LOCAL_IMAGES_FOLDER, extensions=SUPPORTED_IMAGE_FORMATS):
        try:
            collections = [s.strip() for s in os.path.split(filename)[0].replace(LOCAL_IMAGES_FOLDER, "").split(os.sep) if s.strip()]

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
                        print("Adding collection '%s'" % root_coll)
                    else:
                        root_coll = [c for c in children if c.name == collection][0]

            img = ImageService.save_image(filename)
            if root_coll:
                img.collection = root_coll
                img.save()

            print(f"+ {filename} to {root_coll} collection.")
        except Exception as ex:
            failed.append((filename, ex))
            print(f"Error adding {filename}: {ex}")

    if failed:
        print("%s files failed up upload" % len(failed))
        for filename, ex in failed:
            print("%s == %s" % (filename, ex))
