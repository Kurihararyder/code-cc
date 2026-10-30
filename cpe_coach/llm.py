"""選用的 LLM 提示器（OpenAI 或 Anthropic，只用標準函式庫）。沒有金鑰時整個系統照常運作，只是少了 L0/L3/L4 的 AI 提示。"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Dict, List, Optional

RULES = (Path(__file__).parent / "data" / "tutor_rules.md").read_text(encoding="utf-8")

DEFAULT_MODELS = {"openai": "gpt-4o", "anthropic": "claude-sonnet-5-5"}
DEFAULT_BASE = {"openai": "https://api.openai.com/v1", "anthropic": "https://api.anthropic.com/v1"}
# (provider, url, headers builder, body builder, response parser)
Transport = Callable[[str, dict, dict], dict]


class LLMError(Exception):
    pass


def _post(url: str, headers: dict, body: dict, timeout: float = 60.0) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise LLMError(f"API 回應 {e.code}：{e.read().decode('utf-8', 'replace')[:200]}")
    except (urllib.error.URLError, TimeoutError) as e:
        raise LLMError(f"連線失敗：{e}")


class LLMClient:
    def __init__(self, provider: str, api_key: str, model: Optional[str] = None, transport: Transport = _post,
                 base_url: Optional[str] = None):
        if provider not in DEFAULT_MODELS:
            raise LLMError(f"不支援的 provider：{provider}")
        self.provider, self.api_key, self.transport = provider, api_key, transport
        self.model = model or DEFAULT_MODELS[provider]
        self.base_url = (base_url or DEFAULT_BASE[provider]).rstrip("/")

    def complete(self, system: str, user: str) -> str:
        return self.chat(system, [{"role": "user", "content": user}])

    def chat(self, system: str, messages: List[Dict[str, str]]) -> str:
        if self.provider == "openai":
            data = self.transport(
                f"{self.base_url}/chat/completions",
                {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                {"model": self.model, "messages": [{"role": "system", "content": system}] + list(messages)},
            )
            try:
                return data["choices"][0]["message"]["content"] or ""
            except (KeyError, IndexError, TypeError):
                raise LLMError("OpenAI 回應格式無法解析")
        data = self.transport(
            f"{self.base_url}/messages",
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            {"model": self.model, "max_tokens": 1024, "system": system, "messages": list(messages)},
        )
        try:
            return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        except (KeyError, TypeError):
            raise LLMError("Anthropic 回應格式無法解析")


def detect_client(cfg: Dict, env: Optional[Dict[str, str]] = None, key: Optional[str] = None) -> Optional[LLMClient]:
    """key：網頁介面暫存的金鑰（只存在記憶體）。CPE_API_BASE 可改成相容的代理網址。"""
    env = os.environ if env is None else env
    provider = cfg.get("provider")
    model = cfg.get("model") or env.get("CPE_MODEL")
    base = env.get("CPE_API_BASE")
    keys = {"openai": env.get("OPENAI_API_KEY"), "anthropic": env.get("ANTHROPIC_API_KEY")}
    if key:
        keys["openai" if not provider or provider == "openai" else provider] = key
        provider = provider or "openai"
    if provider:
        return LLMClient(provider, keys[provider], model, base_url=base) if keys.get(provider) else None
    for name in ("openai", "anthropic"):
        if keys[name]:
            return LLMClient(name, keys[name], model, base_url=base)
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
