---
title: ExdFileInterface Guide
layout: default
nav_order: 4
---

# ExdFileInterface Guide

`ExdFileInterface` gives you full control over how file structure and channel values are mapped to protobuf messages. Use it when you need multiple groups, custom attributes, or maximum performance.

## Installation

```bash
pip install ods-exd-api-box
```

## Abstract Methods

```python
from ods_exd_api_box import ExdFileInterface, exd_api

class MyHandler(ExdFileInterface):

    @classmethod
    def create(cls, file_path: str, parameters: str) -> ExdFileInterface:
        """Factory method. Receives the file path and a parameters string.
        Raise NotMyFileError if this handler cannot process the file."""

    def close(self) -> None:
        """Release any resources (file handles, caches, etc.)."""

    def fill_structure(self, structure: exd_api.StructureResult) -> None:
        """Populate the StructureResult protobuf with groups, channels,
        attributes, data types, and row counts."""

    def get_values(self, request: exd_api.ValuesRequest) -> exd_api.ValuesResult:
        """Return channel values for the requested group, channels, start
        offset, and limit."""
```

## File Rejection with `NotMyFileError`

When your plugin cannot handle a given file, raise `NotMyFileError`. You can do this in two places:

1. **In `create()`** — when the file extension or header doesn't match:

   ```python
   from ods_exd_api_box import NotMyFileError

   @classmethod
   def create(cls, file_path: str, parameters: str) -> ExdFileInterface:
       if not file_path.endswith(".tdms"):
           raise NotMyFileError(f"File '{file_path}' is not a TDMS file.")
       return cls(file_path, parameters)
   ```

2. **In `fill_structure()`** — when deeper inspection reveals the file is invalid:

   ```python
   def fill_structure(self, structure: exd_api.StructureResult) -> None:
       if not self._is_valid_content():
           raise NotMyFileError(f"File '{self.file_path}' has invalid content.")
       # ... populate structure ...
   ```

The library catches `NotMyFileError` and returns a gRPC `FAILED_PRECONDITION` status to the caller.

## Parsing Parameters

The `parameters` argument is a string passed by the ODS server. Use `ParamParser` to convert it to a dictionary:

```python
from ods_exd_api_box.utils import ParamParser

params = ParamParser.parse_params(parameters)
# Supports: "key1=value1;key2=value2", JSON strings, and Base64-encoded values
value = params.get("my_key", "default")
```

## Adding Attributes with `AttributeHelper`

`AttributeHelper.add()` populates protobuf `ContextVariables` from a Python dictionary:

```python
from ods_exd_api_box.utils import AttributeHelper

# Add file-level attributes
AttributeHelper.add(structure.attributes, {"name": "My Measurement"})

# Add channel-level attributes
AttributeHelper.add(channel.attributes, {
    "description": "Voltage measurement",
    "unit_string": "V",
})
```

Supported value types: `str`, `int`, `float`, `bool`, and datetime objects.

## Complete Example

This is the test example from `tests/external_data_file.py`:

```python
from ods_exd_api_box import ExdFileInterface, exd_api
from ods_exd_api_box.utils import AttributeHelper, ParamParser


class ExternalDataFile(ExdFileInterface):
    """Handler for .exd_api_test files."""

    @classmethod
    def create(cls, file_path: str, parameters: str) -> ExdFileInterface:
        if not file_path.endswith(".exd_api_test"):
            from ods_exd_api_box.exceptions import NotMyFileError
            raise NotMyFileError(
                f"File '{file_path}' is not handled by ExternalDataFile."
            )
        return cls(file_path, parameters)

    def __init__(self, file_path: str, parameters: str):
        params = ParamParser.parse_params(parameters)
        params.get("example_param", "default_value")
        self.file_path = file_path

    def close(self):
        pass

    def fill_structure(self, structure: exd_api.StructureResult) -> None:
        # Add file-level attributes
        AttributeHelper.add(
            attributes=structure.attributes,
            properties={"name": "Raw Layer_00001"},
        )

        # Add groups with channels, data types, units, and attributes
        # (typically read from the actual file)
        # ...

    def get_values(self, request: exd_api.ValuesRequest) -> exd_api.ValuesResult:
        # Read data for the requested channels and row range
        # Return a ValuesResult with the appropriate typed arrays
        # ...
        return exd_api.ValuesResult()
```

## The `__main__` Block

```python
if __name__ == "__main__":
    from ods_exd_api_box import serve_plugin

    serve_plugin(
        file_type_name="EXD-API-TEST",
        file_type_factory=ExternalDataFile.create,
        file_type_file_patterns=["*.exd_api_test"],
    )
```

**Parameters:**

| Parameter | Description |
|---|---|
| `file_type_name` | Identifier for the file type (used in the registry) |
| `file_type_factory` | Your `create` classmethod — called for each new file |
| `file_type_file_patterns` | Glob patterns to match filenames (e.g. `["*.tdms", "*.TDMS"]`) |

`serve_plugin()` registers your factory in `FileHandlerRegistry`, parses CLI / env configuration, and starts the gRPC server. See [Server Options](server-options) for all available settings.

## Protobuf Structure Reference

### `StructureResult`

```
StructureResult
├── identifier       (set by the library)
├── name             (set by the library — filename)
├── attributes       (ContextVariables — file-level metadata)
└── groups[]
    ├── name
    ├── id
    ├── total_number_of_channels
    ├── number_of_rows
    ├── attributes   (ContextVariables — group-level metadata)
    └── channels[]
        ├── name
        ├── id
        ├── data_type    (DT_DOUBLE, DT_STRING, DT_DATE, ...)
        ├── unit_string
        └── attributes   (ContextVariables — channel-level metadata)
```

### `ValuesRequest`

| Field | Description |
|---|---|
| `handle` | Connection handle from `Open` |
| `group_id` | Which group to read from |
| `channel_ids` | List of channel IDs to retrieve |
| `start` | Row offset (0-based) |
| `limit` | Maximum number of rows to return |

### `ValuesResult`

```
ValuesResult
├── id           (group_id echo)
└── channels[]
    ├── id       (channel_id echo)
    └── values
        ├── data_type
        └── <typed_array>   (double_array, string_array, long_array, ...)
```

## Next Steps

- [Server Options](server-options) — CLI arguments, environment variables, TLS
- [Docker Deployment](docker) — containerize your plugin
- [Real-World Plugins](plugins) — see `asam_ods_exd_api_nptdms` for a production example
