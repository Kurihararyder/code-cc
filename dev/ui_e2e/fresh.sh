#!/bin/bash
# 重新啟動一個全新工作區的 cpe web（port 8793）
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
E2E_DIR="${E2E_DIR:-/tmp/cpe-e2e}"; mkdir -p "$E2E_DIR"; cd "$E2E_DIR"
[ -f web.pid ] && kill "$(cat web.pid)" 2>/dev/null
sleep 0.5
rm -rf ws shots && mkdir shots
export PYTHONPATH="$ROOT"
python3 -m cpe_coach init ws >/dev/null
cd ws
CPE_API_BASE=http://127.0.0.1:8792/v1 OPENAI_API_KEY=fake nohup python3 -m cpe_coach web --no-open --port 8793 > "$E2E_DIR/web.log" 2>&1 &
echo $! > "$E2E_DIR/web.pid"
sleep 1.5
curl -s -o /dev/null -w "server %{http_code}\n" http://127.0.0.1:8793/
