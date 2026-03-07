function extractPgnFromText(text) {
  const match = text.match(/(\[Event[\s\S]*?\n\n[\s\S]*?(?:1-0|0-1|1\/2-1\/2|\*))/);
  if (!match) {
    return null;
  }
  return match[1].trim();
}

function readCandidateText() {
  const textareas = Array.from(document.querySelectorAll("textarea"));
  for (const textarea of textareas) {
    if (textarea.value.includes("[Event")) {
      return textarea.value;
    }
  }

  const scripts = Array.from(document.scripts)
    .map((script) => script.textContent || "")
    .join("\n");
  const fromScripts = extractPgnFromText(scripts);
  if (fromScripts) {
    return fromScripts;
  }

  return extractPgnFromText(document.body.innerText);
}

function inferResult(text) {
  const match = text.match(/\[Result\s+"([^"]+)"\]/);
  if (match) {
    return match[1];
  }
  return "*";
}

function inferMode() {
  if (location.pathname.includes("/analysis")) {
    return "analysis";
  }
  if (location.pathname.includes("/play/computer")) {
    return "bot";
  }
  return "live";
}

function siteGameId() {
  const parts = location.pathname.split("/").filter(Boolean);
  return parts[parts.length - 1] || `${Date.now()}`;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "CAPTURE_CHESSCOM_GAME") {
    return;
  }

  const pgn = readCandidateText();
  if (!pgn) {
    sendResponse({ error: "PGN not found on this page." });
    return;
  }

  sendResponse({
    source_url: location.href,
    site_game_id: siteGameId(),
    pgn,
    result: inferResult(pgn),
    mode: inferMode(),
    captured_at: new Date().toISOString(),
  });
});
