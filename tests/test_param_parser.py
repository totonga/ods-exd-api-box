"""Comprehensive tests for ParamParser class."""
import json
import base64
import unittest
from ods_exd_api_box.param_parser import ParamParser


class TestParamParserBasic(unittest.TestCase):
    """Test basic parsing functionality."""

    def test_empty_string(self):
        """Test parsing empty string returns empty dict."""
        self.assertEqual(ParamParser.parse_params(""), {})

    def test_none_input_returns_empty_dict(self):
        """Test that None input returns empty dict."""
        self.assertEqual(ParamParser.parse_params(None), {})

    def test_non_string_input_raises_error(self):
        """Test that non-string input raises ValueError."""
        with self.assertRaisesRegex(ValueError, "parameters must be a string"):
            ParamParser.parse_params(123)
        with self.assertRaisesRegex(ValueError, "parameters must be a string"):
            ParamParser.parse_params([])
        with self.assertRaisesRegex(ValueError, "parameters must be a string"):
            ParamParser.parse_params({})


class TestParamParserSemicolonSeparated(unittest.TestCase):
    """Test semicolon-separated key=value parsing."""

    def test_single_pair(self):
        """Test parsing single key=value pair."""
        result = ParamParser.parse_params("key1=value1")
        self.assertEqual(result, {"key1": "value1"})

    def test_multiple_pairs(self):
        """Test parsing multiple key=value pairs."""
        result = ParamParser.parse_params("key1=value1;key2=value2;key3=value3")
        self.assertEqual(result, {"key1": "value1", "key2": "value2", "key3": "value3"})

    def test_pairs_with_whitespace(self):
        """Test that whitespace is trimmed from keys and values."""
        result = ParamParser.parse_params("  key1  =  value1  ;  key2  =  value2  ")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_value_with_equals_sign(self):
        """Test that values can contain equals signs."""
        result = ParamParser.parse_params("url=http://example.com?param=value")
        self.assertEqual(result, {"url": "http://example.com?param=value"})

    def test_empty_pairs_ignored(self):
        """Test that empty pairs (consecutive semicolons) are skipped."""
        result = ParamParser.parse_params("key1=value1;;key2=value2")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_invalid_pair_without_equals(self):
        """Test that pairs without equals raise ValueError."""
        with self.assertRaisesRegex(ValueError, "must contain '='"):
            ParamParser.parse_params("key1=value1;invalid;key2=value2")

    def test_empty_key_raises_error(self):
        """Test that empty keys raise ValueError."""
        with self.assertRaisesRegex(ValueError, "key cannot be empty"):
            ParamParser.parse_params("=value")

    def test_pairs_with_semicolons_in_values(self):
        """Test parsing pairs (semicolons only split, not used in values)."""
        result = ParamParser.parse_params("key1=value1;key2=value2")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})


class TestParamParserJSON(unittest.TestCase):
    """Test JSON format parsing."""

    def test_simple_json(self):
        """Test parsing simple JSON."""
        json_str = '{"key1": "value1", "key2": "value2"}'
        result = ParamParser.parse_params(json_str)
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_json_with_whitespace(self):
        """Test parsing JSON with leading/trailing whitespace."""
        json_str = '  {"key1": "value1"}  '
        result = ParamParser.parse_params(json_str)
        self.assertEqual(result, {"key1": "value1"})

    def test_json_with_numbers(self):
        """Test parsing JSON with numeric values."""
        json_str = '{"count": 42, "active": true}'
        result = ParamParser.parse_params(json_str)
        self.assertEqual(result, {"count": 42, "active": True})

    def test_json_with_nested_objects(self):
        """Test parsing JSON with nested objects."""
        json_str = '{"user": {"name": "John", "age": 30}}'
        result = ParamParser.parse_params(json_str)
        self.assertEqual(result, {"user": {"name": "John", "age": 30}})

    def test_invalid_json_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Invalid JSON format"):
            ParamParser.parse_params('{"key": "value"')

    def test_invalid_json_missing_quotes(self):
        """Test invalid JSON with missing quotes."""
        with self.assertRaisesRegex(ValueError, "Invalid JSON format"):
            ParamParser.parse_params('{key: value}')


