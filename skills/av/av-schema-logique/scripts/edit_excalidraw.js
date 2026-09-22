/*
  Éditeur de template Excalidraw — commun aux skills av-schema-logique / av-schema-physique.  (v2)
  Usage : node edit_excalidraw.js <template.json> <edits.json> <sortie.excalidraw>

  edits.json (tous les champs optionnels) :
  {
    "title": "Nom du projet",              // remplace [Marque] partout (titre)
    "replace":  { "ancien": "nouveau" },   // substitutions de texte (substring, sensible à la casse)
    "relabel":  [ { "find": "Server Side Rendering", "replace": "Boutique hébergée" } ], // ordonné
    "remove_by_text": ["QR CODE", "création job"], // supprime blocs ET labels libres contenant la chaîne
    "remove_ids": ["db2"],                 // supprime des rectangles par id (+ texte + flèches liés)
    "drop_redundancy": false,              // true : retire les blocs "replica/réplication" + flèches
    "align": [                             // reboucher les trous / aligner après suppression
      { "ids": ["svc0","svc1"], "axis": "x", "gap": 24 },   // distribue en ligne, même y (min)
      { "ids": ["a","b","c"],   "axis": "y", "gap": 24 },   // distribue en colonne, même x (min)
      { "ids": ["c1","c2","c3","c4"], "grid": { "cols": 2, "gapx": 24, "gapy": 24 } }
    ]
  }

  IMPORTANT (ciblage) : les libellés de blocs sont souvent MULTI-LIGNES. Pour `find` / `remove_by_text`,
  vise une sous-chaîne présente sur UNE seule ligne (ex. "Machine Learning") ou insère un vrai \n.

  Sortie toujours cohérente : flèches/labels liés à un bloc supprimé retirés, références orphelines
  nettoyées. En fin de traitement, la console liste les LABELS NON RATTACHÉS (candidats orphelins type
  "création job") à examiner / ajouter à remove_by_text.
*/
const fs = require('fs');
const [,, TPL, EDITS, OUT = 'out.excalidraw'] = process.argv;
const doc = JSON.parse(fs.readFileSync(TPL, 'utf8'));
const edits = EDITS && fs.existsSync(EDITS) ? JSON.parse(fs.readFileSync(EDITS, 'utf8')) : {};
let els = doc.elements || [];
const byId = () => Object.fromEntries(els.map(e => [e.id, e]));

// 1) Substitutions de texte : title -> [Marque], puis replace{} (map), puis relabel[] (ordonné).
const applyMap = (s, m) => { if (typeof s !== 'string') return s; for (const [k, v] of Object.entries(m)) s = s.split(k).join(v); return s; };
const applyList = (s, l) => { if (typeof s !== 'string') return s; for (const { find, replace } of l) if (typeof find === 'string' && typeof replace === 'string') s = s.split(find).join(replace); return s; };
const replaceMap = Object.assign({}, edits.replace || {});
if (edits.title) replaceMap['[Marque]'] = edits.title;
const relabel = Array.isArray(edits.relabel) ? edits.relabel : [];
for (const e of els) if (e.type === 'text') for (const k of ['text', 'originalText'])
  if (typeof e[k] === 'string') e[k] = applyList(applyMap(e[k], replaceMap), relabel);

// 2) Suppression.
const removeIds = new Set(edits.remove_ids || []);
const redun = edits.drop_redundancy ? (edits.redundancy_markers || ['replica', 'réplication']) : [];
const markers = [].concat(edits.remove_by_text || [], redun);
if (markers.length) for (const e of els)
  if (e.type === 'text' && typeof e.text === 'string' && markers.some(s => e.text.toLowerCase().includes(String(s).toLowerCase())))
    removeIds.add(e.containerId || e.id);

let changed = true;
while (changed) {
  changed = false;
  for (const e of els) {
    if (removeIds.has(e.id)) for (const b of (e.boundElements || [])) if (b && b.id && !removeIds.has(b.id)) { removeIds.add(b.id); changed = true; }
    if (e.type === 'arrow') {
      const s = e.startBinding && e.startBinding.elementId, t = e.endBinding && e.endBinding.elementId;
      if ((s && removeIds.has(s)) || (t && removeIds.has(t))) if (!removeIds.has(e.id)) { removeIds.add(e.id); changed = true; }
    }
    if (e.type === 'text' && e.containerId && removeIds.has(e.containerId) && !removeIds.has(e.id)) { removeIds.add(e.id); changed = true; }
  }
}
els = els.filter(e => !removeIds.has(e.id));

// 3) Alignement / distribution (rebouche les trous). Déplace aussi les labels bound (containerId).
const shift = (id, dx, dy) => { const m = byId(); const e = m[id]; if (!e) return; e.x += dx; e.y += dy; for (const t of els) if (t.type === 'text' && t.containerId === id) { t.x += dx; t.y += dy; } };
for (const op of (edits.align || [])) {
  const m = byId();
  const items = (op.ids || []).map(id => m[id]).filter(Boolean);
  if (!items.length) continue;
  if (op.grid && op.grid.cols) {
    const cols = op.grid.cols, gx = op.grid.gapx ?? 24, gy = op.grid.gapy ?? 24;
    const x0 = op.grid.x0 ?? Math.min(...items.map(e => e.x)), y0 = op.grid.y0 ?? Math.min(...items.map(e => e.y));
    const cw = Math.max(...items.map(e => e.width)), ch = Math.max(...items.map(e => e.height));
    items.forEach((e, i) => { const c = i % cols, r = (i / cols) | 0; shift(e.id, (x0 + c * (cw + gx)) - e.x, (y0 + r * (ch + gy)) - e.y); });
  } else if (op.axis === 'x') {
    const y = op.y0 ?? Math.min(...items.map(e => e.y)); const gap = op.gap ?? 24; let x = op.x0 ?? Math.min(...items.map(e => e.x));
    for (const e of items) { shift(e.id, x - e.x, y - e.y); x += e.width + gap; }
  } else if (op.axis === 'y') {
    const x = op.x0 ?? Math.min(...items.map(e => e.x)); const gap = op.gap ?? 24; let y = op.y0 ?? Math.min(...items.map(e => e.y));
    for (const e of items) { shift(e.id, x - e.x, y - e.y); y += e.height + gap; }
  }
}

// 4) Intégrité finale : plus aucune référence vers un id disparu.
const alive = new Set(els.map(e => e.id));
for (const e of els) {
  if (Array.isArray(e.boundElements)) e.boundElements = e.boundElements.filter(b => b && b.id && alive.has(b.id));
  for (const k of ['startBinding', 'endBinding']) if (e[k] && e[k].elementId && !alive.has(e[k].elementId)) e[k] = null;
  if (e.frameId && !alive.has(e.frameId)) e.frameId = null;
}
doc.elements = els;
fs.writeFileSync(OUT, JSON.stringify(doc, null, 2));

// 5) Rapport : labels non rattachés (candidats orphelins à balayer).
const loose = els.filter(e => e.type === 'text' && !e.containerId && String(e.text || '').trim().split(/\s+/).length <= 3
  && !/architecture logique/i.test(e.text || '')).map(e => e.text.replace(/\n/g, ' / '));
console.log('OK', OUT, '| éléments:', els.length, '| supprimés:', removeIds.size);
if (loose.length) console.log('Labels non rattachés à vérifier (candidats orphelins):', JSON.stringify(loose));
