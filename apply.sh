#!/usr/bin/env bash

set -ex

SCRIPT_DIR="$(cd "$(dirname "$0")" ; pwd -P)"
pushd "$SCRIPT_DIR"

pushd "terraform" > /dev/null

rm -rf .terraform
terraform init
terraform apply

popd > /dev/null
popd > /dev/null
