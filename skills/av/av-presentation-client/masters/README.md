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
node scripts/fill_master.js --skill av-presentation-client --master skills/av/av-presentation-client/masters/Presentation_MASTER.pptx --data skills/av/av-presentation-client/input.json --name v1 --out skills/av/av-presentation-client/out
```

Remarque : le remplacement PPTX est effectué en remplaçant le texte dans les fichiers XML `ppt/slides/slideN.xml`. Comme pour DOCX, assurez-vous que chaque placeholder est contenu dans un seul run (texte continu) pour une fiabilité maximale.