class TestParamParserBase64(unittest.TestCase):
    """Test base64 format parsing with B64: prefix."""

    def test_base64_encoded_semicolon_separated(self):
        """Test parsing base64-encoded semicolon-separated values."""
        # Encode "key1=value1;key2=value2"
        original = "key1=value1;key2=value2"
        encoded = base64.b64encode(original.encode('utf-8')).decode('utf-8')
        result = ParamParser.parse_params(f"B64:{encoded}")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_base64_encoded_json(self):
        """Test parsing base64-encoded JSON."""
        original = '{"key1": "value1", "key2": "value2"}'
        encoded = base64.b64encode(original.encode('utf-8')).decode('utf-8')
        result = ParamParser.parse_params(f"B64:{encoded}")
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_base64_with_padding(self):
        """Test parsing base64 with padding."""
        original = "key=value"
        encoded = base64.b64encode(original.encode('utf-8')).decode('utf-8')
        result = ParamParser.parse_params(f"B64:{encoded}")
        self.assertEqual(result, {"key": "value"})

    def test_base64_with_whitespace(self):
        """Test base64 with leading/trailing whitespace."""
        original = "key1=value1;key2=value2"
        encoded = base64.b64encode(original.encode('utf-8')).decode('utf-8')
        encoded_with_space = f"  B64:{encoded}  "
        result = ParamParser.parse_params(encoded_with_space)
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_invalid_base64_raises_error(self):
        """Test that invalid base64 raises ValueError."""
        with self.assertRaisesRegex(ValueError, "Invalid base64 encoding"):
            ParamParser.parse_params("B64:!!!invalid!!!")


class TestParamParserPriority(unittest.TestCase):
    """Test parsing priority (trim -> B64: prefix -> json -> semicolon)."""

    def test_json_not_treated_as_base64(self):
        """Test that JSON without B64: prefix is parsed as JSON."""
        json_str = '{"key": "value"}'
        result = ParamParser.parse_params(json_str)
        self.assertEqual(result, {"key": "value"})

    def test_base64_prefix_required(self):
        """Test that base64 must have B64: prefix."""
        # Regular base64 without prefix is treated as semicolon-separated
        encoded = base64.b64encode(b"a=b;c=d").decode()
        result = ParamParser.parse_params(encoded)
        # Without B64: prefix, the base64 string is treated as semicolon-separated
        # The base64 has '=' so it gets split incorrectly
        self.assertIsInstance(result, dict)

    def test_whitespace_trimmed_before_detection(self):
        """Test whitespace is trimmed before format detection."""
        json_str = '  {"key": "value"}  '
        result = ParamParser.parse_params(json_str)
        self.assertEqual(result, {"key": "value"})


class TestParamParserEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""

    def test_empty_value(self):
        """Test parsing with empty value is allowed."""
        result = ParamParser.parse_params("key=")
        self.assertEqual(result, {"key": ""})

    def test_duplicate_keys_last_wins(self):
        """Test that duplicate keys use the last value."""
        result = ParamParser.parse_params("key=value1;key=value2")
        self.assertEqual(result, {"key": "value2"})

    def test_special_characters_in_values(self):
        """Test special characters in values."""
        result = ParamParser.parse_params("url=http://example.com/path?query=1&other=2")
        self.assertEqual(result, {"url": "http://example.com/path?query=1&other=2"})

    def test_unicode_values(self):
        """Test Unicode characters in values."""
        result = ParamParser.parse_params("greeting=Hello世界")
        self.assertEqual(result, {"greeting": "Hello世界"})

    def test_base64_with_unicode(self):
        """Test base64 encoding of Unicode."""
        original = "greeting=Hello世界"
        encoded = base64.b64encode(original.encode('utf-8')).decode()
        result = ParamParser.parse_params(f"B64:{encoded}")
        self.assertEqual(result, {"greeting": "Hello世界"})

    def test_nested_base64_not_supported(self):
        """Test that deeply nested base64 decoding only happens once."""
        # Create valid inner content: "key=value"
        inner = "key=value"
        inner_encoded = base64.b64encode(inner.encode()).decode()
        # Then encode the base64 string itself
        outer_encoded = base64.b64encode(inner_encoded.encode()).decode()
        # With B64: prefix, it decodes once to get the base64 string
        # That string doesn't start with B64: or {, so it's treated as semicolon-separated
        # But since it has no '=' (base64 has valid chars but not =), it will raise error
        with self.assertRaisesRegex(ValueError, "must contain '='"):
            ParamParser.parse_params(f"B64:{outer_encoded}")

    def test_only_semicolons(self):
        """Test input with only semicolons."""
        result = ParamParser.parse_params(";;;")
        self.assertEqual(result, {})

    def test_json_like_but_not_json(self):
        """Test strings that look like JSON but aren't."""
        # This will raise ValueError
        with self.assertRaisesRegex(ValueError, "Invalid JSON format"):
            ParamParser.parse_params("{not valid json}")

    def test_multiple_equals_in_value(self):
        """Test multiple equals signs in value."""
        result = ParamParser.parse_params("formula=a=b+c=d")
        self.assertEqual(result, {"formula": "a=b+c=d"})
