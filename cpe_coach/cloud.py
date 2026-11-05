"""學程雲端（Supabase）：學號登入、授權檢查、進度同步、AI 代理、管理後台。只用標準函式庫。

安全模型（誠實版）：
- 所有『授權判斷』都在伺服器端（Postgres 的 RLS／函式與 Edge Function）：帳號有沒有啟用、授權期間、IP 允許清單、AI 有沒有開放。
  客戶端只拿到『可以／不可以』與原因；IP 是伺服器看到的連線來源，客戶端無法自報。
- 程式碼在學員電腦上，會寫程式的人可以改掉本機的檢查（這是任何本機程式的共同限制）。所以真正被伺服器保護的是：
  雲端進度、AI 額度與金鑰（OpenAI 金鑰只存在資料庫，由 Edge Function 代為呼叫，學員電腦上從來沒有）。
- 離線寬限：連不上伺服器時，用『上一次伺服器確認通過』的結果，最多撐 grace_hours（預設 72 小時），而且不會超過授權到期時間。
- 公開的 publishable key 只是『門牌』：沒有登入就什麼都讀不到（RLS）；不要把 service_role 金鑰放進任何程式碼。
"""
from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

CONFIG_PATH = Path(__file__).parent / "data" / "cloud.json"
CHECK_EVERY = 600            # 秒：多久向伺服器重新確認一次授權
REASONS = {
    "inactive": "帳號尚未開通。請洽學程管理員啟用。",
    "not_started": "授權期間還沒開始。",
    "expired": "授權已到期。請洽學程管理員延長。",
    "ip_denied": "目前的網路位址不在允許清單內（請連學校網路，或洽管理員）。",
    "ip_unknown": "伺服器無法判斷你的網路位址。",
    "no_profile": "找不到帳號資料，請洽管理員。",
    "no_session": "尚未登入。",
    "offline_expired": "已經太久沒有連線到學程伺服器，請連上網路後重新驗證。",
    "offline_never": "第一次使用必須連上網路登入。",
}
Http = Callable[[str, str, Dict[str, str], Optional[bytes], float], Tuple[int, Any]]


class CloudError(Exception):
    def __init__(self, msg: str, status: int = 0, reason: str = ""):
        super().__init__(msg)
        self.status, self.reason = status, reason


