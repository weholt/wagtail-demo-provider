from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.images import get_image_model
from wagtail.models import Page

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

    content_panels = Page.content_panels + [FieldPanel("image"), FieldPanel("cover_image")]
