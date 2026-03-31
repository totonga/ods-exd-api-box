---
title: FileSimpleInterface Guide
layout: default
nav_order: 5
---

# FileSimpleInterface Guide

`FileSimpleInterface` lets you build an EXD-API plugin by returning a pandas DataFrame. The library handles protobuf generation, data type mapping, and value serialization automatically.

## Installation

```bash
pip install 'ods-exd-api-box[simple]'
```

This installs `pandas >=2.0` as an additional dependency.

## Abstract Methods (required)

```python
from ods_exd_api_box.simple import FileSimpleInterface

class MyHandler(FileSimpleInterface):

    @classmethod
    def create(cls, file_path: str, parameters: dict[str, Any]) -> FileSimpleInterface:
        """Factory method. Receives the file path and parsed parameters dict."""

    def close(self) -> None:
        """Release resources."""

    def data(self) -> pd.DataFrame:
        """Return the file contents as a DataFrame."""
```

{: .note }
Unlike `ExdFileInterface`, the `parameters` argument is already parsed into a `dict[str, Any]` — the library handles `ParamParser` for you.

## Optional Hooks

Override these to customize the generated structure:

| Method | Return Type | Default | Purpose |
|---|---|---|---|
| `not_my_file()` | `bool` | `False` | Return `True` to reject the file |
| `file_attributes()` | `dict[str, Any]` | `{}` | File-level metadata (name, description, …) |
| `group_attributes()` | `dict[str, Any]` | `{}` | Group-level metadata |
| `column_names()` | `list[str] \| None` | `None` (use DataFrame columns) | Override column names |
| `column_units()` | `list[str]` | `[]` | Unit string per column |
| `column_descriptions()` | `list[str]` | `[]` | Description per column |

### File Rejection with `not_my_file()`

Unlike `ExdFileInterface` which raises `NotMyFileError`, the simple interface uses a boolean:

```python
def not_my_file(self) -> bool:
    df = self.data()
    if df.empty or len(df.columns) == 1:
        return True  # reject — library converts this to NotMyFileError
    return False
```

The library catches `True` and raises `NotMyFileError` internally.

## Data Type Mapping

The library automatically maps numpy/pandas dtypes to ODS `DataTypeEnum`:

| numpy / pandas dtype | ODS DataTypeEnum |
|---|---|
| `uint8` | `DT_BYTE` |
| `int8`, `int16` | `DT_SHORT` |
| `uint16`, `int32` | `DT_LONG` |
| `uint32`, `int64` | `DT_LONGLONG` |
| `uint64` | `DT_DOUBLE` (widened) |
| `float32` | `DT_FLOAT` |
| `float64` | `DT_DOUBLE` |
| `datetime64` | `DT_DATE` |
| string dtypes | `DT_STRING` |
| `complex64` | `DT_COMPLEX` |
| `complex128` | `DT_DCOMPLEX` |

{: .warning }
Unsupported dtypes raise `NotImplementedError`. Ensure your DataFrame columns use one of the types above.

## Auto-Generated Structure

The library creates a single group named `"data"` with one channel per DataFrame column:

- **Channel names** come from `column_names()` or DataFrame column headers
- **Channel data types** are mapped from numpy dtypes (see table above)
- **Channel units** and **descriptions** are padded with empty strings if your lists are shorter than the column count
- The **first column** is marked as `independent` if it is monotonically increasing and unique

## Complete Example

From `tests/simple/file_simple_example.py`:

```python
import logging
from typing import Any, override

import pandas as pd

from ods_exd_api_box.simple.file_simple_interface import FileSimpleInterface


class FileSimpleExample(FileSimpleInterface):
    """Concrete implementation for reading CSV files."""

    @classmethod
    @override
    def create(cls, file_path: str, parameters: dict[str, Any]) -> FileSimpleInterface:
        return cls(file_path, parameters)

    def __init__(self, file_path: str, parameters: dict[str, Any]) -> None:
        self.file_path = file_path
        self.parameters = parameters
        self.df: pd.DataFrame | None = None
        self.log = logging.getLogger(__name__)

    @override
    def close(self) -> None:
        if self.df is not None:
            self.log.info("Closing file: %s", self.file_path)
            del self.df
            self.df = None

    @override
    def not_my_file(self) -> bool:
        df = self.data()
        if df.empty or len(df.columns) == 1 or all(df.dtypes == "object"):
            return True
        return False

    @override
    def data(self) -> pd.DataFrame:
        if self.df is None:
            self.log.info("Reading file: %s", self.file_path)
            # Read your file here, e.g.:
            # self.df = pd.read_csv(self.file_path, **self.parameters)
            self.df = pd.DataFrame(...)  # your data
        return self.df
```

## The `__main__` Block

```python
if __name__ == "__main__":
    from ods_exd_api_box.simple.file_simple import serve_plugin_simple

    serve_plugin_simple(
        file_type_name="TEST_SIMPLE",
        file_type_factory=FileSimpleExample.create,
        file_type_file_patterns=["*.TEST_SIMPLE"],
    )
```

**Parameters:**

| Parameter | Description |
|---|---|
| `file_type_name` | Identifier for the file type |
| `file_type_factory` | Your `create` classmethod |
| `file_type_file_patterns` | Glob patterns to match filenames |

`serve_plugin_simple()` internally:
1. Registers your factory in `FileSimpleRegistry`
2. Registers the `FileSimple` wrapper as the `ExdFileInterface` implementation
3. Calls `serve_plugin()` to start the gRPC server

All [server options](server-options) (port, TLS, auto-close, etc.) apply exactly the same.

## Tips

- **Cache your DataFrame** in `data()` to avoid re-reading on every call (the library calls `data()` multiple times for structure and values).
- **Use `not_my_file()`** to gracefully reject files that don't match your expected format.
- **Column order matters** — the first column is checked for independent/monotonic status.
- **Parameters** are parsed from the raw string automatically. Semicolon-separated (`key=val;key2=val2`), JSON, and Base64-wrapped formats are all supported.

## Next Steps

- [Server Options](server-options) — CLI arguments, environment variables, TLS
- [Docker Deployment](docker) — containerize your plugin
- [Real-World Plugins](plugins) — see `asam_ods_exd_api_pandascsv` for a production example using this interface
