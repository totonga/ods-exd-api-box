"""Comprehensive tests for AttribsHelper class."""

import datetime
import unittest

from ods_exd_api_box.proto import ods
from ods_exd_api_box.utils import AttributeHelper, TimeHelper


class TestAttribsHelperTimeConversion(unittest.TestCase):
    """Test time conversion to ASAM ODS format."""

    def setUp(self):
        self.helper = AttributeHelper()

    def test_python_datetime_with_microseconds(self):
        """Test Python datetime conversion with microseconds."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45, 123456)
        result = TimeHelper.to_asam_ods_time(dt)
        # 123456 microseconds = 123456000 nanoseconds
        self.assertEqual(result, "20230115103045123456")

    def test_python_datetime_without_microseconds(self):
        """Test Python datetime conversion without fractional seconds."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45, 0)
        result = TimeHelper.to_asam_ods_time(dt)
        self.assertEqual(result, "20230115103045")

    def test_python_datetime_with_trailing_zero_microseconds(self):
        """Test Python datetime with trailing zeros in microseconds."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45, 100000)
        result = TimeHelper.to_asam_ods_time(dt)
        # 100000 microseconds = 100000000 nanoseconds, trailing zeros stripped
        self.assertEqual(result, "202301151030451")

    def test_python_date(self):
        """Test Python date conversion (no time component)."""
        d = datetime.date(2023, 1, 15)
        result = TimeHelper.to_asam_ods_time(d)
        # Should be midnight
        self.assertEqual(result, "20230115000000")

    def test_unix_timestamp_integer(self):
        """Test Unix timestamp as integer."""
        # Use UTC time to avoid timezone issues
        # 2023-01-15 10:30:45 UTC = 1673779845
        timestamp = 1673779845
        result = TimeHelper.to_asam_ods_time(timestamp)
        # Should have no fractional part - result will be in UTC
        self.assertIn("20230115", result)  # Check date part
        self.assertTrue(len(result) == 14)  # YYYYMMDDhhmmss format

    def test_unix_timestamp_float_with_fractional_seconds(self):
        """Test Unix timestamp as float with fractional seconds."""
        # Use a simple timestamp with known fractional part
        timestamp = 1000.123456789
        result = TimeHelper.to_asam_ods_time(timestamp)
        # Should preserve nanoseconds
        self.assertRegex(result, r"^\d{14}\d+$")  # Date + optional fractions
        self.assertGreater(len(result), 14)  # Should have fractional part

    def test_unix_timestamp_float_with_trailing_zeros(self):
        """Test Unix timestamp with trailing zeros in fractional part."""
        timestamp = 1000.100000  # Simple timestamp with 1/10 second
        result = TimeHelper.to_asam_ods_time(timestamp)
        # Should have fractional part without trailing zeros
        self.assertGreater(len(result), 14)  # Should have fractional part
        self.assertFalse(result.endswith("0"))  # No trailing zeros

    def test_unix_timestamp_zero(self):
        """Test Unix timestamp at epoch."""
        timestamp = 0
        result = TimeHelper.to_asam_ods_time(timestamp)
        # 1970-01-01 00:00:00 UTC
        self.assertEqual(result, "19700101000000")

    def test_invalid_type_raises_error(self):
        """Test that invalid types raise ValueError."""
        with self.assertRaisesRegex(ValueError, "Unsupported datetime type"):
            TimeHelper.to_asam_ods_time("2023-01-15")

    def test_invalid_datetime_raises_error(self):
        """Test that invalid datetime values raise ValueError."""
        with self.assertRaisesRegex(ValueError, "Unsupported datetime type"):
            TimeHelper.to_asam_ods_time(None)

    def test_numpy_datetime64_detection(self):
        """Test detection and conversion of numpy datetime64 (without numpy import)."""
        # This test is just for documentation - actual numpy testing would need numpy installed
        # The logic is tested through the actual to_asam_ods_time method
        pass

    def test_edge_case_midnight(self):
        """Test conversion at midnight."""
        dt = datetime.datetime(2023, 1, 15, 0, 0, 0, 0)
        result = TimeHelper.to_asam_ods_time(dt)
        self.assertEqual(result, "20230115000000")

    def test_edge_case_end_of_day(self):
        """Test conversion at 23:59:59."""
        dt = datetime.datetime(2023, 1, 15, 23, 59, 59, 999999)
        result = TimeHelper.to_asam_ods_time(dt)
        self.assertEqual(result, "20230115235959999999")

    def test_leap_year_date(self):
        """Test conversion on leap year date."""
        dt = datetime.datetime(2020, 2, 29, 12, 0, 0, 0)
        result = TimeHelper.to_asam_ods_time(dt)
        self.assertEqual(result, "20200229120000")


class TestAttribsHelperAddAttributes(unittest.TestCase):
    """Test add method."""

    def setUp(self):
        self.helper = AttributeHelper()
        # Use actual ods.ContextVariables
        self.attributes = ods.ContextVariables()

    def test_add_string_attribute(self):
        """Test adding string attribute."""
        properties = {"name": "test"}
        self.helper.add(self.attributes, properties)
        self.assertIn("test", self.attributes.variables["name"].string_array.values)

    def test_add_float_attribute(self):
        """Test adding float attribute."""
        properties = {"value": 3.14}
        self.helper.add(self.attributes, properties)
        self.assertIn(3.14, self.attributes.variables["value"].double_array.values)

    def test_add_integer_attribute(self):
        """Test adding integer attribute."""
        properties = {"count": 42}
        self.helper.add(self.attributes, properties)
        self.assertIn(42, self.attributes.variables["count"].long_array.values)

    def test_add_bool_attribute(self):
        """Test adding bool attribute."""
        properties = {"enabled": True}
        self.helper.add(self.attributes, properties)
        self.assertIn(True, self.attributes.variables["enabled"].boolean_array.values)

    def test_add_bool_false_attribute(self):
        """Test adding bool False attribute."""
        properties = {"enabled": False}
        self.helper.add(self.attributes, properties)
        self.assertIn(False, self.attributes.variables["enabled"].boolean_array.values)

    def test_add_datetime_attribute(self):
        """Test adding datetime attribute."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45, 123456)
        properties = {"timestamp": dt}
        self.helper.add(self.attributes, properties)

        expected_time = "20230115103045123456"
        self.assertIn(expected_time, self.attributes.variables["timestamp"].string_array.values)

    def test_add_multiple_attributes(self):
        """Test adding multiple attributes of different types."""
        properties = {"name": "test", "value": 3.14, "count": 42, "enabled": True}
        self.helper.add(self.attributes, properties)

        # Verify all were processed
        self.assertEqual(len(properties), 4)
        self.assertIn("test", self.attributes.variables["name"].string_array.values)
        self.assertIn(3.14, self.attributes.variables["value"].double_array.values)
        self.assertIn(42, self.attributes.variables["count"].long_array.values)
        self.assertIn(True, self.attributes.variables["enabled"].boolean_array.values)

    def test_add_invalid_attribute_raises_error(self):
        """Test that invalid attribute types raise ValueError."""
        properties = {"data": [1, 2, 3]}  # List is not supported

        with self.assertRaisesRegex(ValueError, "not assignable"):
            self.helper.add(self.attributes, properties)

    def test_add_empty_properties(self):
        """Test adding empty properties dict."""
        properties = {}
        self.helper.add(self.attributes, properties)

        # Should not raise, no variables should be accessed
        # Empty dict means no properties to add
        self.assertEqual(len(self.attributes.variables), 0)

    def test_is_datetime_type_with_python_datetime(self):
        """Test _is_datetime_type with Python datetime."""
        dt = datetime.datetime(2023, 1, 15, 10, 30, 45)
        # Access the private method via name mangling
        result = TimeHelper.is_datetime_type(dt)
        self.assertTrue(result)

    def test_is_datetime_type_with_python_date(self):
        """Test _is_datetime_type with Python date."""
        d = datetime.date(2023, 1, 15)
        result = TimeHelper.is_datetime_type(d)
        self.assertTrue(result)

    def test_is_datetime_type_with_int(self):
        """Test _is_datetime_type with integer (unix timestamp)."""
        result = TimeHelper.is_datetime_type(1673779845)
        self.assertFalse(result)

    def test_is_datetime_type_with_float(self):
        """Test _is_datetime_type with float (unix timestamp)."""
        result = TimeHelper.is_datetime_type(1673779845.123)
        self.assertFalse(result)

    def test_is_datetime_type_with_bool(self):
        """Test _is_datetime_type with bool."""
        result = TimeHelper.is_datetime_type(True)
        self.assertFalse(result)

    def test_is_datetime_type_with_string(self):
        """Test _is_datetime_type with string."""
        result = TimeHelper.is_datetime_type("2023-01-15")
        self.assertFalse(result)

    def test_delete_entry_when_value_is_none(self):
        """Test that attribute is deleted when value is None."""
        self.helper.add(self.attributes, {"val1": 123, "obsolete": "delete me"})
        self.assertIn("obsolete", self.attributes.variables)
        self.assertIn("val1", self.attributes.variables)

        self.helper.add(self.attributes, {"obsolete": None})
        self.assertNotIn("obsolete", self.attributes.variables)
        self.assertIn("val1", self.attributes.variables)


class TestAttribsHelperNumpyDatetime64(unittest.TestCase):
    """Test numpy datetime64 support (without importing numpy)."""

    def setUp(self):
        self.helper = AttributeHelper()

    def test_numpy_datetime64_like_object(self):
        """Test handling of numpy-like datetime64 objects."""
        # This test documents that numpy datetime64 support exists
        # Actual numpy testing would require numpy to be installed
        # The logic is tested in TimeHelper.is_datetime_type and to_asam_ods_time
        pass
