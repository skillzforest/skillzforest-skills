Placez le master `Compte_rendu_reunion_template_MASTER.docx` dans ce dossier.

Exemple `mappings.json` pour CR (DOCX) :
```
{
	"placeholders": {
		"MEETING_DATE": "date",
		"ATTENDEES": "participants",
		"OBJECT": "object"
	}
}
```

Exemple de `input.json` :
```
{
	"date": "2026-08-16",
	"participants": "Alice, Bob",
	"object": "Atelier cadrage"
}
```

Commande :
```
node scripts/fill_master.js --skill presales-meeting-notes --master skills/sales/presales-meeting-notes/masters/Compte_rendu_reunion_template_MASTER.docx --data skills/sales/presales-meeting-notes/input.json --name v1 --out skills/sales/presales-meeting-notes/out
```

Pour les sections répétées (liste d'actions), le remplacement XML simple ne suffit pas : il faudra un script Node qui duplique des blocs dans le DOCX ou utiliser `docxtemplater`. Dites si vous voulez que j'ajoute ce flux.
