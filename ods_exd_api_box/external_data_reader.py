"""EXD API implementation"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import override
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

import grpc

from . import ExdFileInterface, FileHandlerRegistry, NotMyFileError, exd_api, exd_grpc

# pylint: disable=invalid-name


@dataclass
class FileMapEntry:
    """Entry in the file map."""

    file: ExdFileInterface | None
    ref_count: int = 0
    last_access_time: float = field(default_factory=time.time)


class ExternalDataReader(exd_grpc.ExternalDataReaderServicer):
    """ASAM ODS EXD API implementation."""

    log = logging.getLogger(__name__)

    @override
    def Open(self, request: exd_api.Identifier, context: grpc.ServicerContext) -> exd_api.Handle:
        """Open a connection to an external data file."""
        self.log.info("Open request for URL '%s'", request.url)

        file_path = Path(ExternalDataReader.__get_path(request.url))
        if not file_path.is_file():
            self.log.error("File not found: '%s' (resolved path: '%s')", request.url, file_path)
            context.abort(grpc.StatusCode.NOT_FOUND, f"File '{request.url}' not found.")

        try:
            connection_id = self.__open_file(request)
            self.log.info("Successfully opened file '%s' with connection ID '%s'", request.url, connection_id)

            return exd_api.Handle(uuid=connection_id)
        except NotMyFileError:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Not my file!")
            raise  # for type checker

    @override
    def Close(
        self, request: exd_api.Handle, context: grpc.ServicerContext  # pylint: disable=unused-argument
    ) -> exd_api.Empty:  # pylint: disable=unused-argument
        """Close the connection to an external data file."""
        self.log.info("Close request for handle '%s'", request.uuid)

        self.__close_file(request)
        self.log.info("Successfully closed connection '%s'", request.uuid)
        return exd_api.Empty()

    @override
    def GetStructure(
        self, request: exd_api.StructureRequest, context: grpc.ServicerContext
    ) -> exd_api.StructureResult:
        """Get the structure of the external data file."""
        self.log.debug("GetStructure request for handle '%s'", request.handle.uuid)

        if request.suppress_channels or request.suppress_attributes or 0 != len(request.channel_names):
            self.log.error(
                "GetStructure: Unsupported options "
                "(suppress_channels=%s, suppress_attributes=%s, channel_names=%s)",
                request.suppress_channels,
                request.suppress_attributes,
                request.channel_names,
            )
            context.abort(grpc.StatusCode.UNIMPLEMENTED, "Method not implemented!")

        file, identifier = self.__get_file(request.handle)

        self.log.debug("Retrieved file handler for handle '%s'", request.handle.uuid)

        rv = exd_api.StructureResult(identifier=identifier)
        rv.name = Path(identifier.url).name
        self.log.debug("Filling structure for file '%s'", rv.name)

        try:
            file.fill_structure(rv)
            self.log.debug("Structure filled successfully for handle '%s'", request.handle.uuid)

            return rv
        except NotMyFileError:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, "Not my file!")
            raise  # for type checker

    @override
    def GetValues(self, request: exd_api.ValuesRequest, context: grpc.ServicerContext) -> exd_api.ValuesResult:
        """Get values from the external data file."""
        self.log.debug(
            "GetValues request for handle '%s', channels: %s", request.handle.uuid, len(request.channel_ids)
        )

        file, _ = self.__get_file(request.handle)

        self.log.debug("Retrieving values for handle '%s'", request.handle.uuid)
        result = file.get_values(request)
        self.log.debug("Successfully retrieved values for handle '%s'", request.handle.uuid)
        return result

    @override
    def GetValuesEx(self, request: exd_api.ValuesExRequest, context: grpc.ServicerContext) -> exd_api.ValuesExResult:
        """Get values from the external data file with extended options."""

        context.abort(
            grpc.StatusCode.UNIMPLEMENTED, f"Method not implemented! request. Names: {request.channel_names}"
        )
        return exd_api.ValuesExResult()  # never reached

    def __init__(self, auto_close_interval: int = 0, auto_close_idle: int = 300) -> None:
        self.connect_count: int = 0
        self.connection_map: dict[str, exd_api.Identifier] = {}
        self.file_map: dict[tuple[str, str | None], FileMapEntry] = {}
        self.lock: threading.Lock = threading.Lock()
        self.auto_close_interval: int = auto_close_interval
        self.auto_close_idle: int = auto_close_idle
        self._stop_event = threading.Event()
        self._auto_close_thread: threading.Thread | None = None
        if auto_close_interval > 0:
            self._auto_close_thread = threading.Thread(target=self._auto_close_loop, daemon=True)
            self._auto_close_thread.start()
            self.log.info(
                "Auto-close scheduler started (interval=%ds, idle_timeout=%ds)",
                auto_close_interval,
                auto_close_idle,
            )
        else:
            self.log.debug("Auto-close scheduler disabled")

    def __get_id(self, identifier: exd_api.Identifier) -> str:
        self.connect_count += 1
        rv = str(self.connect_count)
        self.connection_map[rv] = identifier
        return rv

    @staticmethod
    def __uri_to_path(uri: str) -> str:
        parsed = urlparse(uri)
        host = f"{os.path.sep}{os.path.sep}{parsed.netloc}{os.path.sep}"
        return os.path.normpath(os.path.join(host, url2pathname(unquote(parsed.path))))

    @staticmethod
    def __get_path(file_url: str) -> str:
        return ExternalDataReader.__uri_to_path(file_url)

    def __get_file_map_key(self, identifier: exd_api.Identifier) -> tuple[str, tuple[str, str | None]]:
        """Create a composite key from identifier URL and parameters, returning both URL and key."""
        file_path = ExternalDataReader.__get_path(identifier.url)
        file_map_key = (file_path, identifier.parameters)
        return (file_path, file_map_key)

    def __open_file(self, identifier: exd_api.Identifier) -> str:
        with self.lock:
            connection_id = self.__get_id(identifier)
            file_path, file_map_key = self.__get_file_map_key(identifier)
            if file_map_key not in self.file_map:
                self.log.info("Opening external data file '%s' as connection id '%s'.", file_path, connection_id)
                file_handle = FileHandlerRegistry.create_from_path(file_path, identifier.parameters)
                self.file_map[file_map_key] = FileMapEntry(file=file_handle, ref_count=0)
                self.log.debug("File handler created and added to file_map")
            else:
                self.log.debug(
                    "File '%s' already in file_map, reusing existing handler for connection id '%s'",
                    file_path, connection_id)
            self.file_map[file_map_key].ref_count += 1
            self.log.debug(
                "Incremented ref_count for '%s' to %s",
                file_path,
                self.file_map[file_map_key].ref_count,
            )
            return connection_id

    def __get_file(self, handle: exd_api.Handle) -> tuple[ExdFileInterface, exd_api.Identifier]:
        identifier = self.connection_map.get(handle.uuid)
        if identifier is None:
            self.log.error("Handle '%s' not found in connection_map", handle.uuid)
            raise KeyError(f"Handle '{handle.uuid}' not found.")
        file_path, file_map_key = self.__get_file_map_key(identifier)
        entry = self.file_map.get(file_map_key)
        if entry is None:
            self.log.error("Connection URL '%s' not found in file_map for handle '%s'", file_path, handle.uuid)
            raise KeyError(f"Connection URL '{file_path}' not found.")
        entry.last_access_time = time.time()
        self.log.debug("Updated last_access_time for handle '%s' (file: '%s')", handle.uuid, file_path)
        if entry.file is None:
            self.log.error("File handler is None for handle '%s' (file: '%s')", handle.uuid, file_path)
            raise KeyError(f"File handler is None for handle '{handle.uuid}'.")
        return entry.file, identifier

    def __close_file(self, handle: exd_api.Handle) -> None:
        with self.lock:
            identifier = self.connection_map.get(handle.uuid)
            if identifier is None:
                self.log.error("Handle '%s' not found in connection_map for close", handle.uuid)
                raise KeyError(f"Handle '{handle.uuid}' not found for close.")
            file_path, file_map_key = self.__get_file_map_key(identifier)
            self.connection_map.pop(handle.uuid)
            self.log.debug("Removed handle '%s' from connection_map", handle.uuid)
            entry = self.file_map.get(file_map_key)
            if entry is None:
                self.log.error("Connection URL '%s' not found in file_map for close", file_path)
                raise KeyError(f"Connection URL '{file_path}' not found for close.")
            if entry.ref_count > 1:
                entry.ref_count -= 1
                self.log.debug("Decremented ref_count for '%s' to %s", file_path, entry.ref_count)
            else:
                self.log.info("Closing file '%s' (ref_count reached 0)", file_path)
                if entry.file is not None:
                    entry.file.close()
                    self.log.debug("File handler closed for '%s'", file_path)
                self.file_map.pop(file_map_key)
                self.log.debug("File removed from file_map: '%s'", file_path)

    def _prune_idle_files(self) -> None:
        """Remove idle file entries from file_map if they exceed idle timeout.

        This method is thread-safe (acquires self.lock) and logs all cleanup operations.
        Cleanup is based solely on last_access_time, not ref_count.
        """
        with self.lock:
            current_time = time.time()
            keys_to_remove: list[tuple[str, str | None]] = []

            for file_map_key, entry in self.file_map.items():
                idle_duration = current_time - entry.last_access_time
                if idle_duration >= self.auto_close_idle:
                    file_path = file_map_key[0]
                    self.log.info(
                        "Auto-closing idle file '%s' (idle: %.1fs, threshold: %ds, ref_count: %d)",
                        file_path,
                        idle_duration,
                        self.auto_close_idle,
                        entry.ref_count,
                    )
                    if entry.file is not None:
                        try:
                            entry.file.close()
                            self.log.debug("File handler closed for '%s'", file_path)
                        except Exception:
                            self.log.exception("Error closing file '%s'", file_path)
                    keys_to_remove.append(file_map_key)

            removed_count = 0
            for key in keys_to_remove:
                self.file_map.pop(key, None)
                self.log.info("Removed idle file from file_map: '%s'", key[0])
                removed_count += 1

            orphaned_count = 0
            connection_keys_to_remove: list[str] = []
            for conn_id, identifier in self.connection_map.items():
                _, fmk = self.__get_file_map_key(identifier)
                if fmk not in self.file_map:
                    file_path = fmk[0]
                    self.log.warning(
                        "Removing orphaned connection '%s' (file '%s' was evicted from file_map)",
                        conn_id,
                        file_path,
                    )
                    connection_keys_to_remove.append(conn_id)
                    orphaned_count += 1

            for conn_id in connection_keys_to_remove:
                self.connection_map.pop(conn_id, None)

            if removed_count > 0 or orphaned_count > 0:
                self.log.info(
                    "Pruning complete: removed %d file_map entries, cleaned %d orphaned connections",
                    removed_count,
                    orphaned_count,
                )

    def _auto_close_loop(self) -> None:
        """Background loop for periodic file idle timeout checks.

        Runs until _stop_event is set. Calls _prune_idle_files() at each interval.
        """
        self.log.info("Auto-close scheduler loop started")
        try:
            while not self._stop_event.wait(self.auto_close_interval):
                self.log.debug(
                    "Auto-close check: file_map=%d entries, connection_map=%d entries",
                    len(self.file_map),
                    len(self.connection_map),
                )
                try:
                    self._prune_idle_files()
                except Exception:
                    self.log.exception("Exception during auto-close pruning")
        finally:
            self.log.info("Auto-close scheduler loop stopped")

    def stop_auto_close(self) -> None:
        """Stop the auto-close scheduler gracefully.

        Safe to call even if scheduler is not running.
        """
        self._stop_event.set()
        if self._auto_close_thread is not None:
            self.log.info("Stopping auto-close scheduler")
            self._auto_close_thread.join(timeout=5)
            self._auto_close_thread = None
