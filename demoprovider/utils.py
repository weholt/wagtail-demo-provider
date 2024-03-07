# flake8: noqa
# type: ignore

import os
import sys

import django


def configure_django_environ(folder):
    "Configures the django environment based on the location of the manage.py file."
    manage_py_file = os.path.join(folder, "manage.py")
    if not os.path.exists(manage_py_file):
        raise SystemError("Manage.py was not found in the current folder")

    correct_line = next(
        ((line for line in open(manage_py_file).readlines() if "os.environ.setdefault" in line)),
        None,
    )

    if not correct_line:
        raise SystemError("Could not parse manage.py to find correct django environment.")

    settings_folder = correct_line.strip().replace("os.environ.setdefault('DJANGO_SETTINGS_MODULE', '", "").replace(".settings')", "")

    sys.path.append(folder)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.settings" % settings_folder)

    try:
        from django.core.management import execute_from_command_line  # type: ignore noqa
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and " "available on your PYTHONPATH environment variable? Did you " "forget to activate a virtual environment?"
        ) from exc

    django.setup()


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
