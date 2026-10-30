#!/bin/sh
# CPE 教練 安裝程式（Linux）。在終端機執行：  sh install-linux.sh        （只檢查：sh install-linux.sh --check）
HERE=$(cd "$(dirname "$0")" && pwd)
exec sh "$HERE/setup/bootstrap.sh" "$@"
