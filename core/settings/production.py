from .base import *  # noqa: F403

DEBUG = False

try:
    from .local import *  # noqa: F403
except ImportError:
    pass
