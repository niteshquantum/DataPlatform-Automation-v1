import importlib
import pkgutil

from scripts.python.common import downloaders


DOWNLOADERS = {}


for _, module_name, _ in pkgutil.iter_modules(downloaders.__path__):

    module = importlib.import_module(
        f"scripts.python.common.downloaders.{module_name}"
    )

    source_type = getattr(module, "SOURCE_TYPE", None)

    if source_type:
        DOWNLOADERS[source_type] = module


def get_downloader(source_type):
    downloader = DOWNLOADERS.get(source_type)

    if downloader is None:
        raise ValueError(
            f"Unsupported source type: {source_type}"
        )

    return downloader