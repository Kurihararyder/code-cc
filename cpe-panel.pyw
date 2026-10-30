"""CPE 教練：雙擊或由捷徑啟動。已安裝 → 控制台；還沒安裝 → 安裝精靈。
（.pyw 在 Windows 上用 pythonw 執行，不會跳出黑色視窗；內容和 python -m cpe_coach.launcher 一樣。）"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.expanduser("~"))                  # 工作目錄不要放在程式資料夾裡（Windows 無法刪除正在被使用的資料夾）

from cpe_coach.launcher.__main__ import run        # noqa: E402

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
