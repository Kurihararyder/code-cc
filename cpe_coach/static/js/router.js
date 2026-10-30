// 極簡 hash 路由：#/home、#/practice/<題號>、#/course、#/stats、#/settings
import { closeAllLayers } from "./dom.js";
const routes = {}; let cleanup = null, current = { name: "", params: [] };
export const route = (name, mount) => { routes[name] = mount; };
export const go = (path) => { const t = "#" + (path.startsWith("/") ? path : "/" + path); if (location.hash === t) render(); else location.hash = t; };
export const where = () => current;
export async function render() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean).map(decodeURIComponent);
  const name = routes[parts[0]] ? parts[0] : "home";
  current = { name, params: parts.slice(1) };
  const view = document.getElementById("view");
  closeAllLayers();
  if (cleanup) { try { cleanup(); } catch { /* ignore */ } cleanup = null; }
  view.textContent = ""; view.scrollTop = 0;
  window.dispatchEvent(new CustomEvent("routechange", { detail: current }));
  cleanup = (await routes[name](view, current.params)) || null;
}
window.addEventListener("hashchange", render);
