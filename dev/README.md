# dev/ — 出題用的工具（學習者請不要看）

`gen_drills.py` 內含練習題的**參考解**，只用來產生 `cpe_coach/data/drills/` 裡的期望輸出。
想自己學會，就不要打開 `drills_*.py`。

重新產生：`python dev/gen_drills.py`

## 安裝精靈與控制台的開發工具

- `make_icons.py`：只用標準函式庫畫出 `cpe_coach/launcher/assets/` 裡的 `icon.png`／`icon.ico`／`icon.icns`（和網頁介面同一個設計）。
- `launcher_screens.py`：用虛擬螢幕把精靈與控制台的每個畫面開出來並截圖（需要 Xvfb 與 ImageMagick）：`xvfb-run -a -s "-screen 0 1280x800x24" python dev/launcher_screens.py 輸出資料夾`。CI 會存成 artifact；`docs/screens/launcher-*.png` 就是這樣產生的。
- `ci_installer_check.py`：CI 在 Windows／macOS／Linux 的虛擬機上，用雙擊用的啟動檔真的安裝之後，檢查程式、捷徑、登錄、PATH、`cpe` 指令、開啟／關閉服務，以及解除安裝之後有沒有清乾淨。
