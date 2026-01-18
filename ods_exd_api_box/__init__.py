"""
Initialization of the ods-exd-api-box package.
Loads the protobuf stubs and makes them available at package level.
"""

try:
    from importlib.metadata import version

    __version__ = version("ods-exd-api-box")
except Exception:
    __version__ = "0.0.0.dev0"

__author__ = "totonga"

# fmt: off
# isort: skip_file
from .proto import ods, exd_api, exd_grpc

from .exceptions import NotMyFileError
from .file_interface import ExdFileInterface
from .file_handler_registry import FileHandlerRegistry
from .external_data_reader import ExternalDataReader
from .server import serve_plugin
# fmt: on

__all__ = [
    "ods",
    "exd_api",
    "exd_grpc",
    "FileHandlerRegistry",
    "ExternalDataReader",
    "serve_plugin",
    "ExdFileInterface",
    "NotMyFileError",
    "__version__",
]
