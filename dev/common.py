"""共用：題目註冊。"""
import random

DRILLS = []


def D(id, title, stage, topic, statement, inp, out, cat, insight, ref, cases, note="", diff=1, timeout=10, reserve=False):
    DRILLS.append(dict(id=id, title=title, stage=stage, topic=topic, statement=statement.strip(), inp=inp.strip(),
                       out=out.strip(), cat=cat, insight=insight, ref=ref, cases=cases, note=note.strip(),
                       diff=diff, timeout=timeout, reserve=reserve))


def lines(*xs):
    return "\n".join(str(x) for x in xs) + "\n"


def rng(seed):
    return random.Random(seed)
