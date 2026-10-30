# 安裝、使用與更新教學

這份教學的做法已經在乾淨的環境裡實際跑過一遍（git clone → 安裝 → 建工作區 → 啟動網頁介面 → 更新）。
**Windows 的步驟我沒有在真人的 Windows 桌面上走過**，只有 GitHub 上的 Windows 自動測試跑過核心功能；如果某一步和你看到的畫面不一樣，請把畫面或錯誤訊息貼給我。

## 先搞懂兩個資料夾

| 資料夾 | 裡面是什麼 | 誰會改它 |
|---|---|---|
| `code-cc`（程式資料夾） | 程式本身 | 我（在雲端改完推上 GitHub），你用 `cpe update` 更新 |
| `my-cpe`（工作區） | **你的學習進度**：解答、測資、提交紀錄、對話、單字本 | 只有你的練習會改它 |

兩個要**分開放**（工作區不要建在 `code-cc` 裡面）。更新只動程式資料夾，不會動到你的進度。

## 一、需要準備的東西

- **Python 3.9 以上**（考場是 3.9.6，建議裝 3.9～3.12 其中一個）
- **git**（下載與更新用）
- 瀏覽器
- 選用：**g++**（階段 4 起的 C++ 題目才需要）、**OpenAI 金鑰**（「選取文字問 AI」才需要，沒有也能用其他全部功能）

## 二、安裝（只做一次）

下載來源是 GitHub 公開倉庫，不需要登入。目前的開發分支叫 `claude/clever-archimedes-ekcn2m`（還沒合併進 `main`，所以下面都指定這個分支）。

### Windows

1. 裝 Python：到 <https://www.python.org/downloads/> 下載，安裝畫面第一頁**一定要勾選「Add python.exe to PATH」**。
2. 裝 git：<https://git-scm.com/download/win>，一路按 Next。
3. 重新開一個「命令提示字元」或 PowerShell（要重開，PATH 才會生效），依序執行：

```bat
python --version
git clone -b claude/clever-archimedes-ekcn2m https://github.com/Kurihararyder/code-cc.git
cd code-cc
python -m pip install -e .
cpe --version
```

- 最後一行應該顯示 `cpe 2.4.1`（或更新的版本）。
- `python` 找不到時，把上面的 `python` 換成 `py`。
- `cpe` 找不到（pip 安裝時會警告 Scripts 資料夾不在 PATH）：先用 `python -m cpe_coach` 代替 `cpe`，所有指令都一樣能用，例如 `python -m cpe_coach web`；想永久解決，把警告裡列出的那個 Scripts 資料夾加進 PATH。

### macOS

```bash
xcode-select --install                 # 裝 git 和 C++ 編譯器（已經裝過會告訴你）
python3 --version                      # 3.9 以上就可以；沒有的話到 python.org 下載，或 brew install python@3.12
git clone -b claude/clever-archimedes-ekcn2m https://github.com/Kurihararyder/code-cc.git
cd code-cc
python3 -m venv ~/.cpe-venv            # 建一個專用的虛擬環境（新版 Python 不允許直接 pip 到系統）
source ~/.cpe-venv/bin/activate
python -m pip install -e .
cpe --version
```

以後每次開新的終端機，要先執行 `source ~/.cpe-venv/bin/activate` 才有 `cpe` 指令（可以把這行加進 `~/.zshrc`）。

### Linux（以 Debian／Ubuntu 為例）

```bash
sudo apt install python3 python3-venv python3-pip git g++
git clone -b claude/clever-archimedes-ekcn2m https://github.com/Kurihararyder/code-cc.git
cd code-cc
python3 -m venv ~/.cpe-venv
source ~/.cpe-venv/bin/activate
python -m pip install -e .
cpe --version
```

## 三、建立你的工作區並開始

```bash
cd ..                 # 先離開 code-cc 資料夾
cpe init my-cpe       # 建立工作區（資料夾名稱隨你取）
cd my-cpe
cpe web               # 啟動網頁介面，會自動開瀏覽器
```

瀏覽器沒有自動開的話，手動打開 <http://127.0.0.1:8765/>。要結束，回到終端機按 `Ctrl+C`。
**以後每天**：開終端機 → `cd my-cpe` → `cpe web`。（網頁只綁在你自己的電腦上，別人連不進來。）

### 第一次使用的路線

1. 首頁的「今日計畫」會排出今天要做的題。點第一題 `d001`。
2. 左邊是題目、中間寫程式、按「執行測試」（或 `Ctrl+Enter`）判題。卡住再用「提示階梯」，用了提示的題目隔天要無提示重寫。
3. 在題目、程式或測試結果上**選取一段文字**，旁邊會問「要問這一段嗎？」（需要金鑰，見下一節）。
4. 想模擬考場：左側「考試」頁。

終端機版也有完整功能：`cpe today`、`cpe new d001`、`cpe test d001`、`cpe plan -m 30`……`cpe --help` 看全部。

## 四、設定 AI（選用）

