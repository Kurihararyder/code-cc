# dev/ — 出題用的工具（學習者請不要看）

`gen_drills.py` 內含練習題的**參考解**，只用來產生 `cpe_coach/data/drills/` 裡的期望輸出。
想自己學會，就不要打開 `drills_*.py`。

重新產生：`python dev/gen_drills.py`

## 安裝精靈與控制台的開發工具

- `make_icons.py`：只用標準函式庫畫出 `cpe_coach/launcher/assets/` 裡的 `icon.png`／`icon.ico`／`icon.icns`（和網頁介面同一個設計）。
- `launcher_screens.py`：用虛擬螢幕把精靈與控制台的每個畫面開出來並截圖（需要 Xvfb 與 ImageMagick）：`xvfb-run -a -s "-screen 0 1280x800x24" python dev/launcher_screens.py 輸出資料夾`。CI 會存成 artifact；`docs/screens/launcher-*.png` 就是這樣產生的。
- `ci_installer_check.py`：CI 在 Windows／macOS／Linux 的虛擬機上，用雙擊用的啟動檔真的安裝之後，檢查程式、捷徑、登錄、PATH、`cpe` 指令、開啟／關閉服務，以及解除安裝之後有沒有清乾淨。
- `ci_diagnose.py`：CI 的「platform diagnostics」工作用的，只印資訊不會失敗：名稱解析各花多久（macOS 虛擬機上 `socket.getfqdn('127.0.0.1')` 要 35 秒，所以網頁服務不用 Python 內建的 HTTPServer 綁定）、網頁服務啟動時間、Windows 建立 `.lnk` 的做法比較（英文版 Windows 的 WScript.Shell 存不了中文檔名）、一次安裝每一步花多久。平台出怪問題時先看這個工作的日誌。

## CPE 原題資料

- `gen_cpe_sets.py <CPE_Previous_Questions 的資料夾>`：重新產生 `cpe_coach/data/cpe_sets.json`（題號、標題、所屬題單；不含題目敘述）與 `tests/fixtures/cpe_repo_digests.json`（每題範例輸入輸出的 SHA-256，只能拿來比對、無法還原內容）。
- `ui_e2e/fake_github.py`：介面測試用的假 GitHub zip（用 `tests/pdfmaker.py` 自己產生的 PDF）。
- 選用的真實資料驗證：`CPE_QUESTIONS_DIR=<clone 的資料夾> python -m unittest tests.test_cpe_real`（需要的話裝 poppler 才會多一項 pdftotext 對照）。不會執行 repo 裡的任何解答。
