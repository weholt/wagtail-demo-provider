

def filename_from_slug(slug: str, extension: str = ".png") -> str:
    return slug.replace("-", "_").replace(" ", "_") + extension

