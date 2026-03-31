---
title: Choosing an Interface
layout: default
nav_order: 3
---

# Choosing an Interface

`ods-exd-api-box` offers two abstract base classes for building EXD-API plugins. Pick the one that fits your needs.

## Comparison

| Aspect | `ExdFileInterface` | `FileSimpleInterface` |
|---|---|---|
| **Module** | `ods_exd_api_box` | `ods_exd_api_box.simple` |
| **Install** | `pip install ods-exd-api-box` | `pip install 'ods-exd-api-box[simple]'` |
| **Extra dependency** | — | `pandas >=2.0` |
| **Protobuf knowledge** | Required | Not required |
| **Methods to implement** | `create`, `close`, `fill_structure`, `get_values` | `create`, `close`, `data` (+ optional hooks) |
| **Data format** | Protobuf messages directly | `pd.DataFrame` |
| **Structure control** | You build the `StructureResult` protobuf yourself | Auto-generated from DataFrame columns |
| **Value serialization** | You fill `ValuesResult` protobuf yourself | Automatic numpy → protobuf conversion |
| **File rejection** | Raise `NotMyFileError` from `create()` or `fill_structure()` | Return `True` from `not_my_file()` |
| **Multiple plugins per process** | Yes (via `FileHandlerRegistry`) | No (single factory in `FileSimpleRegistry`) |
| **Multiple groups** | Yes (you define the structure) | No (always one group named "data") |
| **Custom attributes per channel** | Yes (full protobuf control) | Limited (unit, description, independent flag) |
| **Entry point** | `serve_plugin()` | `serve_plugin_simple()` |
| **Example** | `tests/external_data_file.py` | `tests/simple/file_simple_example.py` |

## When to use `ExdFileInterface`

- Your file format has **multiple groups** (e.g., TDMS groups)
- You need **fine-grained control** over channel attributes and metadata
- You want to register **multiple file types** in one service
- You are comfortable working with protobuf messages
- Performance-critical scenarios where you want to avoid the pandas overhead

## When to use `FileSimpleInterface`

- Your data naturally fits a **single table** (CSV, Excel, Parquet, …)
- You already use **pandas** to read the file
- You want the **fastest path** from file to working EXD-API plugin
- You don't need custom per-channel attributes beyond name, unit, and description

## How they relate internally

`FileSimpleInterface` is not a separate gRPC implementation. Under the hood, `serve_plugin_simple()` wraps your `FileSimpleInterface` factory inside a `FileSimple` class that implements `ExdFileInterface`, then delegates to the same `serve_plugin()` function. See [Architecture](architecture) for the full call flow.
