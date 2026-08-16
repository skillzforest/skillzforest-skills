Placez le master `Devis_Modulaire_TMA_MASTER.xlsx` dans ce dossier.

Exemple `mappings.json` (XLSX) :
```
{
	"DESTINATAIRE!B2": "client",
	"METADATA!B2": "numero_devis",
	"METADATA!B3": "date",
	"Sheet1!A10": "line_1_description"
}
```

Commande :
```
node scripts/fill_master.js --skill av-devis-tma --master .agents/skills/av-devis-tma/masters/Devis_Modulaire_TMA_MASTER.xlsx --data .agents/skills/av-devis-tma/input.json --name v1 --out .agents/skills/av-devis-tma/out
```

Remarque : pour XLSX le mapping doit être `SheetName!Cell` → `fieldName` et le script écrira la valeur directement dans la cellule. Si vos cellules utilisent des formules dépendantes, elles seront recalculées par Excel lors de l'ouverture.
