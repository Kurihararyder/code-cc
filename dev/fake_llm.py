"""測試用：假的 OpenAI 相容伺服器。依請求內容回傳符合格式的 JSON，並可故意先回一次捏造的引用。"""
import json, re, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

CALLS = []

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        msgs = body["messages"]
        CALLS.append(msgs)
        last = msgs[-1]["content"]
        m = re.search(r'\[學生選取\][^\n]*\n"""\n(.*?)\n"""', msgs[1]["content"], re.S) if len(msgs) > 1 else None
        sel = (m.group(1).strip().splitlines() or ["x"])[0][:40] if m else "x"
        if "找不到" in last and "請只引用" in last:         # 重答
            out = {"type": "predict", "message": f"重新來過。你預期 `{sel}` 這一行執行完之後，相關變數是多少？", "evidence": [{"source": "code", "line": None, "quote": sel}]}
        elif last.startswith("[學生回答]"):
            out = {"type": "feedback", "message": "你提到的方向有一半對。再往下一步：這個值在第二圈會變成多少？", "evidence": [{"source": "code", "line": None, "quote": sel}]}
        elif "FABRICATE" in msgs[1]["content"] and len(msgs) == 2:
            out = {"type": "locate", "message": "看這一行。", "evidence": [{"source": "code", "line": 3, "quote": "this text is not in code"}]}
        else:
            out = {"type": "predict", "message": f"你選的 `{sel}` 執行完後，你預期相關變數是多少？請先猜再用追蹤驗證。", "evidence": [{"source": "code", "line": 1, "quote": sel}]}
        data = json.dumps({"choices": [{"message": {"content": json.dumps(out, ensure_ascii=False)}}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

if __name__ == "__main__":
    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
