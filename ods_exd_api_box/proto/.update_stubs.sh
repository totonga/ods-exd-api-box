#!/bin/bash
# bash .update_stubs.sh
# download current versions of the .proto files
curl -o ods.proto https://raw.githubusercontent.com/asam-ev/ASAM-ODS-Interfaces/main/ods.proto
curl -o ods_external_data.proto https://raw.githubusercontent.com/asam-ev/ASAM-ODS-Interfaces/main/ods_external_data.proto

# Generate Python stubs
python3 -m grpc_tools.protoc \
  -I. \
  --python_out=. \
  --pyi_out=. \
  --grpc_python_out=. \
  ods.proto ods_external_data.proto

# Convert absolute imports to relative imports
sed -i 's/^import ods_pb2 as ods__pb2$/from . import ods_pb2 as ods__pb2/' ods_external_data_pb2.py
sed -i 's/^import ods_external_data_pb2 as ods__external__data__pb2$/from . import ods_external_data_pb2 as ods__external__data__pb2/' ods_external_data_pb2_grpc.py
