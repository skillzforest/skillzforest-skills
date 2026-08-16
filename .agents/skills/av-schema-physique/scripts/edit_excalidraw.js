/*
  Éditeur de template Excalidraw — commun aux skills av-schema-logique / av-schema-physique.
  Usage : node edit_excalidraw.js <template.json> <edits.json> <sortie.excalidraw>

  edits.json (tous les champs optionnels) :
  {
    "title": "Nom du projet",              // remplace [Marque] partout (titre)
    "replace": { "ancien": "nouveau" },    // substitutions de texte (IP, capacités, techno, tenants…)
    "remove_by_text": ["QR CODE"],         // supprime les blocs dont un texte contient ces chaînes
    "remove_ids": ["db2"],                 // supprime des rectangles par id (+ texte + flèches liés)
    "drop_redundancy": false                // true : retire les éléments en pointillés (redondance) + flèches liées
  }

  Règles : n'édite que le CONTENU (textes) et la présence de blocs ; ne recalcule pas la mise en page.
  Après génération : ouvrir dans Excalidraw, ajuster si besoin, exporter en PNG/SVG.
*/
const fs = require('fs');

const [,, TPL, EDITS, OUT='out.excalidraw'] = process.argv;
const doc = JSON.parse(fs.readFileSync(TPL, 'utf8'));
const edits = EDITS && fs.existsSync(EDITS) ? JSON.parse(fs.readFileSync(EDITS, 'utf8')) : {};
let els = doc.elements || [];

// 1) Substitutions de texte (titre + valeurs)
const replaceMap = Object.assign({}, edits.replace || {});
if (edits.title) replaceMap['[Marque]'] = edits.title;
const applyRepl = (s) => {
  if (typeof s !== 'string') return s;
  for (const [k, v] of Object.entries(replaceMap)) s = s.split(k).join(v);
  return s;
};
for (const e of els) {
  if (e.type === 'text') {
    if (typeof e.text === 'string') e.text = applyRepl(e.text);
    if (typeof e.originalText === 'string') e.originalText = applyRepl(e.originalText);
  }
}

// 2) Constitution de l'ensemble des ids à supprimer
const removeIds = new Set(edits.remove_ids || []);

// 2a) redondance : cibler le(s) bloc(s) replica par SÉMANTIQUE (marqueur texte),
//     jamais par style de trait (les pointillés peuvent être un choix graphique global).
const redunMarkers = edits.drop_redundancy ? (edits.redundancy_markers || ['replica', 'réplication']) : [];

// 2b) suppression par texte (remove_by_text + marqueurs de redondance)
//     → rectangle conteneur (via containerId) sinon le texte lui-même
const textMarkers = [].concat(edits.remove_by_text || [], redunMarkers);
if (textMarkers.length) {
  for (const e of els) {
    if (e.type === 'text' && typeof e.text === 'string' &&
        textMarkers.some(sub => e.text.toLowerCase().includes(String(sub).toLowerCase()))) {
      removeIds.add(e.containerId || e.id);
    }
  }
}

// 3) Cascade : pour chaque rectangle supprimé, retirer ses textes + flèches liés ;
//    retirer aussi toute flèche dont une extrémité pointe un élément supprimé ;
//    retirer les textes dont le containerId est supprimé.
let changed = true;
while (changed) {
  changed = false;
  for (const e of els) {
    if (removeIds.has(e.id)) {
      for (const b of (e.boundElements || [])) {
        if (b && b.id && !removeIds.has(b.id)) { removeIds.add(b.id); changed = true; }
      }
    }
    if (e.type === 'arrow') {
      const s = e.startBinding && e.startBinding.elementId;
      const t = e.endBinding && e.endBinding.elementId;
      if ((s && removeIds.has(s)) || (t && removeIds.has(t))) {
        if (!removeIds.has(e.id)) { removeIds.add(e.id); changed = true; }
      }
    }
    if (e.type === 'text' && e.containerId && removeIds.has(e.containerId) && !removeIds.has(e.id)) {
      removeIds.add(e.id); changed = true;
    }
  }
}

// 4) Filtrage + nettoyage des références boundElements vers des ids supprimés
els = els.filter(e => !removeIds.has(e.id));
for (const e of els) {
  if (Array.isArray(e.boundElements)) {
    e.boundElements = e.boundElements.filter(b => b && b.id && !removeIds.has(b.id));
  }
}
doc.elements = els;

fs.writeFileSync(OUT, JSON.stringify(doc, null, 2));
console.log('OK', OUT, '| éléments:', els.length, '| supprimés:', removeIds.size);
