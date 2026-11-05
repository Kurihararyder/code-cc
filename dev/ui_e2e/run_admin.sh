#!/usr/bin/env bash
# 管理後台的瀏覽器測試：假 Supabase（8794）＋真的 cpe web（8795），不連網。需要 playwright。
set -euo pipefail
cd "$(dirname "$0")/../.."
D=$(mktemp -d); trap 'kill $(jobs -p) 2>/dev/null || true; for pid in $(ps -eo pid,args | grep "[c]pe_coach web --no-open --port 8795" | awk "{print \$1}"); do kill $pid; done; rm -rf "$D"' EXIT
python3 dev/ui_e2e/fake_supabase.py 8794 & sleep 1
(cd "$D" && PYTHONPATH="$OLDPWD" python3 -m cpe_coach init >/dev/null && cd cpe-workspace && CPE_CLOUD_URL=http://127.0.0.1:8794 CPE_CLOUD_KEY=fake PYTHONPATH="$OLDPWD" python3 -m cpe_coach web --no-open --port 8795 >"$D/web.log" 2>&1) &
sleep 3
node dev/ui_e2e/admin.js http://127.0.0.1:8795/
