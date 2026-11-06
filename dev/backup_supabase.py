"""把學程資料庫匯出成 JSON（名單、設定、進度摘要、稽核紀錄；不含金鑰、密碼與學員的程式碼）。可排程（cron／工作排程器）每天跑。
用法：CPE_ADMIN_SID=admin CPE_ADMIN_PASSWORD=... python dev/backup_supabase.py [輸出資料夾]
密碼請放在環境變數或排程器的機密設定，不要寫進檔案。"""
import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cpe_coach import cloud  # noqa: E402


def main() -> int:
    sid, pw = os.environ.get("CPE_ADMIN_SID"), os.environ.get("CPE_ADMIN_PASSWORD")
    cfg = cloud.load_config({})
    if not (sid and pw and cfg):
        print("需要環境變數 CPE_ADMIN_SID 與 CPE_ADMIN_PASSWORD，以及 cpe_coach/data/cloud.json", file=sys.stderr)
        return 2
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        c = cloud.Cloud(cfg, Path(tmp))
        c.login(sid, pw)
        data = c.rpc("admin_export", timeout=120)
    f = out / f"cpe-db-{dt.date.today().isoformat()}.json"
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(f, 0o600)
    except OSError:
        pass
    print(f"已寫入 {f}（{len(data['profiles'])} 個帳號、{len(data['progress'])} 份進度）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
