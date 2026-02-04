"""ArgumentParser that supports reading defaults from environment variables."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Sequence


def str2bool(val: Any) -> bool:
    """Convert various string representations to boolean."""
    return str(val).strip().lower() in {"1", "true", "yes", "on"}


class EnvArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that reads default values from environment variables.

    Environment variable names are constructed from argument names by:
    1. Taking the long option name (--foo-bar)
    2. Removing the leading dashes
    3. Converting to uppercase and replacing hyphens with underscores
    4. Prefixing with the env_prefix

    Example:
        parser = EnvArgumentParser(env_prefix="APP_")
        parser.add_argument("--db-host", type=str)
        # Will read from APP_DB_HOST environment variable if set
    """

    def __init__(
        self,
        args: Sequence[str] | None = None,
        env_prefix: str = "ODS_EXD_API_",
        **kwargs: Any,
    ) -> None:
        """Initialize parser with environment variable prefix.

        Args:
            env_prefix: Prefix for environment variables (default: "ODS_EXD_API_")
            *args: Positional arguments passed to ArgumentParser
            **kwargs: Keyword arguments passed to ArgumentParser
        """
        if args is None:
            args = sys.argv[1:]

        dummy_parser = argparse.ArgumentParser(add_help=False)
        dummy_parser.add_argument("--env-prefix", type=str, default=env_prefix)
        parser_args, _ = dummy_parser.parse_known_args(args)
        self._env_prefix = parser_args.env_prefix
        super().__init__(**kwargs)
        super().add_argument(
            "--env-prefix",
            type=str,
            help="Environment variable prefix",
            default=self._env_prefix,
        )

    def add_env_argument(
        self,
        *args: str,
        env_var: str | None = None,
        help: str | None = None,
        action: str | type[argparse.Action] | None = None,
        type: Callable[[str], Any] | None = None,
        **kwargs: Any,
    ) -> argparse.Action:
        """Add argument with environment variable support.

        Args:
            *args: Positional arguments for the argument (e.g., '-f', '--foo')
            env_var: Override environment variable name (without prefix)
            help: Help text for the argument
            action: Argument action (e.g., 'store_true', 'store_false')
            type: Type converter function
            **kwargs: Additional keyword arguments passed to ArgumentParser.add_argument

        Returns:
            The created Action object
        """
        # Guess env_var if not specified (from --foo-bar → FOO_BAR)
        if env_var is None and args:
            for arg in args:
                if arg.startswith("--"):
                    env_var = arg[2:].replace("-", "_").upper()
                    break
        full_env_var = f"{self._env_prefix}{env_var}" if env_var else None

        # Handle env default value
        action_ = action or kwargs.get("action", None)
        type_ = type or kwargs.get("type", None)
        env_val = os.environ.get(full_env_var) if full_env_var else None
        if full_env_var and env_val is not None:
            # If environment variable is set, the argument shouldn't be required
            if "required" in kwargs and kwargs["required"]:
                kwargs["required"] = False

            if action_ == "store_true":
                kwargs["default"] = str2bool(env_val)
            elif action_ == "store_false":
                # For store_false, if env var is truthy, we set default to False (as if flag was present)
                kwargs["default"] = not str2bool(env_val)
            elif type_ is not None:
                # Handle Path, int, float, etc.
                try:
                    if type_ is Path:
                        kwargs["default"] = Path(env_val)
                    else:
                        kwargs["default"] = type_(env_val)
                except Exception as e:
                    logging.warning(
                        f"Ignore Environment variable {full_env_var}. "
                        f"Could not convert {full_env_var}='{env_val}' to {type_}: {e}"
                    )
            else:
                kwargs["default"] = env_val

        # Help string update
        help_text = help or ""
        if full_env_var:
            if help_text:
                help_text += " "
            help_text += f"[env: {full_env_var}]"

        # Build kwargs for super().add_argument()
        # Only include action and type if they were explicitly provided
        super_kwargs = dict(kwargs)
        if help_text:
            super_kwargs["help"] = help_text
        if action is not None:
            super_kwargs["action"] = action
        if type is not None:
            super_kwargs["type"] = type

        return super().add_argument(*args, **super_kwargs)
