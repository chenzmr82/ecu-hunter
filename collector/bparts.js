// Run in a browser tab already open on https://www.b-parts.com/es (same-origin fetch).
// Reads the structured search results embedded in each page (__NEXT_DATA__).
(async () => {
  const items = new Map(), counts = {};
  for (const q of ['9834609880', 'A3C0320410001', '9815023380']) {
    for (let p = 1; p <= 20; p++) {
      const t = await (await fetch('https://www.b-parts.com/es/recambios-auto/search?reference=' + q + '&page=' + p)).text();
      const node = new DOMParser().parseFromString(t, 'text/html').querySelector('#__NEXT_DATA__');
      if (!node) break;
      const qs = JSON.parse(node.textContent).props.pageProps.dehydratedState.queries;
      const qd = qs.find(x => x.state && x.state.data && Array.isArray(x.state.data.results));
      if (!qd) break;
      const data = qd.state.data;
      if (p === 1) counts[q] = data.count ?? null;
      if (!data.results.length) break;
      for (const r of data.results) {
        const c = JSON.parse(JSON.stringify(r));
        delete c.images; delete c.listWithImages;
        c._query = q;
        if (!items.has(c.sku)) items.set(c.sku, c);
      }
      if (data.results.length < 15) break;
      await new Promise(r => setTimeout(r, 900));
    }
  }
  return JSON.stringify({ platform: 'bparts', fetched_at: new Date().toISOString(), counts, items: [...items.values()] });
})();
