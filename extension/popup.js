const DEFAULT_API_URL = "http://localhost:8000";

// ── Onglets ───────────────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach(tabBtn => {
  tabBtn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
    tabBtn.classList.add("active");
    document.getElementById("tab-" + tabBtn.dataset.tab).classList.add("active");
  });
});

// ── Initialisation ────────────────────────────────────────────────────────────
let currentTabUrl = "";

document.addEventListener("DOMContentLoaded", async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTabUrl = tab?.url || "";

  const el = document.getElementById("original-url");
  el.textContent = currentTabUrl || "Aucune URL détectée";

  if (!currentTabUrl.startsWith("http")) {
    const btn = document.getElementById("btn-shorten-current");
    btn.disabled = true;
    btn.textContent = "Non disponible sur cette page";
  }
});

// ── Paramètres ────────────────────────────────────────────────────────────────
document.getElementById("btn-settings").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

// ── Onglet 1 : Page actuelle ──────────────────────────────────────────────────
document.getElementById("btn-shorten-current").addEventListener("click", async () => {
  await shortenAndDisplay(
    currentTabUrl,
    "btn-shorten-current",
    "result-current",
    "result-url-current",
    "error-current",
    "stats-clicks-current",
    "stats-date-current",
  );
});

setupCopyBtn("btn-copy-current", "result-url-current");

// ── Onglet 2 : URL manuelle ───────────────────────────────────────────────────

// Bouton coller depuis presse-papier
document.getElementById("btn-paste").addEventListener("click", async () => {
  const input = document.getElementById("manual-input");

  // Méthode 1 : API Clipboard moderne (fonctionne si permission accordée)
  try {
    const text = await navigator.clipboard.readText();
    if (text) {
      input.value = text.trim();
      input.focus();
      return;
    }
  } catch {}

  // Méthode 2 : focus + execCommand paste (fallback fiable dans les popups Chrome)
  input.focus();
  input.select();
  try {
    document.execCommand("paste");
  } catch {}
});

// Raccourcir sur Entrée dans le champ
document.getElementById("manual-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") document.getElementById("btn-shorten-manual").click();
});

document.getElementById("btn-shorten-manual").addEventListener("click", async () => {
  const url = document.getElementById("manual-input").value.trim();
  if (!url) {
    showError("error-manual", "Veuillez entrer ou coller une URL.");
    return;
  }
  await shortenAndDisplay(
    url,
    "btn-shorten-manual",
    "result-manual",
    "result-url-manual",
    "error-manual",
    "stats-clicks-manual",
    "stats-date-manual",
  );
});

setupCopyBtn("btn-copy-manual", "result-url-manual");

// ── Logique commune ───────────────────────────────────────────────────────────
async function shortenAndDisplay(url, btnId, resultId, resultUrlId, errorId, clicksId, dateId) {
  // Nettoyage : supprime espaces, retours à la ligne et caractères invisibles
  url = url.trim().replace(/[\r\n\t]/g, "");

  // Ajoute https:// si l'utilisateur a oublié le protocole
  if (url && !url.startsWith("http://") && !url.startsWith("https://")) {
    url = "https://" + url;
  }

  if (!url) {
    showError(errorId, "Veuillez entrer une URL valide.");
    return;
  }

  setLoading(btnId, true);
  hideError(errorId);
  hideResult(resultId, clicksId, dateId);

  try {
    const apiUrl = await getApiUrl();
    const response = await fetch(`${apiUrl}/shorten`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      // Pydantic retourne detail comme tableau [{msg, loc, type}]
      let errMsg = response.statusText;
      if (detail.detail) {
        if (Array.isArray(detail.detail)) {
          errMsg = detail.detail.map(e => e.msg).join(", ");
        } else {
          errMsg = String(detail.detail);
        }
      }
      throw new Error(`Erreur ${response.status} : ${errMsg}`);
    }

    const data = await response.json();
    document.getElementById(resultUrlId).textContent = data.short;
    document.getElementById(resultId).classList.add("visible");

    // Stats en arrière-plan
    try {
      const res = await fetch(`${apiUrl}/stats/${data.code}`);
      if (res.ok) {
        const stats = await res.json();
        document.getElementById(clicksId).textContent =
          `👆 ${stats.clicks} clic${stats.clicks !== 1 ? "s" : ""}`;
        const d = new Date(stats.created_at).toLocaleDateString("fr-FR");
        document.getElementById(dateId).textContent = `📅 Créé le ${d}`;
      }
    } catch {}

  } catch (err) {
    if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
      showError(errorId, "Impossible de joindre l'API.\nVérifiez que le serveur est lancé ou configurez l'URL dans les paramètres (⚙️).");
    } else {
      showError(errorId, err.message);
    }
  } finally {
    setLoading(btnId, false);
  }
}

function setupCopyBtn(btnId, urlId) {
  document.getElementById(btnId).addEventListener("click", async () => {
    const url = document.getElementById(urlId).textContent;
    const btn = document.getElementById(btnId);
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = url;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    btn.textContent = "✅ Copié !";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = "Copier";
      btn.classList.remove("copied");
    }, 2000);
  });
}

async function getApiUrl() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(["apiUrl"], (r) => resolve(r.apiUrl || DEFAULT_API_URL));
  });
}

function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (loading) {
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Raccourcissement…';
  } else {
    btn.disabled = false;
    btn.textContent = btnId.includes("current") ? "Raccourcir cette URL" : "Raccourcir";
  }
}

function showError(id, message) {
  const el = document.getElementById(id);
  el.textContent = message;
  el.classList.add("visible");
}

function hideError(id) {
  document.getElementById(id).classList.remove("visible");
}

function hideResult(resultId, clicksId, dateId) {
  document.getElementById(resultId).classList.remove("visible");
  document.getElementById(clicksId).textContent = "";
  document.getElementById(dateId).textContent = "";
}