def load_config(env: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """沒有設定檔、或環境變數 CPE_CLOUD=off 時回傳 None（不要求登入）。"""
    env = os.environ if env is None else env
    if env.get("CPE_CLOUD", "").strip().lower() in ("off", "0", "no", "false"):
        return None
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    cfg["url"] = (env.get("CPE_CLOUD_URL") or cfg.get("url", "")).rstrip("/")
    cfg["key"] = env.get("CPE_CLOUD_KEY") or cfg.get("key", "")
    return cfg if cfg["url"] and cfg["key"] else None


def _http(method: str, url: str, headers: Dict[str, str], body: Optional[bytes], timeout: float) -> Tuple[int, Any]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw, code = r.read(), r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read(), e.code
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        raise CloudError(f"連不上學程伺服器：{getattr(e, 'reason', e)}", 0, "network")
    try:
        return code, (json.loads(raw.decode("utf-8")) if raw else None)
    except ValueError:
        return code, {"error": raw.decode("utf-8", "replace")[:200]}


def _iso(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


class Cloud:
    def __init__(self, cfg: Dict[str, Any], root: Path, http: Http = _http, clock: Callable[[], float] = time.time):
        self.cfg, self.root, self.http, self.clock = cfg, Path(root), http, clock
        self.url, self.key = cfg["url"], cfg["key"]
        self.domain = cfg.get("domain", "icd-cpe.example.com")
        self.path = self.root / ".cpe" / "cloud.json"
        self.sess: Dict[str, Any] = self._load()
        self.last_error: Optional[str] = None
        self.last_sync: Optional[Dict[str, Any]] = None
        self.app_info: Dict[str, Any] = self.sess.get("app") or {}

    # ---------- 儲存 ----------
    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.sess, ensure_ascii=False), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)

    # ---------- HTTP ----------
    def _call(self, method: str, path: str, body: Any = None, token: Optional[str] = None, timeout: float = 15.0) -> Tuple[int, Any]:
        h = {"apikey": self.key, "Content-Type": "application/json", "Authorization": "Bearer " + (token or self.key)}
        return self.http(method, self.url + path, h, None if body is None else json.dumps(body).encode("utf-8"), timeout)

    def app_info_public(self) -> Dict[str, Any]:
        """不用登入：最新版本、最低版本、公告。"""
        code, j = self._call("POST", "/rest/v1/rpc/app_info", {}, timeout=8)
        if code == 200 and isinstance(j, dict):
            self.app_info = j
            return j
        raise CloudError("讀取版本資訊失敗", code)

    # ---------- 登入 ----------
    def email(self, sid: str) -> str:
        return f"{sid.strip().lower()}@{self.domain}"

    def login(self, sid: str, password: str) -> Dict[str, Any]:
        sid = sid.strip().lower()
        if not sid or not password:
            raise CloudError("請輸入學號與密碼")
        code, j = self._call("POST", "/auth/v1/token?grant_type=password", {"email": self.email(sid), "password": password})
        if code != 200 or not isinstance(j, dict) or "access_token" not in j:
            if code in (400, 401, 422):
                raise CloudError("學號或密碼錯誤", code, "bad_credentials")
            if code == 429:
                raise CloudError("嘗試次數太多，請稍後再試", code, "rate_limited")
            raise CloudError(f"登入失敗（HTTP {code}）", code)
        self.sess = {"sid": sid, "access": j["access_token"], "refresh": j.get("refresh_token"),
                     "expires_at": self.clock() + int(j.get("expires_in", 3600))}
        self._save()
        return self.check(login=True)

    def logout(self) -> None:
        self.sess = {}
        try:
            self.path.unlink()
        except OSError:
            pass

    def _token(self) -> str:
        s = self.sess
        if not s.get("access"):
            raise CloudError("尚未登入", 401, "no_session")
        if s.get("expires_at", 0) - 60 > self.clock():
            return s["access"]
        code, j = self._call("POST", "/auth/v1/token?grant_type=refresh_token", {"refresh_token": s.get("refresh")})
        if code == 200 and isinstance(j, dict) and "access_token" in j:
            s.update(access=j["access_token"], refresh=j.get("refresh_token", s.get("refresh")), expires_at=self.clock() + int(j.get("expires_in", 3600)))
            self._save()
            return s["access"]
        if code in (400, 401, 403):                          # 憑證失效（密碼被重設、帳號被刪）：要求重新登入
            self.logout()
            raise CloudError("登入已失效，請重新登入", 401, "no_session")
        raise CloudError(f"更新登入憑證失敗（HTTP {code}）", code)

    def rpc(self, name: str, args: Optional[Dict[str, Any]] = None, timeout: float = 20.0) -> Any:
        code, j = self._call("POST", f"/rest/v1/rpc/{name}", args or {}, self._token(), timeout)
        if code == 401:
            self.logout()
            raise CloudError("登入已失效，請重新登入", 401, "no_session")
        if code >= 400:
            msg = (j or {}).get("message") if isinstance(j, dict) else None
            raise CloudError(msg or f"伺服器錯誤（HTTP {code}）", code, "denied" if code in (401, 403) else "")
        return j

    def fn(self, name: str, body: Dict[str, Any], timeout: float = 60.0) -> Any:
        code, j = self._call("POST", f"/functions/v1/{name}", body, self._token(), timeout)
        if code >= 400:
            raise CloudError((j or {}).get("error") if isinstance(j, dict) and j.get("error") else f"伺服器錯誤（HTTP {code}）", code, (j or {}).get("reason", "") if isinstance(j, dict) else "")
        return j

    # ---------- 授權 ----------
    def check(self, login: bool = False) -> Dict[str, Any]:
        """向伺服器確認授權。連不上時用上次通過的結果（離線寬限）。"""
        try:
            r = self.rpc("check_access", {"p_login": login}, timeout=10)
            self.last_error = None
        except CloudError as e:
            if e.reason == "no_session" or e.status in (401, 403):
                raise
            self.last_error = str(e)
            return self._offline_access()
        info = r.pop("app", None) or {}
        self.app_info = info
        try:
            self.sess["notices"] = self.rpc("my_notices", timeout=10) if r.get("ok") else []
        except CloudError:
            pass                                             # 公告取不到不影響授權
        self.sess.update(acc=r, app=info, checked_at=self.clock())
        self._save()
        return r

    def _offline_access(self) -> Dict[str, Any]:
        acc = self.sess.get("acc")
        if not acc or not acc.get("ok"):
            return dict(acc or {}, ok=False, reason="offline_never" if not acc else acc.get("reason", "offline_expired"), offline=True)
        now = self.clock()
        checked = float(self.sess.get("checked_at", 0))
        grace = float((self.sess.get("app") or {}).get("grace_hours", 72)) * 3600
        until = _iso(acc.get("valid_until"))
        if now < checked - 300 or now - checked > grace:      # 時鐘被往回調、或離線太久
            return dict(acc, ok=False, reason="offline_expired", offline=True)
        if until is not None and now > until:
            return dict(acc, ok=False, reason="expired", offline=True)
        return dict(acc, offline=True, grace_left_h=round((grace - (now - checked)) / 3600, 1))

    def access(self, force: bool = False) -> Dict[str, Any]:
        """目前的授權狀態；超過 CHECK_EVERY 秒就重新向伺服器確認。"""
        if not self.sess.get("access"):
            return {"ok": False, "reason": "no_session"}
        elapsed = self.clock() - float(self.sess.get("checked_at", 0))
        if force or elapsed > CHECK_EVERY or elapsed < -300:           # 時鐘被往回調也要重新確認（離線時會被拒絕）
            try:
                acc = self.check()
                return acc
            except CloudError:
                return {"ok": False, "reason": "no_session"}
        acc = dict(self.sess.get("acc") or {"ok": False, "reason": "no_session"})
        until = _iso(acc.get("valid_until"))
        if acc.get("ok") and until is not None and self.clock() > until:   # 兩次檢查之間到期也要立刻擋住
            acc.update(ok=False, reason="expired")
        return acc

    def status(self, version: str = "") -> Dict[str, Any]:
        acc = self.access() if self.sess.get("access") else {"ok": False, "reason": "no_session"}
        info = self.app_info or {}
        need_update = bool(version and info.get("min_version") and _vt(version) < _vt(info["min_version"]))
        logged = bool(self.sess.get("access"))
        allowed = logged and bool(acc.get("ok")) and not acc.get("must_change_pw") and not need_update
        return {"enabled": True, "logged_in": logged, "allowed": allowed, "access": acc, "reason": acc.get("reason"),
                "message": REASONS.get(acc.get("reason", ""), ""), "offline": bool(acc.get("offline")), "need_update": need_update,
                "must_change_pw": bool(acc.get("must_change_pw")) and logged, "is_admin": acc.get("role") == "admin" and bool(acc.get("ok")),
                "user": {k: acc.get(k) for k in ("student_id", "name", "cohort", "role", "valid_from", "valid_until", "ai_allowed", "ip")} if logged else None,
                "app": info, "notices": self.sess.get("notices") or [], "last_sync": self.last_sync, "last_error": self.last_error, "org": self.cfg.get("org", "")}

    def change_password(self, new: str) -> None:
        if len(new) < 8:
            raise CloudError("新密碼至少 8 個字")
        code, j = self._call("PUT", "/auth/v1/user", {"password": new}, self._token())
        if code >= 400:
            msg = (j or {}).get("msg") or (j or {}).get("message") or f"HTTP {code}" if isinstance(j, dict) else f"HTTP {code}"
            if "different" in str(msg).lower():
                msg = "新密碼不能和舊密碼相同"
            raise CloudError(str(msg), code)
        self.rpc("pw_changed")
        self.access(force=True)

    # ---------- AI 代理 ----------
    def ai_available(self) -> Tuple[bool, str]:
        acc = self.sess.get("acc") or {}
        info = self.app_info or {}
        if not acc.get("ok"):
            return False, "尚未通過授權"
        if not info.get("ai_enabled"):
            return False, "學程管理員尚未開放 AI 功能"
        if not acc.get("ai_allowed"):
            return False, "你的帳號尚未被授權使用 AI（請洽管理員）"
        return True, ""

    def ai_client(self):
        from .llm import LLMClient, LLMError, _post
        ok, _ = self.ai_available()
        if not ok:
            return None

        def transport(url: str, headers: dict, body: dict) -> dict:
            try:
                tok = self._token()
            except CloudError as e:
                raise LLMError(str(e), 401)
            h = dict(headers, apikey=self.key, Authorization="Bearer " + tok)
            try:
                return _post(url, h, body, 90.0)
            except LLMError as e:
                if e.code in (403, 429, 503):               # 伺服器端的拒絕原因直接講給學員聽
                    try:
                        msg = json.loads(str(e).split("：", 1)[1]).get("error")
                        if msg:
                            raise LLMError(msg, e.code)
                    except (IndexError, ValueError, AttributeError):
                        pass
                raise

        return LLMClient("openai", "(學程代理)", "gpt-4o", transport=transport, base_url=self.url + "/functions/v1/ai-proxy", send_auth=False, retries=1)

    # ---------- 進度同步 ----------
    def sync(self, ws) -> Dict[str, Any]:
        """下載雲端進度 → 和本機合併 → 把合併結果傳回雲端。合併規則和『資料夾同步』相同（事件取聯集、進度逐欄位合併）。"""
        from . import sync as sync_mod
        r = self.rpc("load_progress", timeout=60)
        if not r.get("ok"):
            raise CloudError(REASONS.get(r.get("reason", ""), "沒有權限"), 403, r.get("reason", ""))
        with tempfile.TemporaryDirectory() as tmp:
            remote = Path(tmp) / sync_mod.DIRNAME
            if r.get("data"):
                _unpack(r["data"], remote)
            rep = sync_mod.sync_folder(ws, Path(tmp))
            data, summary = _pack(remote), summarize(ws)
        out = self.rpc("save_progress", {"p_data": data, "p_summary": summary, "p_device": _device()}, timeout=120)
        if not out.get("ok"):
            raise CloudError("上傳失敗：" + REASONS.get(out.get("reason", ""), out.get("reason", "")), 403, out.get("reason", ""))
        self.last_sync = {"at": self.clock(), "pulled_events": rep["events_added_local"], "pushed_events": rep["events_added_remote"],
                          "conflicts": len(rep["conflicts"]), "summary": summary}
        return self.last_sync


