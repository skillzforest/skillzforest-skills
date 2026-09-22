#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const minimist = require('minimist');
const ExcelJS = require('exceljs');
const AdmZip = require('adm-zip');

async function fillXlsx(masterPath, outPath, mappings, data) {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.readFile(masterPath);
  for (const key of Object.keys(mappings)) {
    // key format: Sheet!A1
    const parts = key.split('!');
    const sheetName = parts[0];
    const cell = parts[1];
    const sheet = wb.getWorksheet(sheetName) || wb.getWorksheet(Number(sheetName) || 1);
    if (!sheet) continue;
    const value = data[mappings[key]];
    if (value !== undefined) sheet.getCell(cell).value = value;
  }
  await wb.xlsx.writeFile(outPath);
  console.log('Wrote', outPath);
}

function copyMaster(src, dest) {
  fs.copyFileSync(src, dest, fs.constants.COPYFILE_EXCL);
  console.log('Copied master to', dest);
}

// Skills live under skills/<domain>/<skill-name>/ — find the domain folder
// that actually contains this skill instead of hardcoding one.
function findSkillDir(skill) {
  const skillsRoot = path.join('skills');
  const domains = fs.existsSync(skillsRoot) ? fs.readdirSync(skillsRoot) : [];
  for (const domain of domains) {
    const candidate = path.join(skillsRoot, domain, skill);
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

async function main() {
  const argv = minimist(process.argv.slice(2));
  const skill = argv.skill;
  const master = argv.master;
  const dataFile = argv.data;
  const outDir = argv.out || path.join(path.dirname(master), '..', 'out');
  if (!skill || !master) {
    console.error('Usage: node scripts/fill_master.js --skill <skill> --master <masterPath> [--data <data.json>] [--out <outDir>]');
    process.exit(2);
  }
  fs.mkdirSync(outDir, { recursive: true });
  const ext = path.extname(master).toLowerCase();
  const filename = path.basename(master, ext) + '_' + (argv.name || 'filled') + ext;
  const outPath = path.join(outDir, filename);
  const data = dataFile ? JSON.parse(fs.readFileSync(dataFile, 'utf8')) : {};
  // try to load mappings from same skill folder
  const skillDir = findSkillDir(skill);
  let mappings = {};
  if (skillDir) {
    const mappingsPath = path.join(skillDir, 'mappings.json');
    if (fs.existsSync(mappingsPath)) {
      mappings = JSON.parse(fs.readFileSync(mappingsPath, 'utf8'));
    } else {
      const example = path.join(skillDir, 'mappings.example.json');
      if (fs.existsSync(example)) console.warn('No mappings.json found, using example as reference:', example);
    }
  } else {
    console.warn(`Skill '${skill}' not found under skills/*/${skill} — proceeding without mappings.`);
  }

  if (ext === '.xlsx' || ext === '.xls') {
    await fillXlsx(master, outPath, mappings, data);
    return;
  }

  // DOCX/PPTX basic placeholder replacement using XML text replacement.
  if (ext === '.docx') {
    try {
      const zip = new AdmZip(master);
      const docEntry = zip.getEntry('word/document.xml');
      if (docEntry) {
        let xml = docEntry.getData().toString('utf8');
        const placeholders = mappings.placeholders || inferPlaceholders(mappings);
        for (const key of Object.keys(placeholders)) {
          const field = placeholders[key];
          const value = data[field] !== undefined ? data[field] : '';
          const ph = key.startsWith('{{') ? key : `{{${key}}}`;
          xml = xml.split(ph).join(value);
        }
        zip.updateFile('word/document.xml', Buffer.from(xml, 'utf8'));
      }
      zip.writeZip(outPath);
      console.log('Wrote', outPath);
    } catch (e) {
      console.error('DOCX processing failed:', e.message);
      copyMaster(master, outPath);
    }
    console.warn('Note: DOCX placeholder replacement is simple XML replace; placeholders must not be split across runs.');
    return;
  }

  if (ext === '.pptx') {
    try {
      const zip = new AdmZip(master);
      const placeholders = mappings.placeholders || inferPlaceholders(mappings);
      const entries = zip.getEntries();
      for (const entry of entries) {
        if (/^ppt\/slides\/slide\d+\.xml$/.test(entry.entryName)) {
          let xml = entry.getData().toString('utf8');
          for (const key of Object.keys(placeholders)) {
            const field = placeholders[key];
            const value = data[field] !== undefined ? data[field] : '';
            const ph = key.startsWith('{{') ? key : `{{${key}}}`;
            xml = xml.split(ph).join(value);
          }
          zip.updateFile(entry.entryName, Buffer.from(xml, 'utf8'));
        }
      }
      zip.writeZip(outPath);
      console.log('Wrote', outPath);
    } catch (e) {
      console.error('PPTX processing failed:', e.message);
      copyMaster(master, outPath);
    }
    console.warn('Note: PPTX placeholder replacement is simple XML replace; placeholders must not be split across runs.');
    return;
  }

  // For unknown types just copy
  copyMaster(master, outPath);
  console.warn('Auto-fill for this filetype not implemented; copied master only.');
}

function inferPlaceholders(mappings) {
  // If mappings keys are not Sheet!Cell but simple placeholder->field map, normalize
  const out = {};
  for (const k of Object.keys(mappings)) {
    if (k.includes('!')) continue;
    out[k] = mappings[k];
  }
  return out;
}

main().catch(err => { console.error(err); process.exit(1); });
