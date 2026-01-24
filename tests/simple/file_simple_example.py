"""
ExternalFileData class to read data from an external file using pandas.
"""

import logging
from typing import Any, override

import pandas as pd

from ods_exd_api_box.simple.file_simple_interface import FileSimpleInterface


class FileSimpleExample(FileSimpleInterface):
    """
    Concrete implementation for reading CSV files.
    """

    @classmethod
    @override
    def create(cls, file_path: str, parameters: dict[str, Any]) -> FileSimpleInterface:
        """Factory method to create a file handler instance."""
        return cls(file_path, parameters)

    def __init__(self, file_path: str, parameters: dict[str, Any]) -> None:
        """
        Initialize the ExternalFileData class.
        :param file_path: Path to the external file.
        :param parameters: Parameters for reading the file (e.g., delimiter, header). Check pd.read_csv for details.
        """
        self.file_path: str = file_path
        self.parameters: dict[str, Any] = parameters
        self.df: pd.DataFrame | None = None
        self.log = logging.getLogger(__name__)

    @override
    def close(self) -> None:
        """
        Close the file and release resources.
        """
        if self.df is not None:
            self.log.info("Closing file: %s", self.file_path)
            del self.df
            self.df = None

    @override
    def not_my_file(self) -> bool:
        """
        Check if the file should be read with this plugin.
        :return: True if the file should not be read with this plugin, False otherwise.
        """
        # If the CSV file contains only a single column or all columns have datatype string,
        # we assume that it is not meant to be parsed with this plugin.
        df = self.data()
        if df.empty or len(df.columns) == 1 or all(df.dtypes == "object"):
            self.log.info(
                "File %s is not a valid CSV file for this plugin with parameters '%s'.",
                self.file_path,
                self.parameters,
            )
            return True
        return False

    @override
    def data(self) -> pd.DataFrame:
        """
        Read the data from the file and return it as a pandas DataFrame.
        :return: DataFrame containing the data from the file.
        """
        if self.df is None:
            self.log.info("Reading file: %s", self.file_path)
            import numpy as np

            self.df = pd.DataFrame(
                {
                    "byte_col": np.array([10, 20, 30], dtype=np.uint8),
                    "short_int8": np.array([1, 2, 3], dtype=np.int8),
                    "short_int16": np.array([100, 200, 300], dtype=np.int16),
                    "long_uint16": np.array([1000, 2000, 3000], dtype=np.uint16),
                    "long_int32": np.array([10000, 20000, 30000], dtype=np.int32),
                    "longlong_uint32": np.array([100000, 200000, 300000], dtype=np.uint32),
                    "longlong_int64": np.array([1000000, 2000000, 3000000], dtype=np.int64),
                    "double_uint64": np.array([10000000, 20000000, 30000000], dtype=np.uint64),
                    "float_col": np.array([1.5, 2.5, 3.5], dtype=np.float32),
                    "double_col": np.array([10.123, 20.456, 30.789], dtype=np.float64),
                    "string_col": pd.Series(["first", "second", "third"], dtype="string"),
                    "date_col": pd.to_datetime(["2024-01-01", "2024-06-15", "2024-12-31"]),
                    "complex_col": np.array([1 + 2j, 3 + 4j, 5 + 6j], dtype=np.complex64),
                    "dcomplex_col": np.array([1.1 + 2.2j, 3.3 + 4.4j, 5.5 + 6.6j], dtype=np.complex128),
                }
            )
        return self.df


if __name__ == "__main__":
    from ods_exd_api_box.simple.file_simple import serve_plugin_simple

    serve_plugin_simple(
        file_type_name="TEST_SIMPLE",
        file_type_factory=FileSimpleExample.create,
        file_type_file_patterns=["*.TEST_SIMPLE"],
    )
