# Supabase 後端

- `migrations/0001_init.sql`：資料表、RLS、設定預設值、防自行註冊的閘門
- `migrations/0002_functions.sql`：授權判斷 `access_for`／`check_access`、進度存取、管理員函式、權限收回與開放
- `functions/admin`：建立／重設密碼／刪除帳號（需要 service role）
- `functions/ai-proxy`：AI 代理（金鑰只在資料庫）

這些已經套用在專案 `rtwmvezudjtqelrrprsj`（ap-northeast-1）。重建時：依序執行兩個 migration、部署兩個 Edge Function（`verify_jwt` 開啟），再用 SQL 建立第一個管理員（見 `docs/ADMIN.md` 最後一節的欄位；`profiles.role='admin'`、`active=true`，帳號的 email 是 `<學號>@icd-cpe.example.com`）。

客戶端設定在 `cpe_coach/data/cloud.json`（網址與 publishable key；都是公開資訊）。環境變數 `CPE_CLOUD=off` 可暫時關閉登入閘門（開發／測試用），`CPE_CLOUD_URL`／`CPE_CLOUD_KEY` 可指向別的專案。
