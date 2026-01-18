
"""
To simply parse parameters from a string into a dictionary.
"""
import json
import re
import base64


class ParamParser:

    @staticmethod
    def parse_params(parameters: str) -> dict[str, str]:
        """Parse a parameter string into a dictionary.

        Args:
            parameters: A string of parameters in one of these formats:
                       - Base64: "B64:..." where ... is base64-encoded JSON or key=value string
                       - JSON: "{\"key1\": \"value1\", \"key2\": \"value2\"}"
                       - Semicolon-separated: "key1=value1;key2=value2"
                       - None or empty string returns empty dict

        Returns:
            A dictionary with parameter keys and values

        Raises:
            ValueError: If parameters is not a string or None, or if parsing fails
        """
        # Check type first
        if parameters is not None and not isinstance(parameters, str):
            raise ValueError(f"parameters must be a string or None, got {type(parameters).__name__}")

        # Handle None and empty string
        if parameters is None or not parameters:
            return {}

        # Step 1: Trim
        trimmed = parameters.strip()

        # Step 2: Check for B64: prefix
        if trimmed.startswith('B64:'):
            try:
                encoded = trimmed[4:]  # Remove 'B64:' prefix
                decoded = base64.b64decode(encoded).decode('utf-8').strip()
                return ParamParser.parse_params(decoded)
            except (ValueError, UnicodeDecodeError) as e:
                raise ValueError(f"Invalid base64 encoding: {e}")

        # Step 3: Parse JSON or semicolon-separated
        if trimmed.startswith('{'):
            # If it looks like JSON, parse it as JSON
            try:
                return json.loads(trimmed)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e.msg}")

        # Parse as semicolon-separated key=value pairs
        param_dict = {}
        if trimmed:  # Only process if not empty
            for pair in trimmed.split(';'):
                pair = pair.strip()
                if not pair:  # Skip empty pairs
                    continue
                if '=' not in pair:
                    raise ValueError(f"Invalid parameter format: '{pair}' must contain '='")
                key, value = pair.split('=', 1)
                key = key.strip()
                value = value.strip()
                if not key:
                    raise ValueError("Parameter key cannot be empty")
                param_dict[key] = value
        return param_dict