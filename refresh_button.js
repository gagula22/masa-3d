/* Discord scraper — to be pasted into Discord console after Discord channel loads.
 * Outputs a JSON file with new videos found.
 */
(async function() {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const sc = document.querySelector('div.scroller__36d07[class*="customTheme"]') ||
             document.querySelector('[class*="scroller"][class*="customTheme"]');
  if (!sc) { alert('לא נמצא ערוץ דיסקורד. ודא שאתה בערוץ הלייבים.'); return; }

  const messages = {};

  function capture() {
    const items = document.querySelectorAll('li[id^="chat-messages-"]');
    for (const li of items) {
      const id = li.id;
      if (messages[id]) continue;
      const timestamp = li.querySelector('time')?.getAttribute('datetime') || null;
      const links = Array.from(li.querySelectorAll('a[href]')).map(a => a.href);
      const embeds = Array.from(li.querySelectorAll('[class*="embedWrapper"], article[class*="embed"]')).map(e => ({
        title: e.querySelector('[class*="embedTitle"]')?.textContent || null,
        url: e.querySelector('a[class*="embedTitleLink"]')?.href || e.querySelector('a[href]')?.href || null,
      }));
      messages[id] = { id, timestamp, links, embeds };
    }
  }

  // Scroll up to load latest 50-60 messages
  capture();
  for (let i = 0; i < 12; i++) {
    sc.scrollTop = Math.max(0, sc.scrollTop - 800);
    sc.dispatchEvent(new Event('scroll', { bubbles: true }));
    await sleep(700);
    capture();
  }

  // Extract videos
  const videos = [];
  for (const m of Object.values(messages)) {
    if (!m.timestamp) continue;
    const sources = new Set();
    for (const l of m.links) {
      const yt = l.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/))([A-Za-z0-9_-]+)/);
      if (yt) sources.add('yt:' + yt[1]);
      const vm = l.match(/vimeo\.com\/(?:video\/)?(\d+)/);
      if (vm) sources.add('vimeo:' + vm[1]);
    }
    for (const e of m.embeds) {
      if (e.url) {
        const yt = e.url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/))([A-Za-z0-9_-]+)/);
        if (yt) sources.add('yt:' + yt[1]);
        const vm = e.url.match(/vimeo\.com\/(?:video\/)?(\d+)/);
        if (vm) sources.add('vimeo:' + vm[1]);
      }
    }
    for (const s of sources) {
      videos.push({
        d: m.timestamp.substring(0, 10),
        s,
        ttl: (m.embeds[0]?.title || '').replace(/\s+/g, ' ').substring(0, 200),
      });
    }
  }

  // Dedupe
  const seen = new Set();
  const unique = videos.filter(v => seen.has(v.s) ? false : (seen.add(v.s), true));
  unique.sort((a, b) => a.d.localeCompare(b.d));

  // Download as JSON file
  const blob = new Blob([JSON.stringify(unique, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'discord_lives_' + Date.now() + '.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  console.log(`%c✓ נמצאו ${unique.length} סרטונים. הקובץ נשמר ב-Downloads.`,
              'background:#26A69A;color:#fff;padding:4px 8px;font-size:14px');
  alert(`נמצאו ${unique.length} סרטונים. הקובץ ירד.\nחזור לאתר וטען את הקובץ.`);
})();
