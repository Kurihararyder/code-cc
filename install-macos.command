#!/bin/sh
# CPE 教練 安裝程式（macOS）。在 Finder 裡雙擊（第一次要按右鍵 → 打開），或在終端機執行：sh install-macos.command
HERE=$(cd "$(dirname "$0")" && pwd)
sh "$HERE/setup/bootstrap.sh" "$@"
rc=$?
if [ "$rc" -ne 0 ]; then
  echo
  echo "安裝沒有完成（代碼 $rc）。請把上面的訊息複製給我。按 Enter 關閉。"
  read -r _
fi
exit $rc
