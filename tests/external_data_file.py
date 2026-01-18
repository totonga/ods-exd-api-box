"""Interface for handling file access."""

from __future__ import annotations

from typing import override

from google.protobuf.json_format import ParseDict

from ods_exd_api_box import ExdFileInterface, exd_api
from ods_exd_api_box.utils import AttributeHelper, ParamParser


class ExternalDataFile(ExdFileInterface):
    """Class for handling for NI tdms files."""

    @classmethod
    @override
    def create(cls, file_path: str, parameters: str) -> ExdFileInterface:
        """Factory method to create a file handler instance."""
        if not file_path.endswith(".exd_api_test"):
            from ods_exd_api_box.exceptions import NotMyFileError

            raise NotMyFileError(f"File '{file_path}' is not handled by ExternalDataFile.")

        return cls(file_path, parameters)

    def __init__(self, file_path: str, parameters: str):
        """Initialize the external data file handler."""
        params = ParamParser.parse_params(parameters)
        params.get("example_param", "default_value")
        self.file_path = file_path

    @override
    def close(self):
        """Close the external data file."""
        pass

    @override
    def fill_structure(self, structure: exd_api.StructureResult) -> None:
        """Fill the structure of the external data file."""

        if "dummy.exd_api_test" not in self.file_path:
            from ods_exd_api_box.exceptions import NotMyFileError

            raise NotMyFileError(f"File '{self.file_path}' is not handled by ExternalDataFile.")

        AttributeHelper.add(properties={"name": "Raw Layer_00001"}, attributes=structure.attributes)

        hardcoded = exd_api.StructureResult()
        ParseDict(
            {
                "identifier": {"url": "file:///workspaces/ods-exd-api-box/data/dummy.exd_api_test"},
                "name": "dummy.exd_api_test",
                "groups": [
                    {
                        "name": "Layer Data",
                        "totalNumberOfChannels": "7",
                        "numberOfRows": "2000",
                        "channels": [
                            {
                                "name": "First  Channel",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["First  Channel"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                            {
                                "id": "1",
                                "name": "Second Chan",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["Second Chan"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                            {
                                "id": "2",
                                "name": "Third Chan",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["Third Chan"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                            {
                                "id": "3",
                                "name": "Fourth Chan",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["Fourth Chan"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                            {
                                "id": "4",
                                "name": "Fifth Chan",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["Fifth Chan"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                            {
                                "id": "5",
                                "name": "Sixth Chan",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["Sixth Chan"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                            {
                                "id": "6",
                                "name": "Seventh Cha",
                                "dataType": "DT_DOUBLE",
                                "unitString": "Volts",
                                "attributes": {
                                    "variables": {
                                        "NI_UnitDescription": {"stringArray": {"values": ["Volts"]}},
                                        "wf_start_time": {"stringArray": {"values": ["20161215223521000000"]}},
                                        "wf_increment": {"doubleArray": {"values": [1.9999999999999998e-05]}},
                                        "wf_start_offset": {"doubleArray": {"values": [0.0]}},
                                        "NI_Number_Of_Scales": {"longArray": {"values": [2]}},
                                        "NI_Scale[1]_Scale_Type": {"stringArray": {"values": ["Linear"]}},
                                        "wf_samples": {"longArray": {"values": [1]}},
                                        "NI_Scale[1]_Linear_Y_Intercept": {"doubleArray": {"values": [0.0]}},
                                        "NI_Scaling_Status": {"stringArray": {"values": ["unscaled"]}},
                                        "NI_ChannelName": {"stringArray": {"values": ["Seventh Cha"]}},
                                        "NI_Scale[1]_Linear_Input_Source": {"longArray": {"values": [0]}},
                                        "NI_Scale[1]_Linear_Slope": {
                                            "doubleArray": {"values": [0.0003051850947599719]}
                                        },
                                        "unit_string": {"stringArray": {"values": ["Volts"]}},
                                    }
                                },
                            },
                        ],
                    }
                ],
                "attributes": {"variables": {"name": {"stringArray": {"values": ["Raw Layer_00001"]}}}},
            },
            hardcoded,
        )
        structure.MergeFrom(hardcoded)

    @override
    def get_values(self, request: exd_api.ValuesRequest) -> exd_api.ValuesResult:
        """Get values from the external data file."""

        hardcoded = exd_api.ValuesResult()
        ParseDict(
            {
                "channels": [
                    {
                        "values": {
                            "dataType": "DT_DOUBLE",
                            "doubleArray": {
                                "values": [
                                    -0.18402661214026306,
                                    0.1480147709585864,
                                    -0.24506363109225746,
                                    -0.29725028229621264,
                                ]
                            },
                        }
                    },
                    {
                        "id": "1",
                        "values": {
                            "dataType": "DT_DOUBLE",
                            "doubleArray": {
                                "values": [
                                    1.0303048799096652,
                                    0.6497390667439802,
                                    0.7638782921842098,
                                    0.5508590960417493,
                                ]
                            },
                        },
                    },
                ]
            },
            hardcoded,
        )

        return hardcoded


if __name__ == "__main__":

    from ods_exd_api_box import serve_plugin

    serve_plugin(
        file_type_name="EXD-API-TEST",
        file_type_factory=ExternalDataFile.create,
        file_type_file_patterns=["*.exd_api_test"],
    )
