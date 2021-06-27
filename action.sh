#!/usr/bin/env bash

set -euo pipefail

BASE_PATH=$(cd "$(dirname "$0")" && pwd)

mkdir -p "$BASE_PATH/.tools"
curl -sSL https://storage.googleapis.com/container-diff/latest/container-diff-linux-amd64 -o "$BASE_PATH/.tools/container-diff"
chmod +x "$BASE_PATH/.tools/container-diff"

export PYTHONPATH
export PATH=$BASE_PATH/.tools:$PATH

python3 -m buildxy.cli
