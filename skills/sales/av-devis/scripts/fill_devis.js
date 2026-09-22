#!/usr/bin/env node
const fs = require('fs-extra');
const path = require('path');
const Excel = require('exceljs');
const argv = require('minimist')(process.argv.slice(2));

const project = argv.project || argv.p;
const master = argv.master || path.join(__dirname, '../masters/Devis_Modulaire_MASTER.xlsx');
const dataPath = argv.data || path.join(__dirname, 'sample_input.json');
const outDir = argv.out || path.join(__dirname, '../out');
const mappingsPath = argv.mappings || path.join(__dirname, 'mappings.json');

if (!project) {
  console.error('Usage: node scripts/fill_devis.js --project "MonProjet" [--master <path>] [--data <json>] [--out <dir>]');
  process.exit(1);
}

if (!fs.existsSync(master)) {
  console.error('Master not found:', master);
  console.error('Place your master in skills/sales/av-devis/masters/ or pass --master');
  process.exit(1);
}

fs.ensureDirSync(outDir);
const outFile = path.join(outDir, `Devis_${project}.xlsx`);
fs.copyFileSync(master, outFile);
console.log('Copied master to', outFile);

let data = {};
if (fs.existsSync(dataPath)) {
  try { data = fs.readJsonSync(dataPath); } catch (e) { console.warn('Could not read data JSON:', e.message); }
} else {
  console.log('No data file found at', dataPath, '- proceeding with empty data.');
}

if (!fs.existsSync(mappingsPath)) {
  console.log('No mappings.json found at', mappingsPath + '.');
  console.log('To auto-fill cells, create mappings.json with entries like {"DESTINATAIRE!B2":"client", "Sheet1!C10":"numero_devis"}.');
  console.log('Dry-run complete. Open', outFile, 'to inspect the copied master.');
  process.exit(0);
}

(async () => {
  const mappings = fs.readJsonSync(mappingsPath);
  const wb = new Excel.Workbook();
  await wb.xlsx.readFile(outFile);
  for (const mappingKey of Object.keys(mappings)) {
    const field = mappings[mappingKey];
    const val = data[field];
    if (val === undefined) {
      console.log(`No value for field '${field}' (mapping ${mappingKey}) — skipping`);
      continue;
    }
    const parts = mappingKey.split('!');
    if (parts.length !== 2) { console.warn('Invalid mapping key (expect Sheet!Cell):', mappingKey); continue; }
    const sheetName = parts[0];
    const cell = parts[1];
    const sheet = wb.getWorksheet(sheetName) || wb.getWorksheet(sheetName.replace(/\r|\n/g,''));
    if (!sheet) { console.warn('Sheet not found:', sheetName, '- skipping mapping', mappingKey); continue; }
    sheet.getCell(cell).value = val;
    console.log(`Wrote ${field} => ${sheetName}!${cell}`);
  }
  await wb.xlsx.writeFile(outFile);
  console.log('Filled file written to', outFile);
})().catch(err => { console.error('Error:', err); process.exit(2); });
