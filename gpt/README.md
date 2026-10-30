# 在 ChatGPT 使用助教（不需要 API 金鑰）

1. ChatGPT → 探索 GPT → 建立 → 設定 → 把 [`custom_gpt_instructions.md`](custom_gpt_instructions.md) 整份貼進「指示」。
2. 使用時依序貼：題目敘述 → 你的想法或程式 → 失敗的測資。它會依 L0–L4 提示階梯回答，不會給完整程式。
3. 每次用過就在終端機執行 `cpe external <題號>` 記錄，這題會被列入「無提示重寫」。
4. 它的判斷**可能出錯**（研究：約 37% 的提示有誤）。對錯一律以 `cpe test` 為準。

規則內容與 `cpe hint` 使用的是同一份（`cpe gpt-prompt` 可印出）。
