// AI 代理：OpenAI 金鑰只存在資料庫（app_secrets），學生的程式從來拿不到。
// 每次呼叫都檢查：帳號啟用、在授權期間、IP 允許、管理員有開放 AI（全域＋個人）、沒超過每日次數。
import { createClient } from "npm:@supabase/supabase-js@2";

const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...CORS, "Content-Type": "application/json" } });
const MSG: Record<string, string> = {
  inactive: "帳號尚未啟用", not_started: "授權期間還沒開始", expired: "授權已到期", ip_denied: "目前的網路位址不在允許清單", ip_unknown: "無法判斷網路位址", no_profile: "找不到帳號資料",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: u } = await sb.auth.getUser(token);
  if (!u?.user) return json({ error: "未登入" }, 401);
  const ip = req.headers.get("cf-connecting-ip") || (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || null;
  const { data: acc } = await sb.rpc("access_for", { p_uid: u.user.id, p_ip: ip });
  if (!acc?.ok) return json({ error: MSG[acc?.reason] || "沒有權限", reason: acc?.reason }, 403);
  const { data: st } = await sb.from("app_settings").select("value").eq("key", "ai").single();
  const cfg = st?.value || {};
  if (!cfg.enabled) return json({ error: "管理員尚未開放 AI 功能", reason: "ai_off" }, 403);
  if (!acc.ai_allowed) return json({ error: "你的帳號沒有被授權使用 AI（請洽管理員）", reason: "ai_not_allowed" }, 403);
  const since = new Date(Date.now() - 24 * 3600 * 1000).toISOString();
  const { count } = await sb.from("ai_usage").select("id", { count: "exact", head: true }).eq("user_id", u.user.id).gte("at", since);
  if ((count ?? 0) >= (cfg.daily_calls ?? 60)) return json({ error: `今天的 AI 次數已用完（上限 ${cfg.daily_calls ?? 60} 次／24 小時）`, reason: "ai_quota" }, 429);
  const { data: sec } = await sb.from("app_secrets").select("value").eq("key", "openai_key").maybeSingle();
  if (!sec?.value) return json({ error: "管理員還沒有設定 API 金鑰", reason: "no_key" }, 503);
  const body = await req.json().catch(() => null);
  if (!body || !Array.isArray(body.messages)) return json({ error: "格式不對" }, 400);
  const payload: Record<string, unknown> = { model: cfg.model || "gpt-4o", messages: body.messages, max_tokens: Math.min(Number(body.max_tokens) || cfg.max_tokens || 1500, cfg.max_tokens || 1500) };
  if (body.response_format) payload.response_format = body.response_format;
  if (typeof body.temperature === "number") payload.temperature = body.temperature;
  const r = await fetch("https://api.openai.com/v1/chat/completions", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${sec.value}` }, body: JSON.stringify(payload) });
  const text = await r.text();
  try {
    const j = JSON.parse(text);
    await sb.from("ai_usage").insert({ user_id: u.user.id, student_id: acc.student_id, model: payload.model, tokens_in: j.usage?.prompt_tokens ?? 0, tokens_out: j.usage?.completion_tokens ?? 0 });
  } catch (_) { /* 不是 JSON 就不記錄 */ }
  return new Response(text, { status: r.status, headers: { ...CORS, "Content-Type": "application/json" } });
});
