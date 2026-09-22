Placez ici les fichiers masters utilisés par la skill `av-devis`.

-- Nom recommandé: `Devis_Modulaire_MASTER.xlsx`.
- Ne modifiez jamais le fichier master original. Le script local fera une copie avant toute écriture.
- Si vous souhaitez l'auto-remplir localement, ajoutez un fichier `mappings.json` au même niveau que `scripts/fill_devis.js` décrivant les cellules à remplir.

Exemple de commande (depuis la racine du repo) :

```bash
cd skills/av/av-devis
npm install
node scripts/fill_devis.js --project "MonProjet" --master masters/Devis_Modulaire_MASTER.xlsx --data sample_input.json --out out
```
