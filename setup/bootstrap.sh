#!/bin/sh
# CPE 教練 安裝程式（macOS／Linux）。由 install-macos.command／install-linux.sh 呼叫，也可以直接執行：
#   sh setup/bootstrap.sh            找 Python 3.9 以上（沒有就協助安裝）→ 啟動安裝精靈
#   sh setup/bootstrap.sh --check    只檢查，不安裝任何東西、不改任何設定
#   sh setup/bootstrap.sh --yes      全部不詢問：缺 Python 或 tkinter 直接用套件管理員安裝，安裝精靈也用預設值（不開視窗）
# 其他參數原樣交給安裝精靈（例如 --text、--dir 路徑）。
set -u

OS=$(uname -s)
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(dirname "$HERE")
REPO=${CPE_REPO_SLUG:-Kurihararyder/code-cc}
BRANCH=${CPE_INSTALL_BRANCH:-claude/clever-archimedes-ekcn2m}
ARCHIVE=${CPE_ARCHIVE_URL:-https://github.com/$REPO/archive/refs/heads/$BRANCH.zip}
PKG_URL=https://www.python.org/ftp/python/3.12.10/python-3.12.10-macos11.pkg
PKG_SHA256=8373e58da4ea146b3eb1c1f9834f19a319440b6b679b06050b1f9ee3237aa8e4

CHECK=0
YES=0
n=$#
i=0
while [ "$i" -lt "$n" ]; do
  a=$1
  shift
  case "$a" in
    --check) CHECK=1 ;;
    --yes) YES=1; set -- "$@" "$a" ;;                  # 同時轉交給安裝精靈（不詢問、全用預設值）
    *) set -- "$@" "$a" ;;
  esac
  i=$((i + 1))
done

say() { printf '%s\n' "$*"; }

ask() {   # ask "問題" → 同意回傳 0。--yes 一律同意；沒有終端機輸入時不同意
  [ "$YES" -eq 1 ] && return 0
  [ -t 0 ] || return 1
  printf '%s [Y/n] ' "$1"
  read -r ans || return 1
  case "$ans" in "" | y | Y | yes | YES | 是 | 好) return 0 ;; *) return 1 ;; esac
}

py_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)' >/dev/null 2>&1; }

find_python() {   # find_python [tk]：加 tk 時只挑有圖形介面套件（tkinter）的
  fixed="/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 /Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
  [ -n "${CPE_NO_FIXED_PYTHON:-}" ] && fixed=""      # 測試用：只靠 PATH 找（模擬沒有 Python 的電腦；macOS 的 CI 機器在固定位置裝了 Python）
  for c in $fixed python3.13 python3.12 python3.11 python3.10 python3.9 python3 python; do
    p=$(command -v "$c" 2>/dev/null) || continue
    [ -x "$p" ] || continue
    # macOS 沒裝命令列開發者工具時，/usr/bin/python3 只是會跳出安裝視窗的空殼：不要去執行它
    if [ "$OS" = "Darwin" ] && [ "$p" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then continue; fi
    py_ok "$p" || continue
    if [ "${1:-}" = "tk" ] && ! "$p" -c 'import tkinter' >/dev/null 2>&1; then continue; fi
    printf '%s\n' "$p"
    return 0
  done
  return 1
}

linux_pm() {
  for m in apt-get dnf pacman zypper; do command -v "$m" >/dev/null 2>&1 && { printf '%s\n' "$m"; return 0; }; done
  return 1
}

as_root() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }

linux_install() {   # linux_install python | tk
  pm=$(linux_pm) || { say "找不到套件管理員（apt／dnf／pacman／zypper），請手動安裝。"; return 1; }
  case "$1:$pm" in
    python:apt-get) as_root apt-get update && as_root apt-get install -y python3 python3-tk ;;
    python:dnf) as_root dnf install -y python3 python3-tkinter ;;
    python:pacman) as_root pacman -S --noconfirm --needed python tk ;;
    python:zypper) as_root zypper --non-interactive install python3 python3-tk ;;
    tk:apt-get) as_root apt-get update && as_root apt-get install -y python3-tk ;;
    tk:dnf) as_root dnf install -y python3-tkinter ;;
    tk:pacman) as_root pacman -S --noconfirm --needed tk ;;
    tk:zypper) as_root zypper --non-interactive install python3-tk ;;
  esac
}

