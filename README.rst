**********************
Wagtail Demo Provider
**********************

DemoProvider is a reusable Wagtail app for getting random stock images from online providers such as Unsplash and local images
into your Wagtail site with ease. This is especially helpful for demonstration purposes or during development.

**Note** This is currently very early in development, and even if it's a small project, it should be considered
as in alpha state or as proof-of-concept only, and should NOT be used in production. Several imortant areas are
not covered at all, like proper documentation & unit tests.

Features
--------

* Management command for downloading stock images from image providers (currently only unsplash) for local use.
* Management command for adding local lots of images as Wagtail images.
* A demo-provider concept to easily make each app have a consistent way of adding demonstration data.
* A few helper-methods to add an local image to a Django Imagefield or as a Wagtail image in code.

Current status
--------------

* Version : 0.1.0
* Status: alpha/proof-of-concept

Tested with
------------

* Python version 3.12.2
* Django version 5.0.2
* Wagtail version 6.0.1

Installation
------------

Clone main repository:

.. code-block:: bash

    $ git clone https://github.com/weholt/wagtail-demo-provider.git
    $ cd wagtail-demo-provider
    $ pip install .

Or

.. code-block:: bash

    $ pip install git+https://github.com/weholt/wagtail-demo-provider.git

Add demoprovider at the top of your installed apps:

.. code-block:: bash

    INSTALLED_APPS = [
        "demoprovider",
    ]

Important environment variables, can be defined in either .env or settings.py. Example of .env:

.. code-block:: bash

    UNSPLASH_ACCESS_KEY=<your unsplash api-key>
    IMAGE_PROVIDER_DEFAULT_KEYWORDS = portraits, landscape, people, background, profile image, blogging
    IMAGE_PROVIDER_IMAGE_COUNT_PER_KEYWORD = 10
    LOCAL_IMAGES = local-images
    DEMO-PROVIDER-TARGET-FOLDER=demo-images

Basic Usage
-----------

After installation you'll have three new management commands available:

* add_local_images
* download_images
* run_demo_providers

**add_local_images**

This command will look into a specified folder and look for supported image files. Files found
will be added to the site as Wagtail images. Any folders found will be created as collections,
adding the images in them to the newly created collection.

You specify folder to scan either in a *.env*-file in the root directory of your site (next to manage.py)
or in *settings.py* for your project. If not specified, the code looks for a folder called *'local-images'*
in your project root directory.

**download_images**

This command will download stock images from online providers, currently Unsplash, to a local folder specified
as *DEMO-PROVIDER-TARGET-FOLDER* either in a *.env*-file or in *settings.py*. If not specified a folder called
*demo-images* will be created/used.

You can specifiy a comma-separated list of keywords to use to filter images to download, setting the
variable *IMAGE_PROVIDER_DEFAULT_KEYWORDS* in your .env/settings.py.

You can also specifiy how many images per keyword to download, by adding
an integer value to the field *IMAGE_PROVIDER_IMAGE_COUNT_PER_KEYWORD* in your .env/settings.py.

**run_demo_providers**

This command will iterate all installed apps (INSTALLED_APPS in settings.py) and look for a file called *demo.py*.
If found, it will import that file and try to execute a method inside called *run*. Example below:

.. code-block:: python


    def run(*args, **kwargs):
        print("Hello world! I'm a simple demo provider.")

Running

.. code-block:: bash

    $ python manage.py run_demo_providers

will produce:

.. code-block:: bash

    "Hello world! I'm a simple demo provider."

The intended use is for each app to specify its own *demo.py* which will create a suitable set of data
for demonstration or development purposes. The class *ImageService*, defined in *demoprovider.services*
provides a few helpful methods which can be used in this process.

ImageService
------------

Defined in *demoprovider.services*, this class is the heart of this project. This service will scan a local
folder defined in the .env/settings.py, by default *demo-images* in the project root, and provide a cache
of images defined the DemoImage dataclass:

.. code-block:: python

    @dataclass
    class DemoImage:
        filename: str
        metadata: dict

        def get(self, key: str) -> str:
            return self.metadata.get(key, "")

        @property
        def is_valid(self) -> bool:
            return os.path.exists(self.filename)

To instantiate the service:

.. code-block:: python

    from demoprovider.services import ImageService

    srv = ImageService()

The most important methods on the ImageService are the following:

For scanning the folder specified in .env/settings:

.. code-block:: python

    def scan(self) -> None:
        ...

To get a list of image objects based on keywords, with an optional limit. If keywords aren't specified
three random keywords will be used:

.. code-block:: python

    def get_images_by_keywords(self, *keywords: str, limit: int | None = None) -> list[DemoImage]:
        ...

To assign an image specified as a local filename to a Django ImageField (Note that this is a classmethod,
so no need to instaniate the service:

.. code-block:: python

    @classmethod
    def assign_filename_to_image_field(cls, filename, image_field) -> None:
        ...

To create a Wagtail image from a local filename, use the classmethod below. The created object
is returned and can be assigned to other fields:

.. code-block:: python

    @classmethod
    def create_wagtail_image(cls, filename, name: str | None = None) -> Image:  # type: ignore NOQA
        ...

To add a list of DemoImage instances to a collection, creating it if it doesn't exists, optionally as a child
to a specified root collection:

.. code-block:: python

    @classmethod
    def add_images_to_collection(cls, images: list[DemoImage], collection_name: str, root_collection_name: str | None = None) -> Image:
        ...

To get one random image, filtered on optional keywords:

.. code-block:: python

    def get_random_image(self, *keywords: str) -> DemoImage:
        ...

To get a list of random DemoImage instances, based on optional keywords, and count per keyword:

.. code-block:: python

    def get_random_images(self, *keywords: str, count: int = 10) -> list[DemoImage]:
        ...

To add a local folder of images to your website as Wagtail images, creating collections for the images
based on the folder structure in the folder to scan:

.. code-block:: python

    def add_local_folder(self, folder: str) -> None:
        ...

Usage
-----

Page model:

.. code-block:: python

    from django.db import models
    from wagtail.models import Page
    from wagtail.images import get_image_model
    from wagtail.admin.panels import FieldPanel

    Image = get_image_model()


    class HomePage(Page):

        image = models.ImageField(upload_to="django_images", null=True, blank=True)
        cover_image = models.ForeignKey(
            Image,
            on_delete=models.SET_NULL,
            related_name="+",
            null=True,
            blank=True,
        )

        content_panels = Page.content_panels +
            [FieldPanel("image"), FieldPanel("cover_image")]

demo.py, located in the app-folder:

.. code-block:: python

    from django.utils.lorem_ipsum import words
    from wagtail.models import Page
    from home.models import HomePage
    from demoprovider.services import ImageService

    srv = ImageService()


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

        srv.add_images_to_collection(
            srv.get_images_by_keywords("blogging", limit=10),
            collection_name="Some new collection"
        )
