"""Comprehensive tests for EnvArgumentParser class."""

from __future__ import annotations

import os
import unittest
from argparse import Action
from pathlib import Path

from ods_exd_api_box.utils.env_argument_parser import EnvArgumentParser, str2bool


class TestStr2Bool(unittest.TestCase):
    """Test str2bool helper function."""

    def test_true_values(self):
        """Test that various representations of true are recognized."""
        for val in ["1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "On", "ON"]:
            with self.subTest(val=val):
                self.assertTrue(str2bool(val))

    def test_false_values(self):
        """Test that values not representing true are false."""
        for val in ["0", "false", "False", "FALSE", "no", "No", "NO", "off", "Off", "OFF", "random"]:
            with self.subTest(val=val):
                self.assertFalse(str2bool(val))

    def test_whitespace_handling(self):
        """Test that whitespace is trimmed."""
        self.assertTrue(str2bool("  true  "))
        self.assertTrue(str2bool("\ttrue\n"))
        self.assertFalse(str2bool("  false  "))

    def test_non_string_values(self):
        """Test conversion of non-string values."""
        self.assertTrue(str2bool(1))
        self.assertFalse(str2bool(0))
        self.assertTrue(str2bool(True))


class TestEnvArgumentParserBasic(unittest.TestCase):
    """Test basic EnvArgumentParser functionality."""

    def setUp(self):
        """Set up test environment."""
        # Clear any environment variables that might interfere
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_") or key.startswith("TEST_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_default_env_prefix(self):
        """Test that default env_prefix is ODS_EXD_API_."""
        parser = EnvArgumentParser()
        self.assertEqual(parser._env_prefix, "ODS_EXD_API_")

    def test_custom_env_prefix(self):
        """Test custom env_prefix."""
        parser = EnvArgumentParser(env_prefix="CUSTOM_")
        self.assertEqual(parser._env_prefix, "CUSTOM_")

    def test_empty_env_prefix(self):
        """Test empty env_prefix."""
        parser = EnvArgumentParser(env_prefix="")
        self.assertEqual(parser._env_prefix, "")

    def test_basic_argument_without_env(self):
        """Test basic argument parsing without environment variable."""
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(["--foo", "bar"])
        self.assertEqual(args.foo, "bar")

    def test_basic_argument_with_default(self):
        """Test that explicit default is used when no env var."""
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, default="default_value")
        args = parser.parse_args([])
        self.assertEqual(args.foo, "default_value")


