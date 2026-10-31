"""介面測試用：假的 GitHub zip（自己產生的 UVa 風格 PDF，不含任何真題），讓 CPE 原題匯入在沒有網路時也能測。
用法：python3 fake_github.py <port>；CPE_QUESTIONS_URL=http://127.0.0.1:<port>/archive.zip"""
import io
import sys
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tests"))
import pdfmaker  # noqa: E402

LAYOUT = {"一星題": [10008, 10010, 100], "二星題": [10004], "歷屆試題": [255]}


def blob() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for d, nums in LAYOUT.items():
            for n in nums:
                pdf = pdfmaker.make_uva_pdf(n, f"Fake Problem {n}", "Read two integers and print their sum on one line. " * 3,
                                            "One line with two integers.", "One integer.", "1 2", "3")
                z.writestr(f"CPE_Previous_Questions-fake/{d}/{n}/{n}.pdf", pdf)
    return buf.getvalue()


class H(BaseHTTPRequestHandler):
    data = b""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.data)))
        self.end_headers()
        self.wfile.write(self.data)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    H.data = blob()
    HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
