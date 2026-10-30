"""產生每題的英文版題目 cpe_coach/data/drills/<id>/statement.en.md，並在 index.json 補上 title_en／topic_en。
不會動到既有的中文題目敘述與測資（範例取自 tests/case01）。內容來自 dev/en/en_*.py。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "cpe_coach" / "data" / "drills"
sys.path.insert(0, str(Path(__file__).parent / "en"))

import en_s0a, en_s1, en_s2  # noqa: E402

EN = {}
for m in (en_s0a, en_s1, en_s2):
    EN.update(m.EN)


def render(pid, e, stage, diff, sample_in, sample_out):
    title, statement, inp, out, note, topic = e
    return f"""# {pid} {title}

**Stage {stage} · Difficulty {'★' * diff} · Topic: {topic}**

{statement}

## Input
{inp}

## Output
{out}

## Sample Input
```
{sample_in.rstrip(chr(10))}
```

## Sample Output
```
{sample_out.rstrip(chr(10))}
```
""" + (f"\n## Notes\n{note}\n" if note else "")


def main():
    idx_path = OUT / "index.json"
    bank = json.loads(idx_path.read_text(encoding="utf-8"))
    ids = {p["id"] for p in bank}
    assert ids == set(EN), (ids ^ set(EN))
    for p in bank:
        pid = p["id"]
        base = OUT / pid
        s_in = (base / "tests" / "case01.in").read_text(encoding="utf-8")
        s_out = (base / "tests" / "case01.out").read_text(encoding="utf-8")
        e = EN[pid]
        (base / "statement.en.md").write_text(render(pid, e, p["course_stage"], p["difficulty"], s_in, s_out), encoding="utf-8")
        p["title_en"], p["topic_en"] = e[0], e[5]
    idx_path.write_text(json.dumps(bank, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(bank)} 題英文版已寫入")


if __name__ == "__main__":
    main()
