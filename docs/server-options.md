---
title: Server Options
layout: default
nav_order: 6
---

# Server Options

Both `serve_plugin()` and `serve_plugin_simple()` use the same server configuration. Options can be provided via CLI arguments or environment variables.

## Configuration Priority

Values are resolved in this order (highest to lowest):
1. **Command line arguments**
2. **Environment variables**
3. **Default values**

## Options Reference

```bash
python your_plugin.py --help
```

| CLI Option | Environment Variable | Default | Description |
|---|---|---|---|
| `--port` | `ODS_EXD_API_PORT` | `50051` | Port to run the gRPC server on |
| `--bind-address` | `ODS_EXD_API_BIND_ADDRESS` | `[::]` | Address to bind the gRPC server to |
| `--max-workers` | `ODS_EXD_API_MAX_WORKERS` | `2 × CPU count` | Maximum number of worker threads |
| `--max-concurrent-streams` | `ODS_EXD_API_MAX_CONCURRENT_STREAMS` | `None` | Maximum concurrent gRPC streams |
| `--max-send-message-length` | `ODS_EXD_API_MAX_SEND_MESSAGE_LENGTH` | `512` | Max send message length in MB |
| `--max-receive-message-length` | `ODS_EXD_API_MAX_RECEIVE_MESSAGE_LENGTH` | `32` | Max receive message length in MB |
| `--verbose` | `ODS_EXD_API_VERBOSE` | `False` | Enable DEBUG-level logging |
| `--auto-close-interval` | `ODS_EXD_API_AUTO_CLOSE_INTERVAL` | `0` (disabled) | Interval in seconds for the auto-close scheduler |
| `--auto-close-idle` | `ODS_EXD_API_AUTO_CLOSE_IDLE` | `900` | Idle timeout in seconds before auto-closing files |

### TLS Options

| CLI Option | Environment Variable | Default | Description |
|---|---|---|---|
| `--use-tls` | `ODS_EXD_API_USE_TLS` | `False` | Enable TLS/SSL |
| `--tls-cert-file` | `ODS_EXD_API_TLS_CERT_FILE` | — | Path to PEM-encoded server certificate |
| `--tls-key-file` | `ODS_EXD_API_TLS_KEY_FILE` | — | Path to PEM-encoded server private key |
| `--tls-client-ca-file` | `ODS_EXD_API_TLS_CLIENT_CA_FILE` | — | CA bundle for client certificate verification |
| `--require-client-cert` | `ODS_EXD_API_REQUIRE_CLIENT_CERT` | `False` | Require a valid client certificate (mTLS) |

### Health Check Options

| CLI Option | Environment Variable | Default | Description |
|---|---|---|---|
| `--health-check-enabled` | `ODS_EXD_API_HEALTH_CHECK_ENABLED` | `False` | Enable an insecure health check service |
| `--health-check-bind-address` | `ODS_EXD_API_HEALTH_CHECK_BIND_ADDRESS` | `[::]` | Address to bind the health check service to |
| `--health-check-port` | `ODS_EXD_API_HEALTH_CHECK_PORT` | `50052` | Port for the health check service |

## `--env-prefix` — Multi-Instance Deployments

By default, all environment variables use the prefix `ODS_EXD_API_`. The `--env-prefix` option changes which prefix is read:

```bash
# Instance A reads MY_A_PORT, MY_A_VERBOSE, etc.
python plugin.py --env-prefix MY_A_

# Instance B reads MY_B_PORT, MY_B_VERBOSE, etc.
python plugin.py --env-prefix MY_B_
```

This lets you run multiple plugin instances on the same host with separate environment configurations.

{: .note }
`--env-prefix` is parsed *before* all other arguments. The prefix affects which environment variable names are checked for every subsequent option.

## TLS Configuration Examples

### Basic TLS

```bash
python your_plugin.py \
    --use-tls \
    --tls-cert-file /path/to/server.crt \
    --tls-key-file /path/to/server.key
```

### Mutual TLS (mTLS)

```bash
python your_plugin.py \
    --use-tls \
    --tls-cert-file /path/to/server.crt \
    --tls-key-file /path/to/server.key \
    --tls-client-ca-file /path/to/client-ca.crt \
    --require-client-cert
```

### TLS via Environment Variables

```bash
export ODS_EXD_API_USE_TLS=true
export ODS_EXD_API_TLS_CERT_FILE=/path/to/server.crt
export ODS_EXD_API_TLS_KEY_FILE=/path/to/server.key
python your_plugin.py
```

## Auto-Close Scheduler

When dealing with many files, you can enable the auto-close scheduler to release idle file handles:

```bash
python your_plugin.py \
    --auto-close-interval 60 \
    --auto-close-idle 300
```

This checks every 60 seconds and closes any file handle that has been idle for more than 300 seconds.

Set `--auto-close-interval 0` (the default) to disable the scheduler entirely.

## Health Check Service

The health check runs on a **separate insecure port** (even when the main service uses TLS). This is designed for container orchestrators like Kubernetes or Docker health checks:

```bash
python your_plugin.py \
    --health-check-enabled \
    --health-check-port 50052
```

The service implements the standard [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md) and reports the `asam.ods.ExternalDataReader` service as `SERVING`.

## Validation Rules

The server enforces these constraints at startup:
- `--require-client-cert` requires `--use-tls`
- `--tls-client-ca-file` requires `--use-tls`
- `--use-tls` requires both `--tls-cert-file` and `--tls-key-file`

Violations produce a clear error message and exit immediately.
