#!/bin/bash
# 一次跑完所有介面測試（本機與 CI 共用）。需要 Node、playwright（含 chromium）、python3。
# 每個腳本前都重建全新工作區；任何 FAIL、node 非 0 結束（例外／逾時）、或沒印出任何 PASS 都算失敗。
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
E2E_DIR="${E2E_DIR:-/tmp/cpe-e2e}"; mkdir -p "$E2E_DIR"
export E2E_DIR
python3 "$ROOT/dev/fake_llm.py" 8792 >"$E2E_DIR/llm.log" 2>&1 &
LLM=$!
python3 "$HERE/fake_github.py" 8794 >"$E2E_DIR/github.log" 2>&1 &
GH=$!
export CPE_QUESTIONS_URL=http://127.0.0.1:8794/archive.zip
cleanup() { kill "$LLM" "$GH" 2>/dev/null; [ -f "$E2E_DIR/web.pid" ] && kill "$(cat "$E2E_DIR/web.pid")" 2>/dev/null; }
trap cleanup EXIT
sleep 1
status=0
for t in ui gate mobile a11y exam learn cpe; do
  "$HERE/fresh.sh" >/dev/null || { echo "fresh.sh 失敗"; exit 1; }
  echo "=== $t"
  (cd "$E2E_DIR" && timeout 600 node "$HERE/$t.js" 2>&1) | tee "$E2E_DIR/$t.log"
  rc=${PIPESTATUS[0]}                                   # node 本身的結束碼：中途當掉（例外、逾時）也要算失敗
  if [ "$rc" -ne 0 ] || grep -q "^FAIL" "$E2E_DIR/$t.log" || ! grep -q "^PASS" "$E2E_DIR/$t.log"; then echo "✗ $t 失敗（結束碼 $rc）"; status=1; fi
done
[ $status -eq 0 ] && echo "✓ 全部介面測試通過" || echo "✗ 有介面測試失敗"
exit $status
