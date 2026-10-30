# 介面端到端測試（Playwright）

需要 Node 與 Playwright（`npm i playwright`，並有 Chromium）。測試用一個假的 OpenAI 伺服器（`../fake_llm.py`，port 8792），
所以不需要真的金鑰。

```bash
python3 ../fake_llm.py 8792 &        # 假的 OpenAI
./fresh.sh                           # 在 /tmp 建一個全新工作區並啟動 cpe web（port 8793）
node ui.js                           # 桌面：編輯器、選取彈出選單、AI 對話、閘門、指令面板、深色
./fresh.sh && node gate.js           # 單元檢核完整流程（開始 → 計時 → 交卷 → 進入下一單元）
./fresh.sh && node mobile.js         # 手機（iPhone 13）：分頁、底部導覽、選單位置、無橫向捲動
node a11y.js                         # 無障礙：控制項名稱、標題層級、跳到主要內容、焦點回復
```

腳本的截圖會寫到「目前目錄」的 `shots/`，所以請在測試目錄（預設 `/tmp/cpe-e2e`）裡執行，並讓 Node 找得到 playwright（例如 `NODE_PATH=$(npm root -g)`）：

```bash
cd /tmp/cpe-e2e && NODE_PATH=$(npm root -g) node /path/to/dev/ui_e2e/ui.js
```

每個腳本以 PASS／FAIL 逐項輸出；`ui.js`、`gate.js`、`mobile.js` 之間不能共用同一個工作區，每次先 `./fresh.sh`。
