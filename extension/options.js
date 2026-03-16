const DEFAULT_API_URL = "http://localhost:8000";

const elInput   = document.getElementById("api-url");
const elBtnSave = document.getElementById("btn-save");
const elToast   = document.getElementById("toast");

// Charge la valeur sauvegardée au démarrage
document.addEventListener("DOMContentLoaded", () => {
  chrome.storage.sync.get(["apiUrl"], (result) => {
    elInput.value = result.apiUrl || DEFAULT_API_URL;
  });
});

// Sauvegarde
elBtnSave.addEventListener("click", () => {
  const apiUrl = elInput.value.trim().replace(/\/$/, ""); // supprime le slash final

  if (!apiUrl.startsWith("http")) {
    elInput.style.borderColor = "#b91c1c";
    elInput.focus();
    return;
  }

  elInput.style.borderColor = "";
  chrome.storage.sync.set({ apiUrl }, () => {
    elToast.classList.add("visible");
    setTimeout(() => elToast.classList.remove("visible"), 3000);
  });
});

// Valide en temps réel
elInput.addEventListener("input", () => {
  elInput.style.borderColor = "";
});
