# dev/ — 出題用的工具（學習者請不要看）

`gen_drills.py` 內含練習題的**參考解**，只用來產生 `cpe_coach/data/drills/` 裡的期望輸出。
想自己學會，就不要打開 `drills_*.py`。

重新產生：`python dev/gen_drills.py`

## 題目與測資的品質檢查（2.8.0 起）

- `qa.py`：**每一題內建練習題都要通過的檢查**，`python dev/qa.py`（全部）、`python dev/qa.py d007 d060`（指定題）、`--quick`（少跑幾輪隨機對拍）。檢查內容：
  1. 獨立解（`brute`，做法和參考解不同）與參考解在上百筆隨機小資料（`gen`）上逐筆一致；
  2. 每一筆測資（手寫的、隨機的、超大的）都符合題目寫的輸入限制（`valid`）；
  3. 每份『常見錯誤解』（`wrong`，`pt(舊, 新)` 是把參考解改一小段）至少被一筆測資抓到——抓不到時會印出隨機資料裡找得到的反例，補成固定測資；
  4. 需要考效能的題，『正確但太慢的解』（`slow`）在 3 秒內必須跑不完，而參考解最慢那筆要低於 1.6 秒（CI 上用 `QA_REF_MAX` 放寬）；
  5. 範例就是第一筆測資、沒有重複的測資、至少 8 筆（輸入空間很小的題用 `space=` 說明）。
- `qa_s0.py`…`qa_s4.py`、`qa_n.py`：各題的登記（`Q(題號, 獨立解, 隨機小輸入, 輸入檢查, wrong=…, slow=…, big=…)`）。`qa_all.py` 把它們全部載入。
- `drills_n.py`：2.8.0 新增的 93 題（同時寫中文與英文敘述）。新增題目的流程：在 `drills_n.py` 加 `N(...)`（含手寫測資）→ 在 `qa_n.py` 加 `Q(...)` → `python dev/qa.py 題號` 全部通過 → `python dev/gen_drills.py && python dev/gen_drills_en.py && python dev/gen_course.py`。
- 大測資（`big`）會放進最後的測資檔，所以套件大小要留意：能用 2–3 萬筆分出快慢就不要放 10 萬筆。有登記 `big` 的題，舊的手寫超大測資（> 6 萬字元）會被略過，避免同一種壓力測資重複出現。
- 本機判題會忽略行尾空白與檔案結尾的空行，所以『最後一組後面不要多印空行』這類要求不能用 `wrong` 檢查。

## 安裝精靈與控制台的開發工具

- `make_icons.py`：只用標準函式庫畫出 `cpe_coach/launcher/assets/` 裡的 `icon.png`／`icon.ico`／`icon.icns`（和網頁介面同一個設計）。
- `launcher_screens.py`：用虛擬螢幕把精靈與控制台的每個畫面開出來並截圖（需要 Xvfb 與 ImageMagick）：`xvfb-run -a -s "-screen 0 1280x800x24" python dev/launcher_screens.py 輸出資料夾`。CI 會存成 artifact；`docs/screens/launcher-*.png` 就是這樣產生的。
- `ci_installer_check.py`：CI 在 Windows／macOS／Linux 的虛擬機上，用雙擊用的啟動檔真的安裝之後，檢查程式、捷徑、登錄、PATH、`cpe` 指令、開啟／關閉服務，以及解除安裝之後有沒有清乾淨。
- `ci_diagnose.py`：CI 的「platform diagnostics」工作用的，只印資訊不會失敗：名稱解析各花多久（macOS 虛擬機上 `socket.getfqdn('127.0.0.1')` 要 35 秒，所以網頁服務不用 Python 內建的 HTTPServer 綁定）、網頁服務啟動時間、Windows 建立 `.lnk` 的做法比較（英文版 Windows 的 WScript.Shell 存不了中文檔名）、一次安裝每一步花多久。平台出怪問題時先看這個工作的日誌。

## CPE 原題資料

- `gen_cpe_sets.py <CPE_Previous_Questions 的資料夾>`：重新產生 `cpe_coach/data/cpe_sets.json`（題號、標題、所屬題單；不含題目敘述）與 `tests/fixtures/cpe_repo_digests.json`（每題範例輸入輸出的 SHA-256，只能拿來比對、無法還原內容）。
- `ui_e2e/fake_github.py`：介面測試用的假 GitHub zip（用 `tests/pdfmaker.py` 自己產生的 PDF）。
- 選用的真實資料驗證：`CPE_QUESTIONS_DIR=<clone 的資料夾> python -m unittest tests.test_cpe_real`（需要的話裝 poppler 才會多一項 pdftotext 對照）。不會執行 repo 裡的任何解答。
- `cpe_meta_src.py`：91 題的類型標籤、先修單元、難度與提示的來源（我寫的，沒有官方核對）；執行後產生 `cpe_coach/data/cpe_meta.json`。

## 學習工坊的內容

- `lab_quiz_src.py`、`lab_worked_src.py`、`lab_text_src.py`：概念測驗、示範題、找 bug、預測輸出、解法比較、微課、術語表的來源（我寫的）。
- `gen_lab.py`：把這些來源**實際執行**過再產生 `cpe_coach/data/lab/*.json`（測驗題的答案要和實際輸出一致、每個 bug 都要真的讓程式出錯而修正版要通過、各種解法的輸出要一致，否則中止）。CI 會重新產生並檢查沒有差異。
