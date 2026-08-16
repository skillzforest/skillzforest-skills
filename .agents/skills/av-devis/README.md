# av-devis — local scaffold

Ce dossier contient un outil local pour copier et remplir le master `Devis_Modulaire_MASTER.xlsx` en mode dry-run.

Installation :

```bash
cd .agents/skills/av-devis
npm install
```

Exécution (dry-run) :

```bash
node scripts/fill_devis.js --project "MonProjet" --master masters/Devis_Modulaire_MASTER.xlsx --data sample_input.json --out out
```

Si vous fournissez `mappings.json` (format exemple dans `mappings.example.json`), le script appliquera automatiquement les champs du JSON vers les cellules indiquées.

Notes :
- Le script est volontairement minimal pour servir de point d'extension : vous pouvez ajouter l'upload Drive / copy_file / API Sheets plus tard.
- Ce mode permet à un client d'acheter la skill et d'exécuter localement en déposant ses masters.