mac_install_python() {
  if command -v brew >/dev/null 2>&1; then
    say "用 Homebrew 安裝 Python 3.12（含圖形介面套件）…"
    brew install python@3.12 python-tk@3.12 && return 0
    say "Homebrew 沒有成功，改用 python.org 的安裝程式。"
  fi
  tmp=$(mktemp -d)
  say "下載 python.org 的 Python 3.12.10 安裝程式（約 45 MB）…"
  curl -fL --progress-bar -o "$tmp/python.pkg" "$PKG_URL" || { say "下載失敗，請到 https://www.python.org/downloads/ 手動安裝。"; return 1; }
  got=$(shasum -a 256 "$tmp/python.pkg" | cut -d' ' -f1)
  if [ "$got" != "$PKG_SHA256" ]; then say "下載的檔案雜湊值不符（${got}），為了安全已中止。"; return 1; fi
  say "雜湊值驗證通過。接下來會開啟 Apple 的安裝視窗，請一路按『繼續』並輸入你的電腦密碼。"
  open -W "$tmp/python.pkg"
  return 0
}

fetch_bundle() {   # 沒有程式資料夾（只下載了這個 sh）時：下載 zip 到暫存位置
  tmp=$(mktemp -d)
  say "下載程式…（${ARCHIVE}）"
  "$PY" - "$ARCHIVE" "$tmp" <<'PYEOF' || return 1
import sys, urllib.request, zipfile, pathlib
url, out = sys.argv[1], pathlib.Path(sys.argv[2])
data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "cpe-coach-installer"}), timeout=60).read()
(out / "src.zip").write_bytes(data)
with zipfile.ZipFile(out / "src.zip") as z:
    z.extractall(out / "x")
sub = [d for d in (out / "x").iterdir() if d.is_dir()]
print(sub[0] if sub else out / "x")
PYEOF
}

say "== CPE 教練 安裝程式（${OS}）"
PY=$(find_python tk) || PY=$(find_python) || PY=""
if [ -z "$PY" ]; then
  say "✗ 找不到 Python 3.9 以上。"
  if [ "$CHECK" -eq 1 ]; then
    [ "$OS" = "Darwin" ] && say "  （檢查模式）會用 Homebrew 或 python.org 的安裝程式安裝 Python 3.12。" || say "  （檢查模式）會用套件管理員（$(linux_pm || echo 無)）安裝 python3。"
    exit 0
  fi
  if ask "要自動安裝 Python 嗎？"; then
    if [ "$OS" = "Darwin" ]; then mac_install_python; else linux_install python; fi
    PY=$(find_python) || PY=""
  fi
  if [ -z "$PY" ]; then say "✗ 還是找不到 Python 3.9 以上。請先安裝 Python（https://www.python.org/downloads/），再重新執行。"; exit 1; fi
fi
say "✓ Python：${PY}（$("$PY" -c 'import sys; print(sys.version.split()[0])')）"

if "$PY" -c 'import tkinter' >/dev/null 2>&1; then
  say "✓ 圖形介面套件（tkinter）可用"
else
  say "! 這個 Python 沒有 tkinter，安裝精靈會用文字模式。"
  if [ "$OS" = "Linux" ] && [ "$CHECK" -eq 0 ] && ask "要安裝 python3-tk 以使用圖形介面嗎？"; then
    linux_install tk
    PY=$(find_python tk) || PY=$(find_python) || PY=""
  fi
fi

if [ -f "$ROOT/cpe_coach/launcher/__main__.py" ]; then
  BUNDLE=$ROOT
  say "✓ 程式資料夾：$BUNDLE"
elif [ "$CHECK" -eq 1 ]; then
  say "· 這裡沒有程式資料夾；正式安裝時會從 GitHub 下載（${ARCHIVE}）。"
  exit 0
else
  BUNDLE=$(fetch_bundle | tail -n 1) || { say "✗ 下載失敗，請確認網路。"; exit 1; }
fi

if [ "$CHECK" -eq 1 ]; then
  say "== 安裝診斷"
  PYTHONPATH=$BUNDLE "$PY" -m cpe_coach.launcher doctor
  exit 0
fi

exec "$PY" "$BUNDLE/cpe-panel.pyw" install --detach-gui "$@"
