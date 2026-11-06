// Run in a browser tab already open on https://www.ebay.es (same-origin fetch).
// Sorted by newly listed (_sop=10). Note: a future replacement is the official eBay Browse API.
(async () => {
  const out = new Map(), counts = {};
  for (const q of ['9834609880', 'A3C0320410001', '9815023380', 'A3C032041001']) {
    const t = await (await fetch('https://www.ebay.es/sch/i.html?_sop=10&_ipg=120&_nkw=' + q)).text();
    const d = new DOMParser().parseFromString(t, 'text/html');
    counts[q] = (d.querySelector('.srp-controls__count-heading') || {}).textContent;
    for (const li of d.querySelectorAll('li.s-card, li.s-item')) {
      const a = li.querySelector('a[href*="/itm/"]');
      if (!a) continue;
      const id = (a.href.match(/itm\/(\d+)/) || [])[1];
      if (!id || id === '123456') continue;
      const title = ((li.querySelector('.s-card__title, .s-item__title') || {}).textContent || '').trim();
      const r = { query: q, id, title, img: (li.querySelector('img') || {}).src || null, lines: [li.textContent] };
      if (!out.has(id)) out.set(id, r); else out.get(id).query += ',' + q;
    }
    await new Promise(r => setTimeout(r, 1200));
  }
  return JSON.stringify({ platform: 'ebay', fetched_at: new Date().toISOString(), counts, items: [...out.values()] });
})();
