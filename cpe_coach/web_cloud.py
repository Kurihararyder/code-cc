"""網頁介面的雲端部分：登入閘門、授權狀態、進度同步、管理後台代理、自動更新與重新啟動。
瀏覽器只和本機伺服器講話；Supabase 的憑證只存在本機工作區（.cpe/cloud.json，權限 600），不進入網頁。"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Optional

from . import __version__, updater
from .cloud import Cloud, CloudError

ADMIN_RPC = {"admin_list_users", "admin_update_user", "admin_bulk_update", "admin_get_settings", "admin_set_setting", "admin_secret_status",
             "admin_set_secret", "admin_audit", "admin_overview", "admin_ai_usage", "admin_set_archived", "admin_set_notices", "admin_expiring",
             "admin_insights", "admin_export", "admin_reports", "admin_resolve_report", "admin_anomalies", "admin_auto_archive", "admin_assign_save", "admin_assign_delete", "admin_assign_list", "admin_class_overview"}
ADMIN_FN = {"create_users", "reset_password", "delete_user"}
OPEN_GET = {"/api/ping", "/api/cloud/status"}
OPEN_POST = {"/api/cloud/login", "/api/cloud/logout", "/api/cloud/password", "/api/cloud/recheck", "/api/update/check", "/api/update/apply", "/api/restart"}


class CloudMixin:
    cloud: Optional[Cloud] = None
    httpd: Any = None
    update_info: Dict[str, Any] = {}

    # ---------- 閘門 ----------
    def gate(self, path: str, method: str) -> Optional[Dict[str, Any]]:
        """回傳 None 表示放行；否則回傳要給前端的狀態（HTTP 401）。"""
        if self.cloud is None or not path.startswith("/api/"):
            return None
        if path in (OPEN_GET if method == "GET" else OPEN_POST):
            return None
        st = self.cloud.status(__version__)
        return None if st["allowed"] else st

    def cloud_status(self, q: Dict[str, str]) -> Dict[str, Any]:
        if self.cloud is None:
            return {"enabled": False}
        st = self.cloud.status(__version__)
        st["update"] = self.update_info
        st["version"] = __version__
        ok, why = self.cloud.ai_available()
        st["ai"] = {"available": ok, "why": why}
        if st.get("assignments"):
            from . import tracks as tracks_mod
            st["assignments"] = tracks_mod.assignment_progress(self.ws(), st["assignments"])
        return st

    def cloud_login(self, body: Dict[str, Any]) -> Dict[str, Any]:
        if self.cloud is None:
            raise ValueError("沒有啟用學程登入")
        try:
            self.cloud.login(str(body.get("sid", "")), str(body.get("password", "")))
        except CloudError as e:
            raise ValueError(str(e))
        self.kick_sync()
        return self.cloud_status({})

    def cloud_logout(self, body: Dict[str, Any]) -> Dict[str, Any]:
        if self.cloud is not None:
            try:
                if self.cloud.status(__version__)["allowed"]:
                    self.cloud.sync(self.ws())
            except Exception:
                pass
            self.cloud.logout()
        return self.cloud_status({})

    def cloud_password(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.cloud.change_password(str(body.get("new", "")))
        except CloudError as e:
            raise ValueError(str(e))
        self.kick_sync()
        return self.cloud_status({})

    def cloud_recheck(self, body: Dict[str, Any]) -> Dict[str, Any]:
        if self.cloud is not None and self.cloud.sess.get("access"):
            try:
                self.cloud.access(force=True)
            except CloudError:
                pass
        try:
            self.cloud.app_info_public()
        except Exception:
            pass
        return self.cloud_status({})

    def cloud_sync(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            r = self.cloud.sync(self.ws())
        except CloudError as e:
            raise ValueError(str(e))
        return {"sync": r}

    def cloud_report(self, body: Dict[str, Any]) -> Dict[str, Any]:
        try:
            self.cloud.report_problem(str(body.get("id", "")), str(body.get("text", "")))
        except CloudError as e:
            raise ValueError(str(e))
        return {"ok": True}

    def kick_sync(self) -> None:
        """背景同步（登入後、之後每 10 分鐘）；失敗只記下原因，不打斷學習。"""
        if self.cloud is None or getattr(self, "_syncing", False):
            return
        self._syncing = True

        def run() -> None:
            try:
                self.cloud.sync(self.ws())
                self.cloud.last_error = None
            except Exception as e:
                self.cloud.last_error = f"同步失敗：{e}"
            finally:
                self._syncing = False

        threading.Thread(target=run, daemon=True).start()

    # ---------- 管理後台（伺服器端仍會再驗證管理員身分；這裡只是代為轉送）----------
    def _need_admin(self) -> None:
        if self.cloud is None or not self.cloud.status(__version__)["is_admin"]:
            raise ValueError("只有管理員可以使用")

    def admin_rpc(self, body: Dict[str, Any]) -> Dict[str, Any]:
        self._need_admin()
        name = str(body.get("name", ""))
        if name not in ADMIN_RPC:
            raise ValueError("不認得的管理操作")
        try:
            return {"result": self.cloud.rpc(name, body.get("args") or {})}
        except CloudError as e:
            raise ValueError(str(e))

    def admin_fn(self, body: Dict[str, Any]) -> Dict[str, Any]:
        self._need_admin()
        if body.get("action") not in ADMIN_FN:
            raise ValueError("不認得的管理操作")
        try:
            return self.cloud.fn("admin", {k: v for k, v in body.items()})
        except CloudError as e:
            raise ValueError(str(e))

    def admin_ai_test(self, body: Dict[str, Any]) -> Dict[str, Any]:
        self._need_admin()
        try:
            r = self.cloud.fn("ai-proxy", {"messages": [{"role": "user", "content": "只回覆一個字：OK"}], "max_tokens": 5})
            return {"ok": True, "reply": (r.get("choices") or [{}])[0].get("message", {}).get("content", ""), "model": r.get("model")}
        except CloudError as e:
            return {"ok": False, "error": str(e)}

    # ---------- 自動更新 ----------
    def bg_update(self, every: float = 1800.0) -> None:
        """啟動時與之後每 30 分鐘：向學程伺服器讀最低版本／公告，並檢查程式有沒有新版本（只檢查，不動檔案）。"""
        def run() -> None:
            while True:
                info: Dict[str, Any] = {"checked_at": time.time()}
                try:
                    if self.cloud is not None:
                        self.cloud.app_info_public()
                except Exception as e:
                    info["cloud_error"] = str(e)
                try:
                    r = updater.apply(updater.repo_root(), check_only=True)
                    info.update(status=r["status"], behind=r.get("behind", 0), reason=r.get("reason"),
                                commits=[{"sha": a, "subject": b} for a, b in r.get("commits", [])][:10])
                except Exception as e:
                    info.update(status="unavailable", reason=str(e))
                self.update_info = info
                if self.cloud is not None and self.cloud.sess.get("access") and self.cloud.status(__version__)["allowed"]:
                    self.kick_sync()
                time.sleep(every)

        threading.Thread(target=run, daemon=True).start()

    def update_apply(self, body: Dict[str, Any]) -> Dict[str, Any]:
        r = updater.apply(updater.repo_root(), check_only=False)
        out = {"status": r["status"], "reason": r.get("reason"), "notes": r.get("notes", ""), "new_version": r.get("new_version")}
        if r["status"] == "updated":
            self.update_info = {"checked_at": time.time(), "status": "restart", "behind": 0}
        return out

    def update_rollback(self, body: Dict[str, Any]) -> Dict[str, Any]:
        if self.cloud is not None:
            self._need_admin()
        r = updater.rollback(updater.repo_root())
        return {"status": r["status"], "reason": r.get("reason"), "version": r.get("version")}

    def restart(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """更新後用新程式重新啟動自己（同一個埠、同一個工作區）。回應送出後才動作。"""
        argv = [sys.executable, "-u", "-m", "cpe_coach", "web", "--port", str(self.port), "--no-open"]

        def go() -> None:
            time.sleep(0.6)
            if os.name == "nt":                          # Windows 的 exec 不會取代程序：先啟動一個等 1.5 秒（等舊的放掉埠）再啟動的新程序
                code = ("import sys,time; time.sleep(1.5); from cpe_coach.cli import main; "
                        f"sys.exit(main(['web','--port','{self.port}','--no-open']))")
                subprocess.Popen([sys.executable, "-c", code], cwd=os.getcwd(), creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
                os._exit(0)
            os.execv(sys.executable, argv)               # 同一個 pid；監聽的 socket 預設不會被繼承，所以埠會放掉

        threading.Thread(target=go, daemon=True).start()
        return {"restarting": True}