class TestEnvArgumentParserEnvironmentVariables(unittest.TestCase):
    """Test environment variable integration."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_") or key.startswith("TEST_") or key.startswith("CUSTOM_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_string_from_env(self):
        """Test reading string value from environment."""
        os.environ["ODS_EXD_API_FOO"] = "env_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args([])
        self.assertEqual(args.foo, "env_value")

    def test_int_from_env(self):
        """Test reading int value from environment."""
        os.environ["ODS_EXD_API_PORT"] = "8080"
        parser = EnvArgumentParser()
        parser.add_env_argument("--port", type=int)
        args = parser.parse_args([])
        self.assertEqual(args.port, 8080)

    def test_float_from_env(self):
        """Test reading float value from environment."""
        os.environ["ODS_EXD_API_RATIO"] = "3.14"
        parser = EnvArgumentParser()
        parser.add_env_argument("--ratio", type=float)
        args = parser.parse_args([])
        self.assertAlmostEqual(args.ratio, 3.14)

    def test_path_from_env(self):
        """Test reading Path value from environment."""
        os.environ["ODS_EXD_API_CONFIG_FILE"] = "/tmp/config.ini"
        parser = EnvArgumentParser()
        parser.add_env_argument("--config-file", type=Path)
        args = parser.parse_args([])
        self.assertEqual(args.config_file, Path("/tmp/config.ini"))

    def test_store_true_from_env(self):
        """Test store_true action with environment variable."""
        os.environ["ODS_EXD_API_VERBOSE"] = "true"
        parser = EnvArgumentParser()
        parser.add_env_argument("--verbose", action="store_true")
        args = parser.parse_args([])
        self.assertTrue(args.verbose)

    def test_store_true_from_env_false(self):
        """Test store_true action with false environment variable."""
        os.environ["ODS_EXD_API_VERBOSE"] = "false"
        parser = EnvArgumentParser()
        parser.add_env_argument("--verbose", action="store_true")
        args = parser.parse_args([])
        self.assertFalse(args.verbose)

    def test_store_false_from_env(self):
        """Test store_false action with environment variable."""
        os.environ["ODS_EXD_API_NO_COLOR"] = "true"
        parser = EnvArgumentParser()
        parser.add_env_argument("--no-color", action="store_false")
        args = parser.parse_args([])
        self.assertFalse(args.no_color)

    def test_cmdline_overrides_env(self):
        """Test that command line arguments override environment variables."""
        os.environ["ODS_EXD_API_FOO"] = "env_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(["--foo", "cmdline_value"])
        self.assertEqual(args.foo, "cmdline_value")

    def test_explicit_default_overridden_by_env(self):
        """Test that environment variable overrides explicit default."""
        os.environ["ODS_EXD_API_FOO"] = "env_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, default="default_value")
        args = parser.parse_args([])
        self.assertEqual(args.foo, "env_value")

    def test_custom_prefix(self):
        """Test custom environment variable prefix."""
        os.environ["CUSTOM_FOO"] = "custom_value"
        parser = EnvArgumentParser(env_prefix="CUSTOM_")
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args([])
        self.assertEqual(args.foo, "custom_value")

    def test_empty_prefix(self):
        """Test empty environment variable prefix."""
        os.environ["FOO"] = "value"
        parser = EnvArgumentParser(env_prefix="")
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args([])
        self.assertEqual(args.foo, "value")


class TestEnvArgumentParserCustomEnvVar(unittest.TestCase):
    """Test custom environment variable names."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_") or key.startswith("CUSTOM_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_explicit_env_var(self):
        """Test specifying custom environment variable name."""
        os.environ["ODS_EXD_API_CUSTOM_NAME"] = "custom_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, env_var="CUSTOM_NAME")
        args = parser.parse_args([])
        self.assertEqual(args.foo, "custom_value")

    def test_explicit_env_var_with_prefix(self):
        """Test that explicit env_var is still prefixed."""
        os.environ["ODS_EXD_API_MY_VAR"] = "value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, env_var="MY_VAR")
        args = parser.parse_args([])
        self.assertEqual(args.foo, "value")


class TestEnvArgumentParserHelpText(unittest.TestCase):
    """Test help text generation."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_help_includes_env_var(self):
        """Test that help text includes environment variable name."""
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, help="Foo parameter")
        # Get the action
        action: Action | None = None
        for act in parser._actions:
            if "--foo" in act.option_strings:
                action = act
                break
        assert action is not None
        assert action.help is not None
        self.assertIn("[env: ODS_EXD_API_FOO]", action.help)

    def test_help_without_custom_text(self):
        """Test help text when no custom help is provided."""
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        action: Action | None = None
        for act in parser._actions:
            if "--foo" in act.option_strings:
                action = act
                break
        assert action is not None
        assert action.help is not None
        self.assertIn("[env: ODS_EXD_API_FOO]", action.help)

    def test_help_with_custom_prefix(self):
        """Test help text with custom prefix."""
        parser = EnvArgumentParser(env_prefix="CUSTOM_")
        parser.add_env_argument("--foo", type=str, help="Foo parameter")
        action = None
        for act in parser._actions:
            if "--foo" in act.option_strings:
                action = act
                break
        assert action is not None
        assert action.help is not None
        self.assertIn("[env: CUSTOM_FOO]", action.help)


class TestEnvArgumentParserNaming(unittest.TestCase):
    """Test argument name to environment variable conversion."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_dash_to_underscore(self):
        """Test that dashes are converted to underscores."""
        os.environ["ODS_EXD_API_FOO_BAR"] = "value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo-bar", type=str)
        args = parser.parse_args([])
        self.assertEqual(args.foo_bar, "value")

    def test_multiple_dashes(self):
        """Test multiple dashes in argument name."""
        os.environ["ODS_EXD_API_FOO_BAR_BAZ"] = "value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo-bar-baz", type=str)
        args = parser.parse_args([])
        self.assertEqual(args.foo_bar_baz, "value")

    def test_short_option_ignored(self):
        """Test that short options don't affect env var name."""
        os.environ["ODS_EXD_API_FOO_BAR"] = "value"
        parser = EnvArgumentParser()
        parser.add_env_argument("-f", "--foo-bar", type=str)
        args = parser.parse_args([])
        self.assertEqual(args.foo_bar, "value")


