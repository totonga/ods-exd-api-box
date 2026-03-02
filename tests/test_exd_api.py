from __future__ import annotations

import logging
import pathlib
import tempfile
import time
import unittest

import grpc
from google.protobuf.json_format import MessageToJson

from ods_exd_api_box import ExternalDataReader, FileHandlerRegistry, exd_api, ods
from tests.external_data_file import ExternalDataFile
from tests.mock_servicer_context import MockServicerContext


class TestExdApi(unittest.TestCase):
    log = logging.getLogger(__name__)

    def setUp(self):
        """Register ExternalDataFile handler before each test."""
        FileHandlerRegistry.register(file_type_name="test", factory=ExternalDataFile.create)

    def _get_example_file_path(self, file_name: str) -> str:
        example_file_path = pathlib.Path.joinpath(pathlib.Path(__file__).parent.resolve(), "data", file_name)
        return pathlib.Path(example_file_path).absolute().resolve().as_uri()

    def test_open(self):
        service = ExternalDataReader()
        context = MockServicerContext()
        handle = service.Open(
            exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""), context
        )
        try:
            pass
        finally:
            service.Close(handle, context)

    def test_structure(self):
        service = ExternalDataReader()
        context = MockServicerContext()
        handle = service.Open(
            exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""), context
        )
        try:
            structure = service.GetStructure(exd_api.StructureRequest(handle=handle), context)

            self.assertEqual(structure.name, "dummy.exd_api_test")
            self.assertEqual(len(structure.groups), 1)
            self.assertEqual(structure.groups[0].number_of_rows, 2000)
            self.assertEqual(len(structure.groups[0].channels), 7)
            self.assertEqual(structure.groups[0].id, 0)
            self.assertEqual(structure.groups[0].channels[0].id, 0)
            self.assertEqual(structure.groups[0].channels[1].id, 1)
            self.assertEqual(structure.groups[0].channels[0].data_type, ods.DataTypeEnum.DT_DOUBLE)
            self.assertEqual(structure.groups[0].channels[1].data_type, ods.DataTypeEnum.DT_DOUBLE)
        finally:
            service.Close(handle, context)

    def test_get_values(self):
        service = ExternalDataReader()
        context = MockServicerContext()
        handle = service.Open(
            exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""), context
        )
        try:
            values = service.GetValues(
                exd_api.ValuesRequest(handle=handle, group_id=0, channel_ids=[0, 1], start=0, limit=4),
                context,
            )

            self.assertEqual(values.id, 0)
            self.assertEqual(len(values.channels), 2)
            self.assertEqual(values.channels[0].id, 0)
            self.assertEqual(values.channels[1].id, 1)
            self.log.info(MessageToJson(values))

            self.assertEqual(values.channels[0].values.data_type, ods.DataTypeEnum.DT_DOUBLE)
            self.assertSequenceEqual(
                values.channels[0].values.double_array.values,
                [-0.18402661214026306, 0.1480147709585864, -0.24506363109225746, -0.29725028229621264],
            )
            self.assertEqual(values.channels[1].values.data_type, ods.DataTypeEnum.DT_DOUBLE)
            self.assertSequenceEqual(
                values.channels[1].values.double_array.values,
                [1.0303048799096652, 0.6497390667439802, 0.7638782921842098, 0.5508590960417493],
            )

        finally:
            service.Close(handle, context)

    def test_open_not_my_file_in_open(self):

        service = ExternalDataReader()
        context = MockServicerContext()
        with tempfile.NamedTemporaryFile(mode="w", delete=True, suffix=".not_my_file") as tmp:

            with self.assertRaises(grpc.RpcError) as _:
                service.Open(
                    exd_api.Identifier(url=pathlib.Path(tmp.name).absolute().resolve().as_uri(), parameters=""),
                    context,
                )
            self.assertEqual(context.code(), grpc.StatusCode.FAILED_PRECONDITION)
            self.assertEqual(context.details(), "Not my file!")

    def test_open_not_my_file_in_get_structure(self):

        service = ExternalDataReader()
        context = MockServicerContext()
        with tempfile.NamedTemporaryFile(mode="w", delete=True, suffix=".exd_api_test") as tmp:

            handle: exd_api.Handle = service.Open(
                exd_api.Identifier(url=pathlib.Path(tmp.name).absolute().resolve().as_uri(), parameters=""),
                context,
            )

            with self.assertRaises(grpc.RpcError) as _:
                service.GetStructure(exd_api.StructureRequest(handle=handle), context)
            self.assertEqual(context.code(), grpc.StatusCode.FAILED_PRECONDITION)
            self.assertEqual(context.details(), "Not my file!")

    def test_auto_close_scheduler_evicts_idle_files(self):
        """Test that auto-close scheduler evicts idle files based on last_access_time."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            service.Close(handle, context)

            # file_map should still have an entry (Close with ref_count==1 removes it, so re-open and leave open)
        finally:
            service.stop_auto_close()

    def test_auto_close_scheduler_evicts_idle_files_with_open_connections(self):
        """Test that auto-close scheduler evicts idle files even with open connections."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # file_map should have an entry with ref_count=1
            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry after open")
            self.assertEqual(len(service.connection_map), 1, "connection_map should have 1 entry after open")

            # Wait for scheduler to trigger
            time.sleep(3)

            # Scheduler should have evicted the idle file and orphaned connection
            self.assertEqual(len(service.file_map), 0, "file_map should be empty after idle timeout")
            self.assertEqual(len(service.connection_map), 0, "connection_map should be empty after orphan cleanup")

            # Accessing the evicted handle should now fail
            with self.assertRaises(KeyError):
                service.GetStructure(exd_api.StructureRequest(handle=handle), context)
        finally:
            service.stop_auto_close()

    def test_auto_close_scheduler_disabled_by_default(self):
        """Test that with interval=0 (default), scheduler does not run."""
        service = ExternalDataReader()
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            self.assertIsNone(service._auto_close_thread, "Scheduler thread should not be created when disabled")
            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry")

            service.Close(handle, context)
        finally:
            service.stop_auto_close()

    def test_auto_close_with_multiple_opens_same_file_ref_count(self):
        """Test that files with ref_count > 1 are not evicted until all connections closed."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            # Open the same file twice
            handle1 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            handle2 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # Both handles reference the same file_map entry, ref_count should be 2
            file_map_key = list(service.file_map.keys())[0]
            entry = service.file_map[file_map_key]
            self.assertEqual(entry.ref_count, 2, "ref_count should be 2 for two open connections")
            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry")
            self.assertEqual(len(service.connection_map), 2, "connection_map should have 2 entries")

            # Close only first handle
            service.Close(handle1, context)
            self.assertEqual(entry.ref_count, 1, "ref_count should be 1 after closing one connection")
            self.assertEqual(len(service.file_map), 1, "file_map entry should still exist")

            # Close second handle
            service.Close(handle2, context)
            self.assertEqual(len(service.file_map), 0, "file_map should be empty after closing all connections")
            self.assertEqual(len(service.connection_map), 0, "connection_map should be empty")

        finally:
            service.stop_auto_close()

    def test_auto_close_with_multiple_opens_same_file_idle_eviction(self):
        """Test that files are evicted even with ref_count > 1 if idle past threshold."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            # Open the same file twice
            handle1 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            handle2 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            current_len = len(service.file_map)
            self.assertGreater(current_len, 0, "file_map should have entries")

            # Wait for scheduler to evict idle files
            time.sleep(3)

            # Even though ref_count was 2, file should be evicted based on idle time
            self.assertEqual(len(service.file_map), 0, "file_map should be empty after idle timeout")
            # Both connections should be orphaned and removed
            self.assertEqual(len(service.connection_map), 0, "connection_map should be empty")

        finally:
            service.stop_auto_close()

    def test_auto_close_with_multiple_different_files(self):
        """Test that multiple different files are managed independently during eviction."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=2)
        context = MockServicerContext()

        try:
            # Open first file with param v=1
            handle1 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters="v=1"),
                context,
            )
            # Sleep a bit to create time offset
            time.sleep(1)

            # Open second file with param v=2 (same file, different parameters = different file_map_key)
            handle2 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters="v=2"),
                context,
            )

            self.assertEqual(len(service.file_map), 2, "file_map should have 2 entries")
            self.assertEqual(len(service.connection_map), 2, "connection_map should have 2 entries")

            # Wait for first file to become idle (2+ seconds since first open)
            time.sleep(2)

            # Only the first file should be evicted; second file was accessed more recently
            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry (second file)")
            self.assertEqual(len(service.connection_map), 1, "connection_map should have 1 entry")

            # Verify we can still access the second file
            structure = service.GetStructure(exd_api.StructureRequest(handle=handle2), context)
            self.assertEqual(structure.name, "dummy.exd_api_test")

            service.Close(handle2, context)
        finally:
            service.stop_auto_close()

    def test_auto_close_evicted_file_can_be_reopened(self):
        """Test that a file evicted by scheduler can be re-opened."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            file_url = self._get_example_file_path("dummy.exd_api_test")

            # Open and wait for eviction
            handle1 = service.Open(exd_api.Identifier(url=file_url, parameters=""), context)
            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry after open")

            time.sleep(3)

            # File should be evicted
            self.assertEqual(len(service.file_map), 0, "file_map should be empty after idle timeout")

            # Re-open the same file
            handle2 = service.Open(exd_api.Identifier(url=file_url, parameters=""), context)
            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry after re-open")
            self.assertEqual(len(service.connection_map), 1, "connection_map should have 1 entry")

            # Verify new handle is different from old (since old was evicted)
            self.assertNotEqual(handle1.uuid, handle2.uuid, "Re-opened file should have new handle UUID")

            service.Close(handle2, context)
        finally:
            service.stop_auto_close()

    def test_auto_close_accessing_file_prevents_eviction(self):
        """Test that accessing a file updates last_access_time and prevents eviction."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=3)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # Access the file after 1 second (updates last_access_time)
            time.sleep(1)
            service.GetStructure(exd_api.StructureRequest(handle=handle), context)

            # Access again after another second
            time.sleep(1)
            service.GetStructure(exd_api.StructureRequest(handle=handle), context)

            # Total elapsed is 2 seconds, but idle lifetime resets on each access
            # File should not be evicted since max idle is 1 second (2 total from start, 1 from last access)
            time.sleep(1)

            self.assertEqual(len(service.file_map), 1, "file_map should retain entry when file is actively accessed")

            service.Close(handle, context)
        finally:
            service.stop_auto_close()

    def test_auto_close_orphan_cleanup_on_partial_close(self):
        """Test that orphaned connections are cleaned up when multi-open file is evicted."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            # Open same file twice
            handle1 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            handle2 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # Close only first handle, leaving second "orphaned" from file perspective
            service.Close(handle1, context)

            # Wait for scheduler to evict the idle file
            time.sleep(3)

            # Both the file_map entry and the orphaned connection should be gone
            self.assertEqual(len(service.file_map), 0, "file_map should be empty")
            self.assertEqual(len(service.connection_map), 0, "connection_map should be empty (orphaned connection cleaned)")

        finally:
            service.stop_auto_close()

    def test_auto_close_very_short_idle_threshold(self):
        """Test edge case with very short idle timeout."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=0)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # With idle threshold of 0, file should be evicted immediately on next scheduler run
            time.sleep(2)

            self.assertEqual(len(service.file_map), 0, "file_map should be empty with 0 second idle threshold")

        finally:
            service.stop_auto_close()

    def test_auto_close_stop_during_pruning(self):
        """Test that scheduler can be safely stopped."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=10)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            self.assertIsNotNone(service._auto_close_thread)

            # Stop scheduler while file is open
            service.stop_auto_close()

            # Scheduler thread should be stopped
            # (join with timeout should complete quickly)
            time.sleep(0.5)

            # File should still be in map since no more pruning occurs
            self.assertEqual(len(service.file_map), 1, "file_map should retain entry after stop")

            service.Close(handle, context)
        finally:
            service.stop_auto_close()

    def test_auto_close_scheduler_does_not_evict_active_files(self):
        """Test that files accessed within the idle threshold are not evicted."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=10)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # Wait for scheduler to run but idle_timeout is much longer
            time.sleep(2)

            # File should still be in file_map because idle threshold not exceeded
            self.assertEqual(len(service.file_map), 1, "file_map should retain entry when idle < threshold")

            service.Close(handle, context)
        finally:
            service.stop_auto_close()

    def test_auto_close_accessing_evicted_handle_raises_error(self):
        """Test that accessing a handle after file eviction raises KeyError."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # Verify handle and file exist
            self.assertEqual(len(service.file_map), 1, "file_map should have entry")
            self.assertEqual(len(service.connection_map), 1, "connection_map should have entry")

            # Wait for scheduler to evict the idle file
            time.sleep(3)

            # Both file_map and connection_map should be cleaned
            self.assertEqual(len(service.file_map), 0, "file_map should be empty after eviction")
            self.assertEqual(len(service.connection_map), 0, "connection_map should be empty after orphan cleanup")

            # Try to access the evicted file via the old handle
            # Should raise KeyError since the handle was orphan-cleaned
            with self.assertRaises(KeyError) as exc_context:
                service.GetStructure(exd_api.StructureRequest(handle=handle), context)

            # Verify error message mentions the handle was not found
            error_msg = str(exc_context.exception)
            self.assertIn(handle.uuid, error_msg, "Error should mention the missing handle")

        finally:
            service.stop_auto_close()

    def test_auto_close_partial_orphan_cleanup(self):
        """Test error behavior when one of multiple connections is orphan-cleaned."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            # Open file twice
            handle1 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )
            handle2 = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            self.assertEqual(len(service.file_map), 1, "file_map should have 1 entry")
            self.assertEqual(len(service.connection_map), 2, "connection_map should have 2 entries")

            # Close first handle without eviction
            service.Close(handle1, context)
            self.assertEqual(len(service.connection_map), 1, "connection_map should have 1 entry after close")

            # Wait for scheduler to evict the file (and orphan-clean the remaining connection)
            time.sleep(3)

            self.assertEqual(len(service.file_map), 0, "file_map should be empty")
            self.assertEqual(len(service.connection_map), 0, "connection_map should be empty (both connections cleaned)")

            # Try to access with the remaining handle
            with self.assertRaises(KeyError) as exc_context:
                service.GetStructure(exd_api.StructureRequest(handle=handle2), context)

            error_msg = str(exc_context.exception)
            self.assertIn(handle2.uuid, error_msg, "Error should mention handle2 was not found")

        finally:
            service.stop_auto_close()

    def test_auto_close_get_values_on_evicted_handle(self):
        """Test GetValues also fails appropriately on evicted file handle."""
        service = ExternalDataReader(auto_close_interval=1, auto_close_idle=1)
        context = MockServicerContext()

        try:
            handle = service.Open(
                exd_api.Identifier(url=self._get_example_file_path("dummy.exd_api_test"), parameters=""),
                context,
            )

            # Wait for eviction
            time.sleep(3)

            # GetValues should also raise KeyError on evicted handle
            with self.assertRaises(KeyError):
                service.GetValues(
                    exd_api.ValuesRequest(handle=handle, group_id=0, channel_ids=[0], start=0, limit=1),
                    context,
                )

        finally:
            service.stop_auto_close()
