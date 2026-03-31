---
title: Architecture
layout: default
nav_order: 2
---

# Architecture

This page explains how the library wires together gRPC, the file registry, and your plugin code.

## Core Components

| Component | Module | Role |
|---|---|---|
| `ExternalDataReader` | `ods_exd_api_box.external_data_reader` | gRPC servicer — receives `Open`, `Close`, `GetStructure`, `GetValues` calls |
| `FileHandlerRegistry` | `ods_exd_api_box.file_handler_registry` | Maps file type names / patterns to factory functions |
| `serve_plugin()` | `ods_exd_api_box.server` | Registers a factory, configures the server, starts listening |
| `serve_plugin_simple()` | `ods_exd_api_box.simple.file_simple` | Wraps a `FileSimpleInterface` factory inside `FileSimple` and delegates to `serve_plugin()` |

## Call Flow — `ExdFileInterface`

When you call `serve_plugin()`, the following happens:

```
serve_plugin(name, factory, patterns)
  └─ FileHandlerRegistry.register(name, factory, patterns)
  └─ serve(config)
       └─ grpc.server(...)
       └─ ExternalDataReader  ← added as gRPC servicer
       └─ server.start()
```

At runtime, when an ODS server calls the plugin:

```
gRPC Open(url, parameters)
  └─ ExternalDataReader.Open()
       └─ FileHandlerRegistry.create_from_path(file_path, parameters)
            └─ Your factory(file_path, parameters)  → ExdFileInterface instance
       └─ Instance stored in file_map with ref counting

gRPC GetStructure(handle)
  └─ ExternalDataReader.GetStructure()
       └─ your_instance.fill_structure(structure)
       └─ If NotMyFileError raised → FAILED_PRECONDITION status

gRPC GetValues(handle, group_id, channel_ids, start, limit)
  └─ ExternalDataReader.GetValues()
       └─ your_instance.get_values(request) → ValuesResult

gRPC Close(handle)
  └─ ExternalDataReader.Close()
       └─ Decrements ref count; calls your_instance.close() when count reaches 0
```

### File Caching and Reference Counting

`ExternalDataReader` caches opened files keyed by `(file_path, parameters)`. Multiple `Open` calls for the same file reuse the same handler instance and increment a reference counter. The handler is only closed when the last reference is released.

### Auto-Close Scheduler

When `--auto-close-interval` is set to a value greater than 0, a background thread periodically scans for file handles that have been idle longer than `--auto-close-idle` seconds and closes them automatically.

## Call Flow — `FileSimpleInterface`

The simple interface wraps the full interface. When you call `serve_plugin_simple()`:

```
serve_plugin_simple(name, factory, patterns)
  └─ FileSimpleRegistry.register(factory)           ← stores your factory
  └─ serve_plugin(name, FileSimple.create, patterns) ← registers FileSimple as the ExdFileInterface
```

At runtime, `FileSimple` acts as an adapter:

```
FileSimple.create(file_path, parameters)
  └─ Parses parameters string into dict (via ParamParser)
  └─ Creates FileSimpleCache(file_path, parsed_params)

FileSimple.fill_structure(structure)
  └─ FileSimpleCache lazily calls FileSimpleRegistry.create()
       └─ Your factory(file_path, params_dict) → FileSimpleInterface instance
  └─ Calls your_instance.not_my_file()
       └─ If True → raises NotMyFileError
  └─ Reads your_instance.data() → pd.DataFrame
  └─ Auto-maps DataFrame columns to ODS groups/channels:
       - Column names → channel names (or your column_names() override)
       - numpy dtypes → ODS DataTypeEnum
       - Column units/descriptions from your overrides
       - First column marked as independent if monotonic & unique
  └─ Populates protobuf StructureResult automatically

FileSimple.get_values(request)
  └─ Reads column slices from the cached DataFrame
  └─ Converts numpy arrays to protobuf value arrays
  └─ Handles all ODS data types (byte, short, long, float, double, string, date, complex)
```

### Key Design Insight

`FileSimpleInterface` users never touch protobuf. The `FileSimple` wrapper handles:
- Parameter parsing (string → dict via `ParamParser`)
- Data type mapping (numpy dtype → ODS `DataTypeEnum`)
- Structure generation (DataFrame → `StructureResult` protobuf)
- Value serialization (pandas Series → protobuf arrays)
- File rejection conversion (`not_my_file() → True` becomes `NotMyFileError`)

## Multi-Plugin Support

`FileHandlerRegistry` supports registering **multiple** file types in a single process. Each type is keyed by `file_type_name` and matched by `file_patterns` (glob-style, e.g. `*.tdms`).

When only one handler is registered, all files are routed to it regardless of extension. When multiple handlers exist, the registry matches the filename against patterns.

{: .note }
`FileSimpleInterface` only supports **one** plugin per process because `FileSimpleRegistry` stores a single factory. Use `ExdFileInterface` directly if you need multi-plugin support.
