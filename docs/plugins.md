---
title: Real-World Plugins
layout: default
nav_order: 8
---

# Real-World Plugins

These open-source plugins use `ods-exd-api-box` in production.

## asam_ods_exd_api_nptdms

**ASAM ODS EXD-API plugin for NI TDMS files**

| | |
|---|---|
| **Repository** | [github.com/totonga/asam_ods_exd_api_nptdms](https://github.com/totonga/asam_ods_exd_api_nptdms) |
| **Interface** | `ExdFileInterface` |
| **File format** | [NI TDMS](https://www.ni.com/en/support/documentation/supplemental/07/tdms-file-format-internal-structure.html) (Technical Data Management Streaming) |
| **Key dependency** | [npTDMS](https://pypi.org/project/npTDMS/) |
| **Docker image** | `ghcr.io/totonga/asam-ods-exd-api-nptdms` |

### Why `ExdFileInterface`?

TDMS files have a hierarchical structure with **multiple groups**, each containing channels with rich metadata (waveform parameters, scaling info, unit descriptions). The `ExdFileInterface` gives full control to map this multi-group structure and per-channel attributes into the `StructureResult` protobuf.

### Entry point pattern

```python
if __name__ == "__main__":
    from ods_exd_api_box import serve_plugin
    from external_data_nptdms import ExternalDataNpTdms

    serve_plugin(
        file_type_name="TDMS",
        file_type_factory=ExternalDataNpTdms.create,
        file_type_file_patterns=["*.tdms"],
    )
```

---

## asam_ods_exd_api_pandascsv

**ASAM ODS EXD-API plugin for CSV files**

| | |
|---|---|
| **Repository** | [github.com/totonga/asam_ods_exd_api_pandascsv](https://github.com/totonga/asam_ods_exd_api_pandascsv) |
| **Interface** | `FileSimpleInterface` |
| **File format** | CSV (Comma-Separated Values) |
| **Key dependency** | [pandas](https://pypi.org/project/pandas/) |
| **Docker image** | `ghcr.io/totonga/asam-ods-exd-api-pandascsv` |

### Why `FileSimpleInterface`?

CSV files are flat tables — a single group with uniform columns. Pandas reads them natively with `pd.read_csv()`, so `FileSimpleInterface` is the natural fit. Parameters like `delimiter`, `header`, and `encoding` are passed through to pandas automatically.

### Entry point pattern

```python
if __name__ == "__main__":
    from ods_exd_api_box.simple.file_simple import serve_plugin_simple
    from external_data_pandas_csv import ExternalDataPandasCsv

    serve_plugin_simple(
        file_type_name="CSV",
        file_type_factory=ExternalDataPandasCsv.create,
        file_type_file_patterns=["*.csv", "*.CSV"],
    )
```

---

## Building Your Own Plugin

Both plugins follow the same pattern:

1. **Create a class** implementing `ExdFileInterface` or `FileSimpleInterface`
2. **Add a `__main__` block** calling `serve_plugin()` or `serve_plugin_simple()`
3. **Create a Dockerfile** based on the [Docker guide](docker)
4. **Publish** the Docker image to a container registry

See [ExdFileInterface Guide](exd-file-interface) or [FileSimpleInterface Guide](file-simple-interface) for step-by-step instructions.
