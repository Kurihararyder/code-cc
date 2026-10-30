"""cpe update：用暫存的 git 倉庫模擬『我在雲端改完、推上 GitHub，使用者在電腦端更新』。"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cpe_coach
from cpe_coach import cli, updater

HAVE_GIT = shutil.which("git") is not None
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")


def git(cwd, *args):
    p = subprocess.run(["git", "-C", str(cwd)] + list(args), capture_output=True, env=ENV)
    assert p.returncode == 0, (args, p.stderr.decode("utf-8", "replace"))
    return p.stdout.decode("utf-8").strip()


def write_version(root, version, extra=""):
    (root / "cpe_coach").mkdir(parents=True, exist_ok=True)
    (root / "cpe_coach" / "__init__.py").write_text(f'__version__ = "{version}"\n{extra}', encoding="utf-8")
    (root / "cpe_coach" / "cli.py").write_text("def main(argv=None):\n    return 0\n", encoding="utf-8")


CHANGELOG = """# 更新紀錄

## 2.2.0（2026-02-01）
- 新增：第三個功能。

## 2.1.0（2026-01-15）
- 新增：第二個功能。

## 2.0.0（2026-01-01）
- 第一版。
"""


@unittest.skipUnless(HAVE_GIT, "需要 git")
class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin, self.clone = base / "origin", base / "clone"
        self.origin.mkdir()
        git(self.origin, "init", "-q", "-b", "work")
        write_version(self.origin, "2.0.0")
        (self.origin / "CHANGELOG.md").write_text(CHANGELOG.split("## 2.2.0")[0] + "## 2.0.0（2026-01-01）\n- 第一版。\n", encoding="utf-8")
        git(self.origin, "add", "-A")
        git(self.origin, "commit", "-q", "-m", "first")
        subprocess.run(["git", "clone", "-q", "-b", "work", str(self.origin), str(self.clone)], check=True, capture_output=True, env=ENV)

    def tearDown(self):
        self.tmp.cleanup()

    def publish(self, version, subject, extra="", changelog=None):
        write_version(self.origin, version, extra)
        if changelog:
            (self.origin / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
        git(self.origin, "add", "-A")
        git(self.origin, "commit", "-q", "-m", subject)

    def test_up_to_date(self):
        r = updater.apply(self.clone)
        self.assertEqual((r["status"], r["behind"], r["ahead"]), ("up_to_date", 0, 0))
        self.assertEqual(r["version"], "2.0.0")

    def test_check_reports_without_changing_files(self):
        self.publish("2.1.0", "Add feature two")
        self.publish("2.2.0", "Add feature three")
        before = git(self.clone, "rev-parse", "HEAD")
        r = updater.apply(self.clone, check_only=True)
        self.assertEqual((r["status"], r["behind"]), ("available", 2))
        self.assertEqual([c[1] for c in r["commits"]], ["Add feature three", "Add feature two"])
        self.assertEqual(git(self.clone, "rev-parse", "HEAD"), before)
        self.assertEqual(updater.read_version(self.clone), "2.0.0")

    def test_update_fast_forwards_and_shows_changelog_for_new_versions_only(self):
        self.publish("2.1.0", "two")
        self.publish("2.2.0", "three", changelog=CHANGELOG)
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "updated")
        self.assertEqual((r["old_version"], r["new_version"]), ("2.0.0", "2.2.0"))
        self.assertEqual(updater.read_version(self.clone), "2.2.0")
        self.assertIn("第三個功能", r["notes"])
        self.assertIn("第二個功能", r["notes"])
        self.assertNotIn("第一版", r["notes"])                   # 已經有的版本不重複列出
        self.assertEqual(updater.apply(self.clone)["status"], "up_to_date")

    def test_local_modification_blocks_update_and_is_kept(self):
        self.publish("2.1.0", "two")
        (self.clone / "cpe_coach" / "cli.py").write_text("# my edit\n", encoding="utf-8")
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "blocked")
        self.assertIn("cli.py", r["reason"])
        self.assertEqual((self.clone / "cpe_coach" / "cli.py").read_text(encoding="utf-8"), "# my edit\n")
        self.assertEqual(updater.read_version(self.clone), "2.0.0")

    def test_unpushed_local_commit_blocks_update(self):
        self.publish("2.1.0", "two")
        (self.clone / "mine.txt").write_text("x", encoding="utf-8")
        git(self.clone, "add", "-A")
        git(self.clone, "commit", "-q", "-m", "local work")
        r = updater.apply(self.clone)
        self.assertEqual((r["status"], r["ahead"], r["behind"]), ("blocked", 1, 1))
        self.assertIn("還沒推送", r["reason"])

    def test_broken_new_version_is_rolled_back(self):
        old = git(self.clone, "rev-parse", "--short", "HEAD")
        self.publish("2.1.0", "oops", extra="raise RuntimeError('boom')\n")
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "rolled_back")
        self.assertIn("boom", r["reason"])
        self.assertEqual(git(self.clone, "rev-parse", "--short", "HEAD"), old)
        self.assertEqual(updater.read_version(self.clone), "2.0.0")
        self.assertEqual(git(self.clone, "status", "--porcelain", "--untracked-files=no"), "")

    def test_rollback_does_not_leave_stale_bytecode_for_a_same_size_edit(self):
        """版本號 2.0.0 ↔ 2.1.0 長度一樣、又在同一秒內改回來：舊的 .pyc 會被誤認為有效，退回後實際跑的還是新版（壞掉的）程式。"""
        self.publish("2.1.0", "same size, broken", extra="raise RuntimeError('boom')\n")
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "rolled_back")
        self.assertEqual(list((self.clone / "cpe_coach").rglob("*.pyc")), [])             # 驗證時不寫 .pyc；退回後也沒有殘留
        out = subprocess.run([sys.executable, "-c", "import cpe_coach; print(cpe_coach.__version__)"], cwd=str(self.clone), capture_output=True, env=dict(os.environ, PYTHONPATH=str(self.clone)))
        self.assertEqual(out.stdout.decode().strip(), "2.0.0", out.stderr.decode())

    def test_update_does_not_leave_stale_bytecode_for_a_same_size_edit(self):
        """程式剛跑過（寫了 .pyc）、同一秒內更新成長度一樣的版本號（2.0.0 → 2.1.0）：更新後再啟動，跑的必須是新版（服務重新啟動時就是這樣）。"""
        env = dict(os.environ, PYTHONPATH=str(self.clone))
        subprocess.run([sys.executable, "-c", "import cpe_coach"], cwd=str(self.clone), env=env, check=True)        # 寫下 __pycache__
        self.assertTrue(list((self.clone / "cpe_coach").rglob("*.pyc")))
        self.publish("2.1.0", "same size, fine")
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "updated", r)
        out = subprocess.run([sys.executable, "-c", "import cpe_coach; print(cpe_coach.__version__)"], cwd=str(self.clone), capture_output=True, env=env)
        self.assertEqual(out.stdout.decode().strip(), "2.1.0", out.stderr.decode())

    def test_not_a_git_checkout_and_no_upstream_and_detached(self):
        plain = Path(self.tmp.name) / "plain"
        write_version(plain, "1.0.0")
        r = updater.apply(plain)
        self.assertEqual(r["status"], "unavailable")
        self.assertIn("INSTALL.md", r["reason"])
        git(self.clone, "branch", "--unset-upstream")
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "unavailable")
        self.assertIn("set-upstream-to", r["reason"])
        git(self.clone, "checkout", "-q", "--detach")
        self.assertIn("detached", updater.apply(self.clone)["reason"])

    def test_network_failure_is_reported_not_raised(self):
        git(self.clone, "remote", "set-url", "origin", str(Path(self.tmp.name) / "gone"))
        r = updater.apply(self.clone)
        self.assertEqual(r["status"], "unavailable")
        self.assertIn("git fetch", r["reason"])

    def test_git_missing(self):
        with mock.patch("cpe_coach.updater.shutil.which", return_value=None):
            r = updater.apply(self.clone)
        self.assertEqual(r["status"], "unavailable")
        self.assertIn("找不到 git", r["reason"])


class HelperTests(unittest.TestCase):
    def test_version_parsing_and_changelog_slice(self):
        self.assertLess(updater.parse_version("2.9.0"), updater.parse_version("2.10.0"))
        self.assertEqual(updater.changelog_since(CHANGELOG, "2.1.0", "2.2.0").splitlines()[0], "## 2.2.0（2026-02-01）")
        self.assertEqual(updater.changelog_since(CHANGELOG, "2.2.0", "2.2.0"), "")
        self.assertEqual(updater.changelog_since("", "1", "2"), "")

    def test_version_has_a_single_source_and_matches_the_real_changelog(self):
        root = Path(cpe_coach.__file__).resolve().parent.parent
        self.assertEqual(updater.read_version(root), cpe_coach.__version__)
        pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('dynamic = ["version"]', pyproject)               # 版本只寫在 cpe_coach/__init__.py
        self.assertNotRegex(pyproject, r'(?m)^version\s*=\s*"')
        changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        import re
        self.assertEqual(re.search(r"(?m)^## (\d+(?:\.\d+)*)", changelog).group(1), cpe_coach.__version__)      # 最新一節就是目前版本

    def test_cli_version_and_update_command(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            cli.main(["--version"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn(cpe_coach.__version__, buf.getvalue())
        fake = {"status": "available", "branch": "b", "commit": "abc", "upstream": "origin/b", "behind": 2, "ahead": 0,
                "commits": [("111", "feat one"), ("222", "feat two")]}
        buf = io.StringIO()
        with mock.patch("cpe_coach.updater.apply", return_value=fake), contextlib.redirect_stdout(buf):
            rc = cli.main(["update", "--check"])
        self.assertEqual(rc, 0)
        self.assertIn("2 個新的更新", buf.getvalue())
        buf = io.StringIO()
        with mock.patch("cpe_coach.updater.apply", return_value={"status": "unavailable", "reason": "不是 git 安裝"}), contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["update"]), 1)
        self.assertIn("不是 git 安裝", buf.getvalue())
        upd = {"status": "updated", "branch": "b", "commit": "abc", "upstream": "origin/b", "old_version": "2.0.0", "new_version": "2.1.0",
               "old_commit": "abc", "new_commit": "def", "notes": "## 2.1.0\n- 新功能"}
        buf = io.StringIO()
        with mock.patch("cpe_coach.updater.apply", return_value=upd), contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["update"]), 0)
        self.assertIn("2.0.0（abc）→ 2.1.0（def）", buf.getvalue())
        self.assertIn("reset --hard abc", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
