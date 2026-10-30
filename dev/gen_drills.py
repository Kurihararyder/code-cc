"""產生 cpe_coach/data/drills/<id>/{statement.md,meta.json,tests/*.in,*.out} 與題庫條目。"""
import json
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cpe_coach" / "data" / "drills"
sys.path.insert(0, str(Path(__file__).parent))

from common import DRILLS  # noqa: E402


def run_ref(code, text, timeout):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "ref.py"
        f.write_text(code, encoding="utf-8")
        p = subprocess.run([sys.executable, str(f)], input=text.encode(), capture_output=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode()[-500:])
    return p.stdout.decode()


def render(d, sample_in, sample_out):
    stars = "★" * d["diff"]
    return f"""# {d['id']} {d['title']}

**階段 {d['stage']}　難度 {stars}　主題：{d['topic']}**

{d['statement']}

## 輸入
{d['inp']}

## 輸出
{d['out']}

## 範例
輸入：
```
{sample_in.rstrip(chr(10))}
```
輸出：
```
{sample_out.rstrip(chr(10))}
```
""" + (f"\n## 這題在練什麼\n{d['note']}\n" if d["note"] else "")


def main():
    import drills_s0, drills_s1, drills_s2, drills_s3, drills_s4, drills_e  # noqa: F401  (註冊題目)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ids = [d["id"] for d in DRILLS]
    assert len(ids) == len(set(ids)), "重複 id"
    bank = []
    for d in DRILLS:
        base = OUT / d["id"]
        (base / "tests").mkdir(parents=True)
        for i, text in enumerate(d["cases"], 1):
            if isinstance(text, tuple):      # (輸入, 預期輸出覆蓋)
                text = text[0]
            out = run_ref(d["ref"], text, d["timeout"])
            (base / "tests" / f"case{i:02d}.in").write_text(text, encoding="utf-8")
            (base / "tests" / f"case{i:02d}.out").write_text(out, encoding="utf-8")
            if i == 1:
                s_in, s_out = text, out
        (base / "statement.md").write_text(render(d, s_in, s_out), encoding="utf-8")
        bank.append({"id": d["id"], "title": d["title"], "source": "drill", "stage": max(d["stage"], 1),
                     "course_stage": d["stage"], "difficulty": d["diff"], "topic": d["topic"],
                     "hint_category": d["cat"], "hint_insight": d["insight"], "url": None,
                     "official_one_star": False, "drill": True, "reserve": d["reserve"]})
    (OUT / "index.json").write_text(json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8")
    total = sum(len(d["cases"]) for d in DRILLS)
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"{len(DRILLS)} 題，{total} 組測資，{size/1024:.0f} KB")


if __name__ == "__main__":
    main()