def _vt(v: str) -> Tuple[int, ...]:
    import re
    return tuple(int(x) for x in re.findall(r"\d+", v)[:4])


def _device() -> str:
    import platform
    return f"{platform.system()} {platform.node()}"[:60]


MAX_FILES_BYTES = 6_000_000


def _pack(remote: Path) -> Dict[str, Any]:
    """把 cpe-sync 資料夾（事件、進度、單字本、解答…）打成一份 JSON。檔案太大時只留事件與進度。"""
    out: Dict[str, Any] = {"format": 1, "files": {}}
    total = 0
    for f in sorted(remote.rglob("*")):
        if not f.is_file() or f.suffix == ".tmp":
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        rel = f.relative_to(remote).as_posix()
        total += len(text)
        if total > MAX_FILES_BYTES and rel.startswith("files/"):
            continue
        out["files"][rel] = text
    return out


def _unpack(data: Dict[str, Any], remote: Path) -> None:
    for rel, text in (data.get("files") or {}).items():
        p = (remote / rel).resolve()
        if remote.resolve() not in p.parents:                 # 路徑跳脫檢查（雲端資料不可信任）
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def summarize(ws, now: Optional[float] = None) -> Dict[str, Any]:
    """給管理員看的進度摘要（不含程式碼）：解題數、單元、活躍天數、近 4 週每週活躍天數、卡關的題（嘗試多次仍未通過）。"""
    now = time.time() if now is None else now
    st = ws.state()
    probs = st.get("problems", {})
    evs = ws.events()
    stamps = [float(e.get("ts", 0)) for e in evs if e.get("ts")]
    last = max(stamps, default=0)
    days = {time.strftime("%Y-%m-%d", time.localtime(t)) for t in stamps}
    weekly = []
    for w in range(3, -1, -1):                              # 最舊的在前：[3 週前, 2 週前, 上週, 本週]
        lo, hi = now - (w + 1) * 7 * 86400, now - w * 7 * 86400
        weekly.append(len({time.strftime("%Y-%m-%d", time.localtime(t)) for t in stamps if lo < t <= hi}))
    stuck = sorted(({"id": pid, "attempts": int(p.get("attempts", 0))} for pid, p in probs.items() if int(p.get("attempts", 0)) >= 4 and not p.get("first_pass")),
                   key=lambda x: -x["attempts"])[:5]
    return {"solved": sum(1 for p in probs.values() if p.get("first_pass")), "attempted": sum(1 for p in probs.values() if p.get("attempts")),
            "unit": (st.get("course") or {}).get("unit", 1), "events": len(evs), "last_active": last or None, "active_days": len(days),
            "exams": len(st.get("exams", [])), "weekly": weekly, "stuck": stuck}
