Placez le master `Presentation_MASTER.pptx` dans ce dossier.

Exemple `mappings.json` pour PPTX :
```
{
	"placeholders": {
		"PROJECT_TITLE": "titre",
		"SUMMARY": "resume"
	}
}
```

Exemple de commande :
```
node scripts/fill_master.js --skill presales-client-presentation --master skills/sales/presales-client-presentation/masters/Presentation_MASTER.pptx --data skills/sales/presales-client-presentation/input.json --name v1 --out skills/sales/presales-client-presentation/out
```

Remarque : le remplacement PPTX est effectué en remplaçant le texte dans les fichiers XML `ppt/slides/slideN.xml`. Comme pour DOCX, assurez-vous que chaque placeholder est contenu dans un seul run (texte continu) pour une fiabilité maximale.
