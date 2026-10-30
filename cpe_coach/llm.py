"""選用的 LLM 提示器（OpenAI 或 Anthropic，只用標準函式庫）。沒有金鑰時整個系統照常運作，只是少了 L0/L3/L4 的 AI 提示。"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

RULES = (Path(__file__).parent / "data" / "tutor_rules.md").read_text(encoding="utf-8")

DEFAULT_MODELS = {"openai": "gpt-4o", "anthropic": "claude-sonnet-5-5"}
DEFAULT_BASE = {"openai": "https://api.openai.com/v1", "anthropic": "https://api.anthropic.com/v1"}
# (provider, url, headers builder, body builder, response parser)
Transport = Callable[[str, dict, dict], dict]


class LLMError(Exception):
    """code：HTTP 狀態碼（連線失敗為 0；未知為 -1，不重試）；retry_after：伺服器要求的等待秒數。"""

    def __init__(self, msg: str, code: int = -1, retry_after: Optional[float] = None):
        super().__init__(msg)
        self.code, self.retry_after = code, retry_after


RETRY_CODES = (0, 408, 409, 429, 500, 502, 503, 504)


def _post(url: str, headers: dict, body: dict, timeout: float = 60.0) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        ra = e.headers.get("Retry-After") if e.headers else None
        try:
            wait = float(ra) if ra else None
        except ValueError:
            wait = None
        raise LLMError(f"API 回應 {e.code}：{e.read().decode('utf-8', 'replace')[:300]}", e.code, wait)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise LLMError(f"連線失敗：{e}", 0)
    except json.JSONDecodeError:
        raise LLMError("API 回應不是 JSON", 502)


class LLMClient:
    def __init__(self, provider: str, api_key: str, model: Optional[str] = None, transport: Transport = _post,
                 base_url: Optional[str] = None, sleep: Callable[[float], None] = time.sleep, retries: int = 2,
                 send_auth: bool = True):
        if provider not in DEFAULT_MODELS:
            raise LLMError(f"不支援的 provider：{provider}")
        self.provider, self.api_key, self.transport = provider, api_key, transport
        self.model = model or DEFAULT_MODELS[provider]
        self.base_url = (base_url or DEFAULT_BASE[provider]).rstrip("/")
        self.sleep, self.retries = sleep, retries
        self.send_auth = send_auth                     # False：認證標頭由外部代理加上（金鑰不進入這個程序）
        self.json_mode = provider == "openai"          # 要求 JSON 物件輸出；伺服器不支援時自動關掉
        self.usage_log: List[Dict[str, Any]] = []          # 每次呼叫的 token 與耗時（供費用與評測）

    def complete(self, system: str, user: str) -> str:
        return self.chat(system, [{"role": "user", "content": user}])

    # ---- 用量 ----
    def usage(self, since: int = 0) -> Dict[str, Any]:
        cs = self.usage_log[since:]
        return {"calls": len(cs), "tokens_in": sum(c["in"] for c in cs), "tokens_out": sum(c["out"] for c in cs),
                "seconds": round(sum(c["secs"] for c in cs), 2), "retries": sum(c["retries"] for c in cs)}

    def _send(self, url: str, headers: dict, body: dict) -> dict:
        """送出一次請求；暫時性錯誤（429／5xx／連線）最多重試 self.retries 次，指數退避並遵守 Retry-After。"""
        tries = 0
        while True:
            try:
                return self.transport(url, headers, body)
            except LLMError as e:
                if e.code not in RETRY_CODES or tries >= self.retries:
                    raise
                tries += 1
                self.sleep(min(20.0, e.retry_after if e.retry_after is not None else 1.5 * 2 ** (tries - 1)))
                self._last_retries = tries

    def chat(self, system: str, messages: List[Dict[str, str]]) -> str:
        t0 = time.perf_counter()
        self._last_retries = 0
        if self.provider == "openai":
            body: Dict[str, Any] = {"model": self.model, "messages": [{"role": "system", "content": system}] + list(messages)}
            headers = {"Content-Type": "application/json"}
            if self.send_auth:
                headers["Authorization"] = f"Bearer {self.api_key}"
            url = f"{self.base_url}/chat/completions"
            if self.json_mode:
                body["response_format"] = {"type": "json_object"}
            try:
                data = self._send(url, headers, body)
            except LLMError as e:
                if self.json_mode and e.code == 400 and "response_format" in str(e).lower():
                    self.json_mode = False                       # 這個模型／代理不支援：之後不再送這個參數
                    body.pop("response_format", None)
                    data = self._send(url, headers, body)
                else:
                    raise
            try:
                msg = data["choices"][0]["message"]
                text = msg.get("content") or ""
                if not text and msg.get("refusal"):
                    text = str(msg["refusal"])
            except (KeyError, IndexError, TypeError, AttributeError):
                raise LLMError("OpenAI 回應格式無法解析", 502)
            u = data.get("usage") or {}
            tin, tout = int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
        else:
            data = self._send(
                f"{self.base_url}/messages",
                dict({"x-api-key": self.api_key} if self.send_auth else {}, **{"anthropic-version": "2023-06-01", "Content-Type": "application/json"}),
                {"model": self.model, "max_tokens": 1024, "system": system, "messages": list(messages)},
            )
            try:
                text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
            except (KeyError, TypeError):
                raise LLMError("Anthropic 回應格式無法解析", 502)
            u = data.get("usage") or {}
            tin, tout = int(u.get("input_tokens") or 0), int(u.get("output_tokens") or 0)
        self.usage_log.append({"in": tin, "out": tout, "secs": time.perf_counter() - t0, "retries": self._last_retries})
        return text


def detect_client(cfg: Dict, env: Optional[Dict[str, str]] = None, key: Optional[str] = None) -> Optional[LLMClient]:
    """key：網頁介面暫存的金鑰（只存在記憶體）。CPE_API_BASE 可改成相容的代理網址。
    CPE_PROXY_AUTH=1：認證標頭由外部代理（例如雲端環境的『網路密鑰』）加上，這裡不需要、也不會送出金鑰。
    有明確給金鑰時一律以金鑰為準。"""
    env = os.environ if env is None else env
    provider = cfg.get("provider")
    model = cfg.get("model") or env.get("CPE_MODEL")
    base = env.get("CPE_API_BASE")
    keys = {"openai": env.get("OPENAI_API_KEY"), "anthropic": env.get("ANTHROPIC_API_KEY")}
    if key:
        keys["openai" if not provider or provider == "openai" else provider] = key
        provider = provider or "openai"
    proxy = env.get("CPE_PROXY_AUTH", "").strip().lower() in ("1", "true", "yes")
    if provider:
        if keys.get(provider):
            return LLMClient(provider, keys[provider], model, base_url=base)
        return LLMClient(provider, "", model, base_url=base, send_auth=False) if proxy else None
    for name in ("openai", "anthropic"):
        if keys[name]:
            return LLMClient(name, keys[name], model, base_url=base)
    if proxy:
        return LLMClient("anthropic" if env.get("CPE_PROVIDER") == "anthropic" else "openai", "", model, base_url=base, send_auth=False)
    return None


_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
REMOVED = "[⚠ 程式碼過長，已被系統移除。請用自己的話寫出實作。]"


def strip_long_code(text: str, max_lines: int) -> str:
    """護欄的輸出端過濾：超過 max_lines 行的程式碼區塊一律移除（CS50 的經驗：光靠提示詞擋不住）。"""
    def repl(m: "re.Match[str]") -> str:
        body = m.group(1).rstrip("\n")
        return m.group(0) if len(body.splitlines()) <= max_lines else REMOVED
    text = _FENCE.sub(repl, text)
    # 沒有用 ``` 包起來、但連續縮排的長程式碼
    out, run = [], []
    for line in text.split("\n"):
        if line.startswith(("    ", "\t")):
            run.append(line)
            continue
        if run:
            out.extend(run if len(run) <= max_lines else [REMOVED])
            run = []
        out.append(line)
    if run:
        out.extend(run if len(run) <= max_lines else [REMOVED])
    return "\n".join(out)
