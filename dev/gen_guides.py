"""由 dev/guides/*.py 產生學習指南：docs/guides/<id>.md 與 cpe_coach/data/guides/<id>.json（網頁測驗用）。
逐題檢查選項與解析；帶 verify 的題目會實際用 tclsh／python／iverilog／g++ 執行，輸出對不上就失敗。"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "dev"))
import guide_lib as L  # noqa: E402
from cpe_coach import course  # noqa: E402

MIN_Q = 30


def stage_map(track: str, stage: int) -> str:
    c = course.load(track)
    rows = ["| 單元 | 週次 | 名稱 | 目標 |", "| --- | --- | --- | --- |"]
    for u in c["units"]:
        if u["stage"] == stage:
            a, b = course.week_range(u)
            rows.append(f"| {u['n']} | {a if a == b else f'{a}–{b}'} | {u['title']} | {u['goal']} |")
    return "\n".join(rows)


def load_guides():
    out = []
    for f in sorted((ROOT / "dev" / "guides").glob("*.py")):
        if f.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location("guide_" + f.stem, f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        out.append(m.GUIDE)
    return out


def main() -> int:
    guides = load_guides()
    (ROOT / "docs" / "guides").mkdir(parents=True, exist_ok=True)
    outdir = ROOT / "cpe_coach" / "data" / "guides"
    outdir.mkdir(parents=True, exist_ok=True)
    keep = set()
    index = []
    verified = total = 0
    for g in guides:
        g = dict(g)
        g["map"] = stage_map(g["track"], g["stage"])
        seen = set()
        nq = 0
        for grp in g["groups"]:
            for i, q in enumerate(grp["questions"], 1):
                where = f"{g['id']}／{grp['title']}／第 {i} 題"
                key = q["stem"] + "\n" + q["code"]
                if key in seen:
                    raise SystemExit(f"{where}：題幹與程式碼重複")
                seen.add(key)
                verified += L.check_question(q, where)
                nq += 1
        if nq < MIN_Q:
            raise SystemExit(f"{g['id']}：只有 {nq} 題，至少要 {MIN_Q} 題")
        total += nq
        (ROOT / "docs" / "guides" / f"{g['id']}.md").write_text(L.render_markdown(g), encoding="utf-8")
        data = L.to_quiz_json(g)
        (outdir / f"{g['id']}.json").write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        keep.add(f"{g['id']}.json")
        index.append({"id": g["id"], "track": g["track"], "stage": g["stage"], "title": g["title"], "questions": nq,
                      "groups": [{"title": grp["title"], "n": len(grp["questions"])} for grp in g["groups"]]})
    for f in outdir.glob("*.json"):
        if f.name not in keep and f.name != "index.json":
            f.unlink()
    (outdir / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"學習指南：{len(guides)} 份、{total} 題（其中 {verified} 題用程式實際執行驗證過答案）")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
