"""Helper functions for adding attributes to ASAM ODS structures."""
from ods_exd_api_box.proto import ods
from . import TimeHelper

class AttribsHelper:
    """Helper class to add attributes to ASAM ODS structures."""

    @staticmethod
    def add(attributes: ods.ContextVariables, properties: dict[str, object]) -> None:
        """
        Add attributes to ASAM ODS ContextVariables.
        This is used to add metadata attributes to Exd API structures.
        If an attribute value already exists, it is overwritten.
        """

        for name, value in properties.items():
            if value is None:
                if name in attributes.variables:
                    del attributes.variables[name]
            elif isinstance(value, bool):
                attributes.variables[name].boolean_array.values.append(value)
            elif isinstance(value, int):
                attributes.variables[name].long_array.values.append(value)
            elif isinstance(value, float):
                attributes.variables[name].double_array.values.append(value)
            elif isinstance(value, str):
                attributes.variables[name].string_array.values.append(value)
            elif TimeHelper.is_datetime_type(value):
                attributes.variables[name].string_array.values.append(
                    TimeHelper.to_asam_ods_time(value))
            else:
                raise ValueError(
                    f'Attribute "{name}": "{value}" not assignable')