「選取文字問 AI」會把你的程式與題目敘述傳給 OpenAI，並產生 API 費用（每次約一兩千 token）。

- **最簡單**：網頁右上角（或「設定」頁）貼上 OpenAI 金鑰，按「測試連線」。金鑰只存在這個程式的記憶體，不寫入任何檔案，每次重開要再貼。
- **環境變數**（重開不用再貼）：啟動前設定 `OPENAI_API_KEY`。
  - PowerShell：`$env:OPENAI_API_KEY="sk-..."; cpe web`
  - 命令提示字元：`set OPENAI_API_KEY=sk-...` 然後 `cpe web`
  - macOS／Linux：`export OPENAI_API_KEY=sk-...`
- 建議在 OpenAI 後台為這把金鑰設花費上限。
- 想評測 AI 詢問系統的表現：`cpe ai-eval --yes`（會呼叫約 20～40 次 API）。

## 五、更新（我在雲端改好之後，你在電腦上做）

```bash
cpe update --check    # 只看有沒有新版本（不會改程式檔）
cpe update            # 更新，並顯示這次更新的內容
```

更新完，如果網頁介面還開著，回到它的終端機按 `Ctrl+C`，再重新執行 `cpe web`。網頁的「設定 → 版本與更新」也有「檢查更新」按鈕（只檢查，不會更新）。

它做了什麼、怎麼保護你：

- 只做 fast-forward 的 `git pull`；更新後會用新程式重新載入一次，**載入失敗會自動退回更新前的版本**。
- 你**改過程式資料夾裡的檔案**，或有還沒推送的 commit 時，不會更新，並告訴你為什麼。所以不要直接改 `code-cc` 裡的檔案，要改請告訴我。
- 你的學習進度在工作區，更新不會碰它；舊版建立的工作區會繼續能用（有自動測試，用 1.0.0 與 2.1.0 實際產生的工作區驗證過）。想更保險，更新前先 `cpe export` 備份一份。
- 更新完萬一有問題，終端機會印出一行退回的指令（`git reset --hard <更新前的版本>`）。

手動更新也可以：`cd code-cc`，然後 `git pull`。

> 備註：`cpe update` 是 2.4.0 才有的。如果你裝的是更舊的版本，第一次請手動 `git pull`，之後就能用 `cpe update`。
> 如果之後我把分支合併進 `main`，要改追蹤 `main`：在 `code-cc` 資料夾執行 `git switch main`。

## 六、備份與搬家

```bash
cpe export                         # 把進度打包成 zip（不含 API 金鑰）
cpe restore 備份檔.zip --dir 新資料夾   # 在新電腦還原
```

網頁的「設定 → 備份與搬家」也能下載。系統每小時還會自動留一份進度快照（工作區的 `.cpe/backups`）。換電腦時：新電腦照「二、安裝」裝好，再 `cpe restore`。

## 七、疑難排解

| 狀況 | 怎麼辦 |
|---|---|
| `cpe` 不是內部或外部命令 | 用 `python -m cpe_coach`（或 `py -m cpe_coach`）代替 `cpe`；macOS／Linux 檢查是否已 `source ~/.cpe-venv/bin/activate` |
| `python` 找不到（Windows） | 改用 `py`；還是找不到就重新安裝 Python 並勾選 Add to PATH |
| 埠 8765 被占用 | `cpe web --port 8800`，網址也跟著改 |
| 瀏覽器沒有自動開 | 手動貼上終端機顯示的網址 |
| 終端機中文變亂碼（舊版 cmd） | 改用 Windows Terminal 或 PowerShell；或先執行 `chcp 65001` |
| 提示「找不到 g++」 | 只有 C++ 題目需要。Windows：安裝 MSYS2（<https://www.msys2.org/>），在它的終端機執行 `pacman -S mingw-w64-ucrt-x86_64-gcc`，再把 `C:\msys64\ucrt64\bin` 加進 PATH，新開終端機確認 `g++ --version`。macOS：`xcode-select --install`。Linux：`sudo apt install g++` |
| `cpe update` 說不是 git 安裝 | 你是用 zip 或 `pip install .` 裝的。照「二、安裝」用 `git clone` 重裝一次（進度在工作區，不受影響） |
| `cpe update` 說程式檔被修改過 | 在 `code-cc` 資料夾執行 `git status` 看改了哪些；不需要這些修改就 `git checkout .` 放棄，要保留就 `git stash` |
| 提示「已有進行中的考試」 | `cpe mock finish` 交卷，或在網頁「考試」頁交卷 |
| 進度檔壞掉 | 程式會自動從 `.cpe/state.json.bak` 還原並寫一份 `recovered.txt` 說明；還救不回來就用備份 `cpe restore` |
| 防毒或防火牆跳出提示 | 網頁服務只綁 `127.0.0.1`（本機），不對外；允許即可 |

## 八、解除安裝

```bash
python -m pip uninstall cpe-coach
```

然後刪除 `code-cc` 資料夾。**`my-cpe` 是你的進度，先 `cpe export` 備份再決定要不要刪。**
