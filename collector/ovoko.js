// Run in a browser tab already open on https://ovoko.es (same-origin fetch).
// Returns a JSON string: {platform, fetched_at, counts, items:[...]}.
// Low volume: one search per code, ~1 s between pages.
(async () => {
  const P = s => s ? parseFloat(s.replace(/\./g, '').replace(',', '.')) : null;
  const all = [], counts = {};
  for (const q of ['9834609880', 'A3C0320410001', '9815023380']) {
    for (let p = 1; p <= 12; p++) {
      const html = await (await fetch('https://ovoko.es/buscar?q=' + q + '&page=' + p)).text();
      const d = new DOMParser().parseFromString(html, 'text/html');
      if (p === 1) { const m = html.match(/(\d+)\s*piezas encontradas/); counts[q] = m ? +m[1] : null; }
      const cards = d.querySelectorAll('a[data-testid="item-card-horizontal-container"]');
      if (!cards.length) break;
      for (const c of cards) {
        const href = c.getAttribute('href');
        if (/match_type=partial/.test(href)) continue;
        const priceArea = (c.querySelector('[class*=areaPrice]') || c).textContent.replace(/\s+/g, ' ');
        all.push({
          query: q, url: 'https://ovoko.es' + href.split('?')[0],
          id: href.split('/')[2].split('-')[0].toUpperCase(),
          title: (c.querySelector('p') || {}).textContent,
          donor: ((c.querySelector('[data-testid=vehicle-details]') || {}).textContent || '').replace('Tomado de:', '').replace(/\s+/g, ' ').trim(),
          codes: [...c.querySelectorAll('[data-testid=product-code]')].map(x => x.textContent.trim()),
          seller: (c.querySelector('[data-testid=seller-info-title]') || {}).textContent,
          price: P((priceArea.match(/([\d\.]+,\d{2})\s*€/) || [])[1]),
          img: (c.querySelector('img') || {}).src || null
        });
      }
      await new Promise(r => setTimeout(r, 1000));
    }
  }
  const items = [...new Map(all.map(x => [x.id, x])).values()];
  return JSON.stringify({ platform: 'ovoko', fetched_at: new Date().toISOString(), counts, items });
})();
