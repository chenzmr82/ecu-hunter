(function () {
  "use strict";

  var I18N = {
    es: {
      title: "Cazador de centralita",
      subtitle: "Peugeot 3008 1.2 PureTech 130 · Continental VD56.1",
      search: "Buscar: modelo, vendedor, código…",
      f_hide_tried: "Ocultar ya probadas",
      f_warranty: "Solo con garantía ≥ 12 meses",
      f_unlocked: "Solo virgen / desbloqueada",
      f_hide_kits: "Ocultar kits",
      f_same_engine: "Solo mismo motor (130 CV)",
      h_new: "Nuevas (24–48 h)",
      h_a: "Confirmadas: A3C y HW exactos",
      hint_a: "A3C0320410001 y HW 9815023380 indicados por el vendedor. Falta confirmar el inmovilizador con el vendedor.",
      h_n: "Por verificar",
      hint_n: "Falta el A3C o el HW en el anuncio, o aparece con un dígito distinto. Pedir foto de la etiqueta antes de comprar.",
      h_x: "Descartadas",
      hint_x: "Diésel, otro motor, otro A3C, bloqueadas, o el código solo aparece en una lista pegada de decenas de referencias.",
      foot: 'Datos públicos de Ovoko, B-Parts y eBay. Precios de Ovoko sin envío ni tarifa de servicio. Para marcar una unidad como probada, edita <a id="tried-link" href="#">data/tried.yaml</a>.',
      last_run: "Última búsqueda",
      runs: "búsquedas",
      s_a: "confirmadas", s_n: "por verificar", s_new: "nuevas 24–48 h", s_offers: "anuncios",
      none: "Nada por ahora.",
      unit_offers: "anuncios",
      open: "Abrir",
      ask: "Copiar mensaje al vendedor",
      copied: "Mensaje copiado",
      mark_tried: "Marcar como probada",
      ship_free: "envío gratis", ship_inc: "envío e IVA incl.", plus_ship: "+ envío",
      warranty: "garantía", months: "meses", returns: "devolución", days: "días", free_ret: "devolución gratis",
      listed: "publicado", from: "desde", non_eu: "fuera UE: posibles aduanas",
      imm_unlocked: "Virgen / desbloqueada", imm_locked: "Bloqueada", imm_kit: "Kit (ECU + cerradura/llave)", imm_unknown: "Inmovilizador: ¿?",
      same_engine: "Mismo motor 130 CV", accident: "Coche siniestrado",
      NEW: "NUEVA", RECENT: "RECIENTE", PRICE_DOWN: "BAJA DE PRECIO", GONE: "YA NO ESTÁ", TRIED: "YA PROBADA",
      same_unit: "Misma unidad en varios anuncios", conf_definitive: "seguro", conf_strong: "muy probable", conf_probable: "probable",
      tried_note: "Probada y devuelta",
      km: "km", unknown_price: "precio ¿?",
      gone_offer: "retirado",
      last_seen: "visto por última vez", seller_says: "Vendedor", src_off: "sin clave API"
    },
    en: {
      title: "ECU hunter",
      subtitle: "Peugeot 3008 1.2 PureTech 130 · Continental VD56.1",
      search: "Search: model, seller, code…",
      f_hide_tried: "Hide already tried",
      f_warranty: "Only ≥ 12-month warranty",
      f_unlocked: "Only virgin / unlocked",
      f_hide_kits: "Hide kits",
      f_same_engine: "Only same engine (130 hp)",
      h_new: "New (24–48 h)",
      h_a: "Confirmed: A3C and HW exact",
      hint_a: "A3C0320410001 and HW 9815023380 stated by the seller. Immobiliser status still to confirm with the seller.",
      h_n: "Needs check",
      hint_n: "A3C or HW missing from the listing, or one digit off. Ask for a label photo before buying.",
      h_x: "Excluded",
      hint_x: "Diesel, other engine, other A3C, locked, or the code only appears inside a pasted list of dozens of references.",
      foot: 'Public data from Ovoko, B-Parts and eBay. Ovoko prices exclude shipping and service fee. To mark a unit as tried, edit <a id="tried-link" href="#">data/tried.yaml</a>.',
      last_run: "Last search",
      runs: "searches",
      s_a: "confirmed", s_n: "needs check", s_new: "new 24–48 h", s_offers: "listings",
      none: "Nothing yet.",
      unit_offers: "listings",
      open: "Open",
      ask: "Copy message to seller",
      copied: "Message copied",
      mark_tried: "Mark as tried",
      ship_free: "free shipping", ship_inc: "shipping & VAT incl.", plus_ship: "+ shipping",
      warranty: "warranty", months: "months", returns: "returns", days: "days", free_ret: "free returns",
      listed: "listed", from: "from", non_eu: "non-EU: possible customs",
      imm_unlocked: "Virgin / unlocked", imm_locked: "Locked", imm_kit: "Kit (ECU + lock/key)", imm_unknown: "Immobiliser: ?",
      same_engine: "Same engine 130 hp", accident: "Accident car",
      NEW: "NEW", RECENT: "RECENT", PRICE_DOWN: "PRICE DROP", GONE: "GONE", TRIED: "TRIED",
      same_unit: "Same unit in several listings", conf_definitive: "certain", conf_strong: "very likely", conf_probable: "likely",
      tried_note: "Tried and returned",
      km: "km", unknown_price: "price ?",
      gone_offer: "removed",
      last_seen: "last seen", seller_says: "Seller", src_off: "no API key"
    }
  };
  var PLAT = { ovoko: "Ovoko", bparts: "B-Parts", ebay: "eBay" };

  var lang = "es";
  try { lang = localStorage.getItem("ecu-lang") || "es"; } catch (e) {}
  var DATA = null;

  function t(k) { return (I18N[lang] && I18N[lang][k]) || I18N.es[k] || k; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function eur(v) {
    if (v == null) return "";
    return new Intl.NumberFormat(lang === "es" ? "es-ES" : "en-GB", { style: "currency", currency: "EUR" }).format(v);
  }
  function fmtDate(iso, withTime) {
    if (!iso) return "";
    var d = new Date(iso);
    var o = { day: "2-digit", month: "short" };
    if (withTime) { o.hour = "2-digit"; o.minute = "2-digit"; }
    return d.toLocaleString(lang === "es" ? "es-ES" : "en-GB", o);
  }
  function num(n) { return n == null ? "" : new Intl.NumberFormat(lang === "es" ? "es-ES" : "en-GB").format(n); }

  function repoLinks() {
    var h = location.hostname, m = h.match(/^([^.]+)\.github\.io$/);
    var seg = location.pathname.split("/").filter(Boolean)[0];
    if (m && seg) return "https://github.com/" + m[1] + "/" + seg + "/edit/main/data/tried.yaml";
    return "../data/tried.yaml";
  }

  function applyStatic() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) { el.textContent = t(el.getAttribute("data-i18n")); });
    document.querySelectorAll("[data-i18n-ph]").forEach(function (el) { el.placeholder = t(el.getAttribute("data-i18n-ph")); });
    document.querySelectorAll("[data-i18n-html]").forEach(function (el) { el.innerHTML = t(el.getAttribute("data-i18n-html")); });
    var tl = document.getElementById("tried-link"); if (tl) tl.href = repoLinks();
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === lang));
    });
  }

  function codeTag(label, status) {
    var cls = status === "exact" ? "ok" : status === "near" ? "warn" : "bad";
    var mark = status === "exact" ? "✓" : status === "near" ? "≈" : "✗";
    return '<span class="tag ' + cls + '">' + label + " " + mark + "</span>";
  }

  function immTag(u) {
    var m = { unlocked: "ok", locked: "bad", kit: "warn", unknown: "" };
    return '<span class="tag ' + (m[u.immobiliser] || "") + '">' + esc(t("imm_" + u.immobiliser)) + "</span>";
  }

  function offerRow(o) {
    var price, sub = [];
    if (o.total_eur != null) {
      price = eur(o.total_eur);
      if (o.platform === "bparts") sub.push(t("ship_inc"));
      else if (o.shipping_eur === 0) sub.push(t("ship_free"));
      else if (o.shipping_eur) sub.push(eur(o.price_eur) + " + " + eur(o.shipping_eur));
    } else if (o.price_eur != null) {
      price = eur(o.price_eur);
      sub.push(o.platform === "ovoko" ? t("plus_ship") + " + tarifa" : t("plus_ship"));
    } else price = t("unknown_price");
    var meta = [];
    if (o.warranty_months) meta.push(t("warranty") + " " + o.warranty_months + " " + t("months"));
    if (o.free_returns) meta.push(t("free_ret") + (o.return_days ? " " + o.return_days + " " + t("days") : ""));
    else if (o.return_days) meta.push(t("returns") + " " + o.return_days + " " + t("days"));
    if (o.ships_from && o.ships_from !== "España") meta.push(t("from") + " " + o.ships_from);
    if (o.non_eu) meta.push("⚠ " + t("non_eu"));
    if (o.listed_at) meta.push(t("listed") + " " + fmtDate(o.listed_at, true));
    if (o.gone) meta.push(t("gone_offer"));
    else if (DATA && o.last_seen && o.last_seen !== DATA.last_run_at) meta.push(t("last_seen") + " " + fmtDate(o.last_seen));
    return '<tr class="' + (o.gone ? "gone" : "") + '">' +
      '<td><span class="plat">' + esc(PLAT[o.platform] || o.platform) + "</span><br><span class=\"meta\">" + esc(o.seller || o.platform_id) + "</span></td>" +
      '<td class="meta meta-col">' + esc(meta.join(" · ")) + "</td>" +
      '<td class="p"><b>' + esc(price) + "</b><br><span class=\"meta\">" + esc(sub.join(" ")) + "</span></td>" +
      '<td class="go"><a class="btn primary" href="' + esc(o.url) + '" target="_blank" rel="noopener noreferrer">' + esc(t("open")) + " ↗</a></td></tr>";
  }

  function card(u) {
    var d = u.donor || {};
    var donor = d.text || "";
    var bits = [];
    if (d.engine_code) bits.push(d.engine_code);
    if (d.kw) bits.push(d.kw + " kW");
    if (d.km) bits.push(num(d.km) + " " + t("km"));
    var tags = [codeTag("A3C", u.a3c), codeTag("HW", u.hw), codeTag("PSA", u.psa), immTag(u)];
    if (u.same_engine) tags.push('<span class="tag ok">' + esc(t("same_engine")) + "</span>");
    if (u.kit && u.immobiliser !== "kit") tags.push('<span class="tag warn">' + esc(t("imm_kit")) + "</span>");
    if (u.accident) tags.push('<span class="tag warn">' + esc(t("accident")) + "</span>");
    (u.badges || []).forEach(function (b) {
      var cls = b === "NEW" || b === "RECENT" ? "new" : b === "PRICE_DOWN" ? "ok" : "bad";
      tags.push('<span class="tag ' + cls + '">' + esc(t(b)) + "</span>");
    });
    var img = u.image
      ? '<img class="thumb" loading="lazy" referrerpolicy="no-referrer" alt="" src="' + esc(u.image) + '">'
      : '<div class="thumb ph">—</div>';
    var best = u.best_total_eur != null ? eur(u.best_total_eur) : t("unknown_price");
    var bestSub = u.best_total_known ? "" : t("plus_ship");
    var extra = "";
    if (u.reasons && u.reasons.length) extra += '<p class="reasons">' + esc(u.reasons.join(" · ")) + "</p>";
    (u.seller_comments || []).forEach(function (c) {
      extra += '<p class="reasons">💬 ' + esc(t("seller_says")) + " (" + esc(PLAT[c.platform] || c.platform) + "): “" + esc(c.text.replace(/\s+/g, " ")) + "”</p>";
    });
    if (u.notes && u.notes.length) extra += '<p class="notes">📝 ' + esc(u.notes.join(" · ")) + "</p>";
    if (u.dedupe) extra += '<p class="dedupe">🔗 ' + esc(t("same_unit")) + " (" + esc(t("conf_" + u.dedupe.confidence)) + "): " + esc(u.dedupe.why.join(", ")) + "</p>";
    if (u.tried) extra += '<p class="notes">↩ ' + esc(t("tried_note")) + (u.tried.returned ? " " + esc(u.tried.returned) : "") + (u.tried.reason ? ": " + esc(u.tried.reason) : "") + "</p>";
    var cls = "card" + (u.tried ? " tried" : "") + ((u.badges || []).indexOf("GONE") >= 0 ? " gone" : "") +
      ((u.badges || []).some(function (b) { return b === "NEW" || b === "RECENT"; }) ? " new" : "");
    return '<article class="' + cls + '" id="u-' + esc(u.id.replace(/[^a-zA-Z0-9]/g, "_")) + '">' + img +
      "<div>" +
      '<div class="head"><div><div class="donor">' + esc(donor) + "</div>" +
      '<div class="reasons">' + esc(bits.join(" · ")) + (u.offers.length > 1 ? " · " + u.offers.length + " " + esc(t("unit_offers")) : "") + "</div></div>" +
      '<div class="price">' + esc(best) + (bestSub ? "<small>" + esc(bestSub) + "</small>" : "") + "</div></div>" +
      '<div class="tags">' + tags.join("") + "</div>" + extra +
      '<table class="offers"><tbody>' + u.offers.map(offerRow).join("") + "</tbody></table>" +
      '<div class="actions"><button type="button" class="btn" data-ask="1">' + esc(t("ask")) + "</button>" +
      '<a class="btn" target="_blank" rel="noopener" href="' + esc(repoLinks()) + '">' + esc(t("mark_tried")) + "</a></div>" +
      "</div></article>";
  }

  function passes(u) {
    var q = (document.getElementById("q").value || "").trim().toLowerCase();
    if (document.getElementById("f-hide-tried").checked && u.tried) return false;
    if (document.getElementById("f-warranty").checked && !u.offers.some(function (o) { return (o.warranty_months || 0) >= 12; })) return false;
    if (document.getElementById("f-unlocked").checked && u.immobiliser !== "unlocked") return false;
    if (document.getElementById("f-hide-kits").checked && u.kit) return false;
    if (document.getElementById("f-same-engine").checked && !u.same_engine) return false;
    if (q) {
      var hay = [u.donor && u.donor.text, (u.codes_seen || []).join(" ")].concat(u.offers.map(function (o) {
        return [o.title, o.seller, o.platform, o.platform_id].join(" ");
      })).join(" ").toLowerCase();
      if (hay.indexOf(q) < 0) return false;
    }
    return true;
  }

  function fill(id, countId, list) {
    var el = document.getElementById(id);
    el.innerHTML = list.length ? list.map(card).join("") : '<p class="empty">' + esc(t("none")) + "</p>";
    document.getElementById(countId).textContent = "(" + list.length + ")";
  }

  function render() {
    applyStatic();
    if (!DATA) return;
    var tg = DATA.target;
    document.getElementById("target").innerHTML =
      "<code>A3C " + esc(tg.a3c) + "</code><code>HW " + esc(tg.hw) + "</code><code>PSA " + esc(tg.psa) + "</code>";
    var src = Object.keys(DATA.sources || {}).map(function (k) {
      var s = DATA.sources[k];
      return '<span class="' + (s.ok ? "src-ok" : "src-bad") + '">' + esc(PLAT[k] || k) + (s.ok ? " · " + s.kept : " ✗ " + (/API key/.test(s.error || "") ? t("src_off") : "")) + "</span>";
    });
    document.getElementById("status").innerHTML =
      "<span>" + esc(t("last_run")) + ": <b>" + esc(fmtDate(DATA.last_run_at, true)) + "</b> (" + DATA.runs + " " + esc(t("runs")) + ")</span>" + src.join("");

    var units = DATA.units.filter(passes);
    var isNew = function (u) { return (u.badges || []).some(function (b) { return b === "NEW" || b === "RECENT"; }); };
    var A = units.filter(function (u) { return u.grade === "A"; });
    var N = units.filter(function (u) { return u.grade === "N"; });
    var X = units.filter(function (u) { return u.grade === "X"; });
    var NEW = units.filter(function (u) { return u.grade !== "X" && isNew(u); });
    fill("list-new", "c-new", NEW);
    fill("list-a", "c-a", A);
    fill("list-n", "c-n", N);
    fill("list-x", "c-x", X);
    var nOffers = DATA.units.reduce(function (s, u) { return s + u.offers.length; }, 0);
    document.getElementById("stats").innerHTML = [
      [A.length, t("s_a")], [N.length, t("s_n")], [NEW.length, t("s_new")], [nOffers, t("s_offers")]
    ].map(function (x) { return '<div class="stat"><b>' + x[0] + "</b><span>" + esc(x[1]) + "</span></div>"; }).join("");
  }

  function toast(msg) {
    var el = document.getElementById("toast");
    el.textContent = msg; el.classList.add("show");
    setTimeout(function () { el.classList.remove("show"); }, 1600);
  }

  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-lang]");
    if (b) {
      lang = b.getAttribute("data-lang");
      try { localStorage.setItem("ecu-lang", lang); } catch (err) {}
      render();
      return;
    }
    if (e.target.closest("[data-ask]")) {
      var msg = (DATA && DATA.ask_seller_message_es) || "";
      var done = function () { toast(t("copied")); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(msg).then(done, function () { prompt("", msg); });
      else { window.prompt("", msg); }
    }
  });
  ["q", "f-hide-tried", "f-warranty", "f-unlocked", "f-hide-kits", "f-same-engine"].forEach(function (id) {
    document.getElementById(id).addEventListener(id === "q" ? "input" : "change", render);
  });

  fetch("data/units.json", { cache: "no-store" })
    .then(function (r) { return r.json(); })
    .then(function (d) { DATA = d; render(); })
    .catch(function () { document.getElementById("stats").innerHTML = '<p class="empty">units.json ✗</p>'; });
  applyStatic();
})();
