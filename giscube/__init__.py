from .utils import get_version  # noqa isort:skip

# 'alpha', 'beta', 'rc', 'final'
VERSION = (0, 114, 0, 'final', 0)

__version__ = get_version(VERSION)

default_app_config = 'giscube.apps.GiscubeConfig'
