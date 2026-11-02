// 管理員專用：建立／重設密碼／刪除帳號（需要 service role，所以不能在客戶端做）
import { createClient } from "npm:@supabase/supabase-js@2";

const DOMAIN = "icd-cpe.example.com";
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...CORS, "Content-Type": "application/json" } });
const SID = /^[a-z0-9][a-z0-9_-]{2,23}$/;

function randPw(n = 10): string {
  const a = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const b = crypto.getRandomValues(new Uint32Array(n));
  return Array.from(b, (x) => a[x % a.length]).join("");
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const url = Deno.env.get("SUPABASE_URL")!;
  const sb = createClient(url, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: u } = await sb.auth.getUser(token);
  if (!u?.user) return json({ error: "未登入" }, 401);
  const { data: me } = await sb.from("profiles").select("role,active").eq("id", u.user.id).single();
  if (!me || me.role !== "admin" || !me.active) return json({ error: "只有管理員可以使用" }, 403);
  const body = await req.json().catch(() => ({}));
  const audit = (action: string, detail: unknown) => sb.from("audit_log").insert({ user_id: u.user!.id, action, detail });

  if (body.action === "create_users") {
    const rows: any[] = Array.isArray(body.users) ? body.users.slice(0, 500) : [];
    const out: any[] = [];
    await sb.from("signup_gate").update({ open_until: new Date(Date.now() + 90_000).toISOString() }).eq("id", 1);   // 短暫開門：只有這段期間才允許新增帳號
    for (const r of rows) {
      const sid = String(r.student_id || "").trim().toLowerCase();
      if (!SID.test(sid)) { out.push({ student_id: sid, ok: false, error: "學號格式不對（3–24 字，英數、底線、減號）" }); continue; }
      const pw = String(r.password || "") || randPw();
      if (pw.length < 6) { out.push({ student_id: sid, ok: false, error: "密碼至少 6 個字" }); continue; }
      const { data, error } = await sb.auth.admin.createUser({ email: `${sid}@${DOMAIN}`, password: pw, email_confirm: true, app_metadata: { provisioned: true } });
      if (error || !data.user) { out.push({ student_id: sid, ok: false, error: /already|registered|exists/i.test(error?.message || "") ? "學號已存在" : (error?.message || "建立失敗") }); continue; }
      const { error: e2 } = await sb.from("profiles").insert({
        id: data.user.id, student_id: sid, name: String(r.name || ""), cohort: String(r.cohort || body.cohort || ""), role: "student",
        active: body.active === true, ai_allowed: body.ai_allowed === true, must_change_pw: true,
        valid_from: body.valid_from || null, valid_until: body.valid_until || null,
      });
      if (e2) { await sb.auth.admin.deleteUser(data.user.id); out.push({ student_id: sid, ok: false, error: e2.message }); continue; }
      out.push({ student_id: sid, name: r.name || "", ok: true, password: pw, id: data.user.id });
    }
    await sb.from("signup_gate").update({ open_until: new Date(0).toISOString() }).eq("id", 1);
    await audit("admin_create_users", { count: out.filter((x) => x.ok).length, failed: out.filter((x) => !x.ok).length });
    return json({ results: out });
  }
  if (body.action === "reset_password") {
    const pw = String(body.password || "") || randPw();
    if (pw.length < 6) return json({ error: "密碼至少 6 個字" }, 400);
    const { error } = await sb.auth.admin.updateUserById(body.id, { password: pw });
    if (error) return json({ error: error.message }, 400);
    await sb.from("profiles").update({ must_change_pw: true }).eq("id", body.id);
    await audit("admin_reset_password", { target: body.id });
    return json({ ok: true, password: pw });
  }
  if (body.action === "delete_user") {
    if (body.id === u.user.id) return json({ error: "不能刪除自己" }, 400);
    const { error } = await sb.auth.admin.deleteUser(body.id);
    if (error) return json({ error: error.message }, 400);
    await audit("admin_delete_user", { target: body.id });
    return json({ ok: true });
  }
  return json({ error: "未知的操作" }, 400);
});
