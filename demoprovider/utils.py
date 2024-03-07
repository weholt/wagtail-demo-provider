import os
from typing import Type


def find_files(folder: str, extensions=None):
    "Finds files in a given folder, including subfolders, according to a list of file extensions"
    if not extensions:
        extensions = []
    for root, _, files in os.walk(folder):
        for file in files:
            if not extensions or os.path.splitext(file)[-1].lower() in extensions:
                yield os.path.join(root, file)


def filename_from_slug(slug: str, extension: str = ".png") -> str:
    return slug.replace("-", "_").replace(" ", "_") + extension


def implements(proto: Type):
    """
    Credits: https://stackoverflow.com/questions/62922935/python-check-if-class-implements-unrelated-interface
    Creates a decorator for classes that checks that the decorated class implements the runtime protocol `proto`
    """

    def _deco(cls_def):
        try:
            assert issubclass(cls_def, proto)
        except AssertionError as e:
            e.args = (f"{cls_def} does not implement protocol {proto}",)
            raise
        return cls_def

    return _deco
