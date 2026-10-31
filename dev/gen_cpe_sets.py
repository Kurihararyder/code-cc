"""產生 cpe_coach/data/cpe_sets.json（CPE 原題清單：題號與標題）和 tests/fixtures/cpe_repo_digests.json（驗證用的雜湊）。

用法：git clone https://github.com/LuckyPigeon/CPE_Previous_Questions 之後
      python dev/gen_cpe_sets.py <那個資料夾>
只存「題號、標題、屬於哪個集合」這些事實；題目敘述有版權，不存。
雜湊檔只有 SHA-256（每題範例輸入輸出經過空白正規化之後的雜湊），用來在 CI 偵測擷取結果有沒有變，內容無法從雜湊還原。
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from cpe_coach import cpeimport, service, uvastatement  # noqa: E402

# 有些 PDF 沒有標題列（或標題讀不出來）：用 UVa 官方的題目名稱補上
TITLE_FALLBACK = {10189: "Minesweeper", 11456: "Trainsorting"}
SETS = {"one": "一星題", "two": "二星題", "past": "歷屆試題"}


def norm(text: str) -> str:
    return " ".join(text.split())


def main(folder: str) -> int:
    src = Path(folder)
    commit = ""
    head = src / ".git" / "HEAD"
    if head.exists():
        import subprocess
        commit = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    found = cpeimport.scan_folder(src)
    by_key = {}
    for f in found:
        by_key.setdefault(f.key, {})[f.number] = f
    old = json.loads((REPO / "cpe_coach" / "data" / "cpe_sets.json").read_text(encoding="utf-8")) if (REPO / "cpe_coach" / "data" / "cpe_sets.json").exists() else {}
    bank = {}
    for name in ("problems.json", "problems_extra.json"):
        for p in json.loads((REPO / "cpe_coach" / "data" / name).read_text(encoding="utf-8")):
            bank[p.get("number")] = p["title"]
    out_sets = {}
    digests = {}
    for key, dirname in SETS.items():
        problems = []
        folders = sorted(int(d.name) for d in (src / dirname).iterdir() if d.is_dir() and d.name.isdigit())
        for n in folders:
            f = by_key.get(key, {}).get(n)
            if f is not None:
                st = uvastatement.from_pdf(f.read())
                title = (st.title or TITLE_FALLBACK.get(n, "")).replace("’", "'").replace("‘", "'")
                samples = service.parse_samples(st.text)
                digests[str(n)] = [hashlib.sha256((norm(a) + "\n---\n" + norm(b)).encode("utf-8")).hexdigest() for a, b in samples]
                problems.append({"uva": n, "title": title})
            else:
                title = bank.get(n) or next((p["title"] for k in old.get("sets", {}) for p in old["sets"][k]["problems"] if p["uva"] == n), None)
                problems.append(dict({"uva": n, "title": title or f"UVA {n}", "no_pdf": True}, **({} if title else {"title_unknown": True})))
        out_sets[key] = {"name": dirname, "problems": problems}
    data = {
        "_note": "社群整理的 CPE 題目清單。只收題號與標題（事實）；題目敘述有版權，不內建，匯入時才從 GitHub 下載到使用者自己的電腦。no_pdf：該 repo 裡這題沒有 PDF。",
        "source": {"repo": "https://github.com/LuckyPigeon/CPE_Previous_Questions", "commit": commit or old.get("source", {}).get("commit", ""),
                   "license": "MIT（repo 本身）；題目敘述的著作權屬於各題作者"},
        "sets": out_sets,
    }
    (REPO / "cpe_coach" / "data" / "cpe_sets.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    fx = REPO / "tests" / "fixtures"
    fx.mkdir(parents=True, exist_ok=True)
    (fx / "cpe_repo_digests.json").write_text(json.dumps({"commit": data["source"]["commit"], "digests": digests}, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print({k: len(v["problems"]) for k, v in out_sets.items()}, "digests:", len(digests))
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
