import pathlib
import socket
import subprocess
import time
import unittest

import grpc

from ods_exd_api_box import exd_api, exd_grpc, ods

# pylint: disable=no-member


class TestDockerContainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # build Docker-Image
        result = subprocess.run(
            ["docker", "build", "-f", "tests/simple/Dockerfile_simple.test", "-t", "test_container", "."],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Docker build failed: {result.stderr}")

        # Clean up any existing test container from previous runs
        subprocess.run(
            ["docker", "stop", "test_container"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        subprocess.run(
            ["docker", "rm", "test_container"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )

        example_file_path = pathlib.Path.joinpath(pathlib.Path(__file__).parent.resolve(), "..", "data")
        data_folder = pathlib.Path(example_file_path).absolute().resolve()
        cp = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--name",
                "test_container",
                "-p",
                "50051:50051",
                "-v",
                f"{data_folder}:/data",
                "test_container",
            ],
            stdout=subprocess.PIPE,
            check=True,
        )
        cls.container_id = cp.stdout.decode().strip()
        cls.__wait_for_port_ready()

    @classmethod
    def tearDownClass(cls):
        # stop container
        subprocess.run(["docker", "stop", "test_container"], check=True)

    @classmethod
    def __wait_for_port_ready(cls, host="localhost", port=50051, timeout=30):
        start_time = time.time()
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return
            if time.time() - start_time > timeout:
                raise TimeoutError("Port did not become ready in time.")
            time.sleep(0.5)

    def test_container_health(self):
        channel = grpc.insecure_channel("localhost:50051")
        stub = exd_grpc.ExternalDataReaderStub(channel)
        self.assertIsNotNone(stub)
        grpc.channel_ready_future(channel).result(timeout=5)

    def test_structure(self):
        with grpc.insecure_channel("localhost:50051") as channel:
            grpc.channel_ready_future(channel).result(timeout=5)
            service = exd_grpc.ExternalDataReaderStub(channel)

            handle = service.Open(exd_api.Identifier(url="/data/dummy.exd_api_test", parameters=""), None)
            try:
                structure = service.GetStructure(exd_api.StructureRequest(handle=handle), None)

                self.assertEqual(structure.name, "dummy.exd_api_test")
                self.assertEqual(len(structure.groups), 1)
                self.assertEqual(structure.groups[0].number_of_rows, 3)
                self.assertEqual(len(structure.groups[0].channels), 14)
                self.assertEqual(structure.groups[0].id, 0)

                # Check various channel data types
                channels = structure.groups[0].channels
                self.assertEqual(channels[0].name, "byte_col")
                self.assertEqual(channels[0].data_type, ods.DataTypeEnum.DT_BYTE)
                self.assertEqual(channels[1].name, "short_int8")
                self.assertEqual(channels[1].data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertEqual(channels[4].name, "long_int32")
                self.assertEqual(channels[4].data_type, ods.DataTypeEnum.DT_LONG)
                self.assertEqual(channels[6].name, "longlong_int64")
                self.assertEqual(channels[6].data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertEqual(channels[8].name, "float_col")
                self.assertEqual(channels[8].data_type, ods.DataTypeEnum.DT_FLOAT)
                self.assertEqual(channels[9].name, "double_col")
                self.assertEqual(channels[9].data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertEqual(channels[10].name, "string_col")
                self.assertEqual(channels[10].data_type, ods.DataTypeEnum.DT_STRING)
                self.assertEqual(channels[11].name, "date_col")
                self.assertEqual(channels[11].data_type, ods.DataTypeEnum.DT_DATE)
                self.assertEqual(channels[12].name, "complex_col")
                self.assertEqual(channels[12].data_type, ods.DataTypeEnum.DT_COMPLEX)
                self.assertEqual(channels[13].name, "dcomplex_col")
                self.assertEqual(channels[13].data_type, ods.DataTypeEnum.DT_DCOMPLEX)
            finally:
                service.Close(handle, None)

    def test_get_values(self):
        with grpc.insecure_channel("localhost:50051") as channel:
            grpc.channel_ready_future(channel).result(timeout=5)
            service = exd_grpc.ExternalDataReaderStub(channel)

            handle = service.Open(exd_api.Identifier(url="/data/dummy.exd_api_test", parameters=""), None)

            try:
                values = service.GetValues(
                    exd_api.ValuesRequest(
                        handle=handle,
                        group_id=0,
                        channel_ids=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
                        start=0,
                        limit=3,
                    ),
                    None,
                )
                self.assertEqual(values.id, 0)
                self.assertEqual(len(values.channels), 14)

                # Channel 0: byte_col (DT_BYTE)
                self.assertEqual(values.channels[0].id, 0)
                self.assertEqual(values.channels[0].values.data_type, ods.DataTypeEnum.DT_BYTE)
                self.assertEqual(values.channels[0].values.byte_array.values, b"\x0a\x14\x1e")  # 10, 20, 30

                # Channel 1: short_int8 (DT_SHORT)
                self.assertEqual(values.channels[1].id, 1)
                self.assertEqual(values.channels[1].values.data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertSequenceEqual(values.channels[1].values.long_array.values, [1, 2, 3])

                # Channel 2: short_int16 (DT_SHORT)
                self.assertEqual(values.channels[2].id, 2)
                self.assertEqual(values.channels[2].values.data_type, ods.DataTypeEnum.DT_SHORT)
                self.assertSequenceEqual(values.channels[2].values.long_array.values, [100, 200, 300])

                # Channel 3: long_uint16 (DT_LONG)
                self.assertEqual(values.channels[3].id, 3)
                self.assertEqual(values.channels[3].values.data_type, ods.DataTypeEnum.DT_LONG)
                self.assertSequenceEqual(values.channels[3].values.long_array.values, [1000, 2000, 3000])

                # Channel 4: long_int32 (DT_LONG)
                self.assertEqual(values.channels[4].id, 4)
                self.assertEqual(values.channels[4].values.data_type, ods.DataTypeEnum.DT_LONG)
                self.assertSequenceEqual(values.channels[4].values.long_array.values, [10000, 20000, 30000])

                # Channel 5: longlong_uint32 (DT_LONGLONG)
                self.assertEqual(values.channels[5].id, 5)
                self.assertEqual(values.channels[5].values.data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertSequenceEqual(values.channels[5].values.longlong_array.values, [100000, 200000, 300000])

                # Channel 6: longlong_int64 (DT_LONGLONG)
                self.assertEqual(values.channels[6].id, 6)
                self.assertEqual(values.channels[6].values.data_type, ods.DataTypeEnum.DT_LONGLONG)
                self.assertSequenceEqual(values.channels[6].values.longlong_array.values, [1000000, 2000000, 3000000])

                # Channel 7: double_uint64 (DT_DOUBLE)
                self.assertEqual(values.channels[7].id, 7)
                self.assertEqual(values.channels[7].values.data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertSequenceEqual(values.channels[7].values.double_array.values, [10000000, 20000000, 30000000])

                # Channel 8: float_col (DT_FLOAT)
                self.assertEqual(values.channels[8].id, 8)
                self.assertEqual(values.channels[8].values.data_type, ods.DataTypeEnum.DT_FLOAT)
                self.assertAlmostEqual(values.channels[8].values.float_array.values[0], 1.5, places=5)
                self.assertAlmostEqual(values.channels[8].values.float_array.values[1], 2.5, places=5)
                self.assertAlmostEqual(values.channels[8].values.float_array.values[2], 3.5, places=5)

                # Channel 9: double_col (DT_DOUBLE)
                self.assertEqual(values.channels[9].id, 9)
                self.assertEqual(values.channels[9].values.data_type, ods.DataTypeEnum.DT_DOUBLE)
                self.assertAlmostEqual(values.channels[9].values.double_array.values[0], 10.123, places=5)
                self.assertAlmostEqual(values.channels[9].values.double_array.values[1], 20.456, places=5)
                self.assertAlmostEqual(values.channels[9].values.double_array.values[2], 30.789, places=5)

                # Channel 10: string_col (DT_STRING)
                self.assertEqual(values.channels[10].id, 10)
                self.assertEqual(values.channels[10].values.data_type, ods.DataTypeEnum.DT_STRING)
                self.assertSequenceEqual(values.channels[10].values.string_array.values, ["first", "second", "third"])

                # Channel 11: date_col (DT_DATE)
                self.assertEqual(values.channels[11].id, 11)
                self.assertEqual(values.channels[11].values.data_type, ods.DataTypeEnum.DT_DATE)
                self.assertEqual(len(values.channels[11].values.string_array.values), 3)
                # Date values are converted to ASAM ODS time format strings

                # Channel 12: complex_col (DT_COMPLEX)
                self.assertEqual(values.channels[12].id, 12)
                self.assertEqual(values.channels[12].values.data_type, ods.DataTypeEnum.DT_COMPLEX)
                # Complex values are stored as [real1, imag1, real2, imag2, ...]
                complex_values = values.channels[12].values.float_array.values
                self.assertAlmostEqual(complex_values[0], 1.0, places=5)  # real part of 1+2j
                self.assertAlmostEqual(complex_values[1], 2.0, places=5)  # imag part of 1+2j
                self.assertAlmostEqual(complex_values[2], 3.0, places=5)  # real part of 3+4j
                self.assertAlmostEqual(complex_values[3], 4.0, places=5)  # imag part of 3+4j
                self.assertAlmostEqual(complex_values[4], 5.0, places=5)  # real part of 5+6j
                self.assertAlmostEqual(complex_values[5], 6.0, places=5)  # imag part of 5+6j

                # Channel 13: dcomplex_col (DT_DCOMPLEX)
                self.assertEqual(values.channels[13].id, 13)
                self.assertEqual(values.channels[13].values.data_type, ods.DataTypeEnum.DT_DCOMPLEX)
                # Double complex values are stored as [real1, imag1, real2, imag2, ...]
                dcomplex_values = values.channels[13].values.double_array.values
                self.assertAlmostEqual(dcomplex_values[0], 1.1, places=5)  # real part of 1.1+2.2j
                self.assertAlmostEqual(dcomplex_values[1], 2.2, places=5)  # imag part of 1.1+2.2j
                self.assertAlmostEqual(dcomplex_values[2], 3.3, places=5)  # real part of 3.3+4.4j
                self.assertAlmostEqual(dcomplex_values[3], 4.4, places=5)  # imag part of 3.3+4.4j
                self.assertAlmostEqual(dcomplex_values[4], 5.5, places=5)  # real part of 5.5+6.6j
                self.assertAlmostEqual(dcomplex_values[5], 6.6, places=5)  # imag part of 5.5+6.6j
            finally:
                service.Close(handle, None)