class TestEnvPrefixOption(unittest.TestCase):
    """Test --env-prefix command line option."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_") or key.startswith("ALT_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_env_prefix_changes_lookup(self):
        """Test that --env-prefix changes environment variable lookup."""
        os.environ["ALT_FOO"] = "alt_value"
        os.environ["ODS_EXD_API_FOO"] = "default_value"
        args_list = ["--env-prefix", "ALT_"]
        parser = EnvArgumentParser(args_list)
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(args_list)
        self.assertEqual(args.foo, "alt_value")

    def test_env_prefix_with_equals(self):
        """Test --env-prefix=VALUE syntax."""
        os.environ["ALT_FOO"] = "alt_value"
        args_list = ["--env-prefix=ALT_"]
        parser = EnvArgumentParser(args_list)
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(args_list)
        self.assertEqual(args.foo, "alt_value")

    def test_env_prefix_empty_string(self):
        """Test --env-prefix with empty string."""
        os.environ["FOO"] = "value"
        args_list = ["--env-prefix", ""]
        parser = EnvArgumentParser(args_list)
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(args_list)
        self.assertEqual(args.foo, "value")

    def test_env_prefix_not_from_env_var(self):
        """Test that --env-prefix cannot be set via environment variable."""
        os.environ["ODS_EXD_API_ENV_PREFIX"] = "ALT_"
        os.environ["ODS_EXD_API_FOO"] = "default_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args([])
        # Should use default prefix, not ALT_
        self.assertEqual(args.foo, "default_value")

    def test_env_prefix_with_multiple_args(self):
        """Test --env-prefix with multiple arguments."""
        os.environ["ALT_FOO"] = "foo_value"
        os.environ["ALT_BAR"] = "bar_value"
        args = ["--env-prefix", "ALT_"]
        parser = EnvArgumentParser(args)
        parser.add_env_argument("--foo", type=str)
        parser.add_env_argument("--bar", type=str)
        args = parser.parse_args(args)
        self.assertEqual(args.foo, "foo_value")
        self.assertEqual(args.bar, "bar_value")

    def test_cmdline_overrides_env_with_custom_prefix(self):
        """Test command line overrides env even with custom prefix."""
        os.environ["ALT_FOO"] = "env_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(["--env-prefix", "ALT_", "--foo", "cmdline_value"])
        self.assertEqual(args.foo, "cmdline_value")


class TestEnvArgumentParserServerLike(unittest.TestCase):
    """Test scenarios similar to server.py usage."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_server_config_scenario(self):
        """Test a scenario similar to server.py configuration."""
        # Set up environment variables
        os.environ["ODS_EXD_API_BIND_ADDRESS"] = "localhost"
        os.environ["ODS_EXD_API_PORT"] = "9090"
        os.environ["ODS_EXD_API_MAX_WORKERS"] = "8"
        os.environ["ODS_EXD_API_USE_TLS"] = "true"
        os.environ["ODS_EXD_API_VERBOSE"] = "1"

        parser = EnvArgumentParser(description="ASAM ODS EXD-API gRPC Server")
        parser.add_env_argument("--bind-address", type=str, default="[::]")
        parser.add_env_argument("--port", type=int, default=50051)
        parser.add_env_argument("--max-workers", type=int, default=4)
        parser.add_env_argument("--use-tls", action="store_true")
        parser.add_env_argument("--verbose", action="store_true")

        args = parser.parse_args([])

        self.assertEqual(args.bind_address, "localhost")
        self.assertEqual(args.port, 9090)
        self.assertEqual(args.max_workers, 8)
        self.assertTrue(args.use_tls)
        self.assertTrue(args.verbose)

    def test_mixed_env_and_cmdline(self):
        """Test mixing environment variables and command line arguments."""
        os.environ["ODS_EXD_API_PORT"] = "8080"
        os.environ["ODS_EXD_API_MAX_WORKERS"] = "16"

        parser = EnvArgumentParser()
        parser.add_env_argument("--bind-address", type=str, default="[::]")
        parser.add_env_argument("--port", type=int, default=50051)
        parser.add_env_argument("--max-workers", type=int, default=4)

        args = parser.parse_args(["--bind-address", "0.0.0.0"])

        self.assertEqual(args.bind_address, "0.0.0.0")  # from cmdline
        self.assertEqual(args.port, 8080)  # from env
        self.assertEqual(args.max_workers, 16)  # from env

    def test_path_arguments(self):
        """Test Path type arguments."""
        os.environ["ODS_EXD_API_TLS_CERT_FILE"] = "/path/to/cert.pem"
        os.environ["ODS_EXD_API_TLS_KEY_FILE"] = "/path/to/key.pem"

        parser = EnvArgumentParser()
        parser.add_env_argument("--tls-cert-file", type=Path)
        parser.add_env_argument("--tls-key-file", type=Path)

        args = parser.parse_args([])

        self.assertEqual(args.tls_cert_file, Path("/path/to/cert.pem"))
        self.assertEqual(args.tls_key_file, Path("/path/to/key.pem"))

    def test_no_env_uses_defaults(self):
        """Test that defaults are used when no environment variables are set."""
        parser = EnvArgumentParser()
        parser.add_env_argument("--bind-address", type=str, default="[::]")
        parser.add_env_argument("--port", type=int, default=50051)
        parser.add_env_argument("--verbose", action="store_true")

        args = parser.parse_args([])

        self.assertEqual(args.bind_address, "[::]")
        self.assertEqual(args.port, 50051)
        self.assertFalse(args.verbose)


class TestEnvArgumentParserEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test environment."""
        self.env_backup = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith("ODS_EXD_API_"):
                del os.environ[key]

    def tearDown(self):
        """Restore environment."""
        os.environ.clear()
        os.environ.update(self.env_backup)

    def test_invalid_type_conversion(self):
        """Test that invalid type conversion uses raw string."""
        os.environ["ODS_EXD_API_PORT"] = "not_a_number"
        parser = EnvArgumentParser()
        parser.add_env_argument("--port", type=int)
        args = parser.parse_args(["--port=15"])
        self.assertEqual(args.port, 15)

    def test_invalid_type_conversion_default(self):
        """Test that invalid type conversion uses raw string."""
        os.environ["ODS_EXD_API_PORT"] = "not_a_number"
        parser = EnvArgumentParser()
        parser.add_env_argument("--port", type=int, default=17)
        args = parser.parse_args([])
        self.assertEqual(args.port, 17)

    def test_invalid_type_conversion_default_env(self):
        """Test that invalid type conversion uses raw string."""
        os.environ["ODS_EXD_API_PORT"] = "21"
        parser = EnvArgumentParser()
        parser.add_env_argument("--port", type=int, default=17)
        args = parser.parse_args([])
        self.assertEqual(args.port, 21)

    def test_invalid_type_conversion_default_env_param(self):
        """Test that invalid type conversion uses raw string."""
        os.environ["ODS_EXD_API_PORT"] = "21"
        parser = EnvArgumentParser()
        parser.add_env_argument("--port", type=int, default=17)
        args = parser.parse_args(["--port=42"])
        self.assertEqual(args.port, 42)

    def test_type_conversion_fallback(self):
        """Test fallback for type conversion failures in add_env_argument."""
        os.environ["ODS_EXD_API_FOO"] = "notanumber"

        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=int)
        args = parser.parse_args([])
        self.assertIsNone(args.foo)

    def test_positional_arguments(self):
        """Test that positional arguments work normally."""
        parser = EnvArgumentParser()
        parser.add_env_argument("input_file")
        parser.add_env_argument("--foo", type=str)
        args = parser.parse_args(["test.txt"])
        self.assertEqual(args.input_file, "test.txt")

    def test_required_argument(self):
        """Test required arguments still work."""
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, required=True)
        with self.assertRaises(SystemExit):
            parser.parse_args([])

    def test_required_argument_satisfied_by_env(self):
        """Test required argument satisfied by environment variable."""
        os.environ["ODS_EXD_API_FOO"] = "value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str, required=True)
        args = parser.parse_args([])
        self.assertEqual(args.foo, "value")

    def test_env_prefix_position_in_args(self):
        """Test --env-prefix can appear anywhere in arguments."""
        os.environ["ALT_FOO"] = "alt_value"
        parser = EnvArgumentParser()
        parser.add_env_argument("--foo", type=str)
        parser.add_env_argument("--bar", type=str, default="default")

        # Can only be changed in global args, not in individual parse_args calls
        args = parser.parse_args(["--bar", "custom", "--env-prefix", "ALT_"])
        self.assertIsNone(args.foo)
        self.assertEqual(args.bar, "custom")

    def test_env_prefix_position_in_args_global(self):
        """Test --env-prefix can appear anywhere in arguments."""
        os.environ["ALT_FOO"] = "alt_value"
        parser = EnvArgumentParser(["--env-prefix", "ALT_"])
        parser.add_env_argument("--foo", type=str)
        parser.add_env_argument("--bar", type=str, default="default")

        # Can only be changed in global args, not in individual parse_args calls
        args = parser.parse_args(["--bar", "custom"])
        self.assertEqual(args.foo, "alt_value")
        self.assertEqual(args.bar, "custom")

    def test_multiple_store_true_flags(self):
        """Test multiple store_true flags with environment variables."""
        os.environ["ODS_EXD_API_VERBOSE"] = "true"
        os.environ["ODS_EXD_API_DEBUG"] = "1"
        os.environ["ODS_EXD_API_QUIET"] = "false"

        parser = EnvArgumentParser()
        parser.add_env_argument("--verbose", action="store_true")
        parser.add_env_argument("--debug", action="store_true")
        parser.add_env_argument("--quiet", action="store_true")

        args = parser.parse_args([])

        self.assertTrue(args.verbose)
        self.assertTrue(args.debug)
        self.assertFalse(args.quiet)


if __name__ == "__main__":
    unittest.main()
