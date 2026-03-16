const DEFAULT_API_URL = "http://localhost:8000";

// ── Création du menu clic droit ───────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "shorten-link",
    title: "🔗 Raccourcir ce lien",
    contexts: ["link"],
  });

  chrome.contextMenus.create({
    id: "shorten-page",
    title: "🔗 Raccourcir cette page",
    contexts: ["page"],
  });
});

// ── Gestion du clic dans le menu ─────────────────────────────────────────────
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const urlToShorten =
    info.menuItemId === "shorten-link"
      ? info.linkUrl
      : tab.url;

  if (!urlToShorten || !urlToShorten.startsWith("http")) return;

  const apiUrl = await getApiUrl();

  let data;
  try {
    const response = await fetch(`${apiUrl}/shorten`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlToShorten }),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    data = await response.json();

  } catch (err) {
    notify("PyShort — Erreur", "Serveur inaccessible. Vérifiez que l'API tourne.");
    return;
  }

  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: injectToast,
      args: [data.short],
    });
  } catch (err) {
    // Page protégée (ex: chrome://) — fallback notification
    notify("🔗 URL raccourcie !", data.short);
  }
});

// ── Toast injecté dans la page ────────────────────────────────────────────────
function injectToast(shortUrl) {

  const existing = document.getElementById("__pyshort_toast__");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "__pyshort_toast__";

  toast.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:16px;">🔗</span>
        <span style="font-weight:700;font-size:14px;">URL raccourcie</span>
      </div>
      <button id="__pyshort_close__" style="
        background:none;border:none;color:#94a3b8;font-size:18px;
        cursor:pointer;padding:0 2px;line-height:1;
      " title="Fermer">✕</button>
    </div>

    <div style="
      background:#0f172a;border:1px solid #334155;border-radius:8px;
      padding:8px 12px;margin-bottom:12px;
      font-size:12px;color:#38bdf8;word-break:break-all;line-height:1.5;
    ">${shortUrl}</div>

    <button id="__pyshort_copy__" style="
      width:100%;padding:9px;
      background:#0ea5e9;color:white;border:none;
      border-radius:8px;font-size:13px;font-weight:600;
      cursor:pointer;transition:background 0.2s;
    ">📋 Copier dans le presse-papier</button>
  `;

  Object.assign(toast.style, {
    position:     "fixed",
    bottom:       "24px",
    right:        "24px",
    background:   "#1e293b",
    color:        "#e2e8f0",
    border:       "1px solid #0ea5e9",
    borderRadius: "12px",
    padding:      "14px 16px",
    zIndex:       "999999",
    boxShadow:    "0 8px 32px rgba(0,0,0,0.5)",
    fontFamily:   "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    width:        "300px",
    opacity:      "0",
    transition:   "opacity 0.3s ease",
  });

  document.body.appendChild(toast);

  // Animation d'entrée
  requestAnimationFrame(() => { toast.style.opacity = "1"; });

  // Bouton Fermer
  document.getElementById("__pyshort_close__").addEventListener("click", () => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  });

  // Bouton Copier
  const btnCopy = document.getElementById("__pyshort_copy__");
  btnCopy.addEventListener("mouseenter", () => { btnCopy.style.background = "#38bdf8"; });
  btnCopy.addEventListener("mouseleave", () => { btnCopy.style.background = "#0ea5e9"; });

  btnCopy.addEventListener("click", () => {
    navigator.clipboard.writeText(shortUrl).then(() => {
      btnCopy.textContent = "✅ Copié !";
      btnCopy.style.background = "#16a34a";
      // Fermeture auto 2s après la copie
      setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
      }, 2000);
    }).catch(() => {
      // Fallback textarea
      const ta = document.createElement("textarea");
      ta.value = shortUrl;
      ta.style.cssText = "position:fixed;opacity:0;";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      btnCopy.textContent = "✅ Copié !";
      btnCopy.style.background = "#16a34a";
      setTimeout(() => {
        toast.style.opacity = "0";
        setTimeout(() => toast.remove(), 300);
      }, 2000);
    });
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getApiUrl() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(["apiUrl"], (result) => {
      resolve(result.apiUrl || DEFAULT_API_URL);
    });
  });
}

function notify(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon48.png",
    title,
    message,
    priority: 2,
  });
}