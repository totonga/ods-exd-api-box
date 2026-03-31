---
title: Docker Deployment
layout: default
nav_order: 7
---

# Docker Deployment

EXD-API plugins are typically deployed as Docker images. This page shows real-world Dockerfiles from production plugins.

## ExdFileInterface Plugin (nptdms)

From [asam_ods_exd_api_nptdms](https://github.com/totonga/asam_ods_exd_api_nptdms):

```dockerfile
# docker build -t ghcr.io/totonga/asam-ods-exd-api-nptdms:latest .
# docker run --rm -it -v "$(pwd)/data":"$(pwd)/data" -p 50051:50051 ghcr.io/totonga/asam-ods-exd-api-nptdms:latest
FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/totonga/asam_ods_exd_api_nptdms
LABEL org.opencontainers.image.description="ASAM ODS External Data API for NI TDMS files (*.tdms)"
LABEL org.opencontainers.image.licenses=MIT
WORKDIR /app
# Create a non-root user and change ownership of /app
RUN useradd -ms /bin/bash appuser && chown -R appuser /app

# Copy source code first (needed for pip install)
COPY pyproject.toml .
# Install required packages
RUN pip3 install --upgrade pip && pip3 install .

COPY external_data_file.py ./

USER appuser
# Start server
CMD [ "python3", "external_data_file.py"]
```

## FileSimpleInterface Plugin (pandascsv)

From [asam_ods_exd_api_pandascsv](https://github.com/totonga/asam_ods_exd_api_pandascsv):

```dockerfile
# docker build -t ghcr.io/totonga/asam-ods-exd-api-pandascsv:latest .
# docker run --rm -it -v "$(pwd)/data":"$(pwd)/data" -p 50051:50051 ghcr.io/totonga/asam-ods-exd-api-pandascsv:latest
FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/totonga/asam_ods_exd_api_pandascsv
LABEL org.opencontainers.image.description="ASAM ODS External Data API for CSV files (*.csv)"
LABEL org.opencontainers.image.licenses=MIT
WORKDIR /app
# Create a non-root user and change ownership of /app
RUN useradd -ms /bin/bash appuser && chown -R appuser /app

# Copy source code first (needed for pip install)
COPY pyproject.toml .
# Install required packages
RUN pip3 install --upgrade pip && pip3 install .

COPY external_file_data.py ./

USER appuser
# Start server
CMD [ "python3", "external_file_data.py"]
```

## Dockerfile Structure

Both plugins follow the same pattern:

| Step | Purpose |
|---|---|
| `FROM python:3.12-slim` | Minimal Python base image |
| `LABEL org.opencontainers.image.*` | OCI metadata for container registries (source, description, license) |
| `WORKDIR /app` | Set working directory |
| `RUN useradd ...` | Create a non-root user for security |
| `COPY pyproject.toml` | Copy project definition (declares `ods-exd-api-box` as a PyPI dependency) |
| `RUN pip3 install .` | Install the plugin and all dependencies from PyPI |
| `COPY external_data_file.py` | Copy the plugin entry point script |
| `USER appuser` | Switch to non-root user |
| `CMD [...]` | Start the gRPC server |

{: .important }
The plugin's `pyproject.toml` declares `ods-exd-api-box` (or `ods-exd-api-box[simple]`) as a dependency.
`pip install .` pulls everything from PyPI — the library source is **not** copied into the image.

{: .note }
The build/run commands at the top of each Dockerfile use `ghcr.io/<owner>/<plugin-name>:latest` as the image name,
following the convention for GitHub Container Registry.

## Building and Running

```bash
# Build the image
docker build -t ghcr.io/myorg/my-exd-plugin:latest .

# Run (expose gRPC port, mount data directory)
docker run --rm -it \
    -v "$(pwd)/data":"$(pwd)/data" \
    -p 50051:50051 \
    ghcr.io/myorg/my-exd-plugin:latest

# Run with custom options
docker run --rm -it \
    -p 8080:8080 \
    ghcr.io/myorg/my-exd-plugin:latest \
    python3 external_data_file.py --port 8080 --verbose
```

{: .note }
The data volume mount `-v "$(pwd)/data":"$(pwd)/data"` maps the host path identically into the container.
This is important because the ODS server passes file paths as URLs (e.g., `file:///home/user/data/measurement.tdms`)
and these paths must resolve identically inside the container.

## Mounting Data Files

The ODS server references files using URL paths that must resolve inside the container.
The convention is to mirror the host path inside the container:

```bash
docker run --rm -it \
    -v "$(pwd)/data":"$(pwd)/data" \
    -p 50051:50051 \
    ghcr.io/myorg/my-exd-plugin:latest
```

Alternatively, mount to a fixed path:

```bash
docker run --rm -it \
    -p 50051:50051 \
    -v /path/to/data:/data:ro \
    ghcr.io/myorg/my-exd-plugin:latest
```

## TLS with Docker

Mount your certificates as a volume:

```bash
docker run --rm -it \
    -p 50051:50051 \
    -v /path/to/certs:/certs:ro \
    -v "$(pwd)/data":"$(pwd)/data" \
    ghcr.io/myorg/my-exd-plugin:latest \
    python3 external_data_file.py \
        --use-tls \
        --tls-cert-file /certs/server.crt \
        --tls-key-file /certs/server.key
```

Mutual TLS:

```bash
docker run --rm -it \
    -p 50051:50051 \
    -v /path/to/certs:/certs:ro \
    -v "$(pwd)/data":"$(pwd)/data" \
    ghcr.io/myorg/my-exd-plugin:latest \
    python3 external_data_file.py \
        --use-tls \
        --tls-cert-file /certs/server.crt \
        --tls-key-file /certs/server.key \
        --tls-client-ca-file /certs/client-ca.crt \
        --require-client-cert
```

## Using Environment Variables

Environment variables are often more convenient in container orchestration:

```bash
docker run --rm -it \
    -p 50051:50051 \
    -v "$(pwd)/data":"$(pwd)/data" \
    -e ODS_EXD_API_PORT=50051 \
    -e ODS_EXD_API_VERBOSE=true \
    -e ODS_EXD_API_AUTO_CLOSE_INTERVAL=60 \
    -e ODS_EXD_API_AUTO_CLOSE_IDLE=300 \
    ghcr.io/myorg/my-exd-plugin:latest
```

## Health Checks

Enable the health check service for container orchestrators:

```bash
docker run --rm -it \
    -p 50051:50051 \
    -p 50052:50052 \
    -v "$(pwd)/data":"$(pwd)/data" \
    -e ODS_EXD_API_HEALTH_CHECK_ENABLED=true \
    ghcr.io/myorg/my-exd-plugin:latest
```

### Docker health check directive

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import grpc; ch=grpc.insecure_channel('localhost:50052'); grpc.channel_ready_future(ch).result(timeout=3)" || exit 1
```

### Docker Compose

```yaml
services:
  exd-plugin:
    image: ghcr.io/myorg/my-exd-plugin:latest
    # or build from source:
    # build: .
    ports:
      - "50051:50051"
      - "50052:50052"
    environment:
      ODS_EXD_API_HEALTH_CHECK_ENABLED: "true"
      ODS_EXD_API_VERBOSE: "true"
    volumes:
      - ./data:./data
    healthcheck:
      test: ["CMD", "python3", "-c",
        "import grpc; ch=grpc.insecure_channel('localhost:50052'); grpc.channel_ready_future(ch).result(timeout=3)"]
      interval: 30s
      timeout: 5s
      start_period: 10s
      retries: 3
```

## Production Tips

- **Non-root user** — Always run as a non-root user (the example Dockerfile does this).
- **Read-only volumes** — Mount data and certificate volumes as `:ro`.
- **`.dockerignore`** — Exclude `tests/`, `.venv/`, `*.egg-info/`, `.git/` to keep images small.
- **Multi-stage builds** — For large dependencies, use a build stage to install packages and copy only the runtime into the final image.
- **Pinning** — Pin your base image and dependency versions for reproducible builds.
