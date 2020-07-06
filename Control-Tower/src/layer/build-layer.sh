#!/bin/bash
set -eo pipefail
rm -rf package

pip install --target ./python -r ../function/requirements.txt