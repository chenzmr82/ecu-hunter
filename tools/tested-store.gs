// Google Apps Script bound to the "ECU hunter – probadas" sheet, deployed as a web app.
// The page (site/app.js) reads GET and writes POST. Append-only log: the last row per key wins.
var SHEET = 'probadas';

function sheet_() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(SHEET) || ss.insertSheet(SHEET);
  if (sh.getLastRow() === 0) sh.appendRow(['time', 'key', 'tested', 'label']);
  return sh;
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  var rows = sheet_().getDataRange().getValues().slice(1);
  var state = {};
  rows.forEach(function (r) { state[r[1]] = { tested: r[2] === true || r[2] === 'TRUE', at: r[0], label: r[3] }; });
  var out = Object.keys(state).filter(function (k) { return state[k].tested; })
    .map(function (k) { return { key: k, at: state[k].at, label: state[k].label }; });
  return json_({ tested: out });
}

function doPost(e) {
  var d = JSON.parse(e.postData.contents || '{}');
  var sh = sheet_();
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    (d.keys || []).slice(0, 50).forEach(function (k) {
      if (/^(ovoko|bparts|ebay):[A-Za-z0-9_-]{1,40}$/.test(k)) {
        sh.appendRow([new Date(), k, !!d.tested, String(d.label || '').slice(0, 200)]);
      }
    });
  } finally {
    lock.releaseLock();
  }
  return json_({ ok: true });
}
