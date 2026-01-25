"""
Initializes the simple feature module.
"""

import importlib.util

if importlib.util.find_spec("pandas") is None:
    raise ImportError(
        "pandas is required for the 'simple' feature. Install with: pip install 'ods_exd_api_box[simple]'"
    )

from .file_simple import serve_plugin_simple
from .file_simple_interface import FileSimpleInterface

__all__ = ["serve_plugin_simple", "FileSimpleInterface"]
