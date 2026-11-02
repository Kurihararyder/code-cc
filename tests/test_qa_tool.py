"""dev/qa.py（題目與測資的品質檢查）本身要能用：挑幾題跑，並確認『壞題』真的會被抓到。"""
import subprocess
import sys
import unittest
from pathlib import Path

DEV = Path(__file__).resolve().parent.parent / "dev"


def run_qa(*ids):
    return subprocess.run([sys.executable, str(DEV / "qa.py"), "--quick", *ids], capture_output=True, text=True, timeout=300, cwd=str(DEV))


class QaToolTests(unittest.TestCase):
    def test_a_few_drills_pass(self):
        r = run_qa("d001", "d007", "d021", "d111")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("4/4", r.stdout)

    def test_a_weak_test_set_is_reported(self):
        """把 d007 的『被錯誤解漏掉的年份』拿掉，檢查工具要指出有錯誤解沒被抓到。"""
        code = r"""
import sys
sys.path.insert(0, %r)
import qa
qa.load()
d = qa._REF["d007"]
d["cases"] = [c for c in d["cases"] if not any(x in (c[0] if isinstance(c, tuple) else c) for x in ("200\n", "300\n"))]
q = qa.QA["d007"]; q["nrand"] = 0
probs = qa.check("d007", rounds=5)
print("\n".join(probs))
""" % str(DEV)
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300, cwd=str(DEV))
        self.assertIn("錯誤解沒被測資抓到", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
