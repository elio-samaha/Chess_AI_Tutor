const API_BASE = "http://127.0.0.1:8000";
const PENDING_KEY = "pendingImports";

async function setBadge(text, color) {
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color });
}

async function queuePending(payload) {
  const { [PENDING_KEY]: existing = [] } = await chrome.storage.local.get(PENDING_KEY);
  existing.push(payload);
  await chrome.storage.local.set({ [PENDING_KEY]: existing });
}

async function flushPending() {
  const { [PENDING_KEY]: existing = [] } = await chrome.storage.local.get(PENDING_KEY);
  if (!existing.length) {
    return;
  }

  const remaining = [];
  for (const payload of existing) {
    try {
      await postImport(payload);
    } catch {
      remaining.push(payload);
    }
  }

  await chrome.storage.local.set({ [PENDING_KEY]: remaining });
  await setBadge(remaining.length ? "Q" : "", remaining.length ? "#cc8d2d" : "#2f6f3e");
}

async function postImport(payload) {
  const response = await fetch(`${API_BASE}/imports/extension/game`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Import failed: ${response.status}`);
  }

  return response.json();
}

chrome.runtime.onInstalled.addListener(() => {
  void flushPending();
});

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) {
    return;
  }

  try {
    const payload = await chrome.tabs.sendMessage(tab.id, { type: "CAPTURE_CHESSCOM_GAME" });
    if (!payload || payload.error) {
      await setBadge("!", "#a54343");
      return;
    }

    try {
      await postImport(payload);
      await setBadge("OK", "#2f6f3e");
      await flushPending();
    } catch {
      await queuePending(payload);
      await setBadge("Q", "#cc8d2d");
    }
  } catch {
    await setBadge("!", "#a54343");
  }
});
