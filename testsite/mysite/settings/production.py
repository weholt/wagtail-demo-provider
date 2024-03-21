# flake8: noqa
# type: ignore


from .base import *

DEBUG = False

try:
    from .local import *
except ImportError:
    pass
