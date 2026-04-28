// Gemini Conversation Scraper
// Usage:
//   1. Open the Gemini shared conversation page in browser
//   2. Manually scroll to the TOP of the conversation (to force all turns to render)
//   3. Paste and run STEP 1 in DevTools Console — it will log "捕捉第 N 輪" as it collects
//   4. Paste and run STEP 2 to download the JSON file
//
// Tested on: gemini.google.com/share/* (public share links)
// Output: gemini-conversation.json — array of { order, user, model }

// ── STEP 1: Start collection ──────────────────────────────────────────────────
window._geminiData = new Map();
window._geminiOrder = 0;

function capture() {
  document.querySelectorAll('.conversation-container').forEach(el => {
    const id = el.id;
    if (!id || window._geminiData.has(id)) return;

    const userText = el.querySelector('user-query-content')?.innerText?.trim()
      || el.querySelector('user-query')?.innerText?.trim() || '';

    const modelEl = el.querySelector('model-response');
    const modelText = modelEl?.querySelector('message-content')?.innerText?.trim()
      || modelEl?.innerText?.trim() || '';

    if (userText || modelText) {
      window._geminiData.set(id, { order: window._geminiOrder++, user: userText, model: modelText });
      console.log(`捕捉第 ${window._geminiData.size} 輪`);
    }
  });
}

capture();

window._observer = new MutationObserver(capture);
window._observer.observe(document.querySelector('infinite-scroller'), { childList: true, subtree: true });

console.log(`✅ 監聽啟動，目前 ${window._geminiData.size} 輪。`);

// ── STEP 2: Download (run after collection is complete) ───────────────────────
window._observer.disconnect();
const turns = Array.from(window._geminiData.values()).sort((a, b) => a.order - b.order);
const blob = new Blob([JSON.stringify(turns, null, 2)], { type: 'application/json' });
const a = Object.assign(document.createElement('a'), {
  href: URL.createObjectURL(blob),
  download: 'gemini-conversation.json'
});
document.body.appendChild(a);
a.click();
document.body.removeChild(a);
console.log(`✅ 完成！共 ${turns.length} 輪，已下載。`);
