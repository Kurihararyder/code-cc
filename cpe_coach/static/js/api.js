const token = document.querySelector('meta[name="cpe-token"]').content;
const listeners = new Set();
export const onConnection = (fn) => listeners.add(fn);
let offline = false;
function setOffline(v) { if (v !== offline) { offline = v; listeners.forEach((f) => f(!v)); } }

export class ApiError extends Error { constructor(msg, status) { super(msg); this.status = status; } }

export async function api(path, body) {
  let r;
  try {
    r = await fetch(path, { method: body === undefined ? "GET" : "POST", headers: { "X-CPE-Token": token, "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body) });
  } catch (e) { setOffline(true); throw new ApiError("連線中斷", 0); }
  setOffline(false);
  const j = await r.json().catch(() => ({ error: "伺服器回應異常" }));
  if (!r.ok) throw new ApiError(j.error || "HTTP " + r.status, r.status);
  return j;
}
export const get = (p, params) => api(params ? p + "?" + new URLSearchParams(params) : p);
export const post = (p, b = {}) => api(p, b);
