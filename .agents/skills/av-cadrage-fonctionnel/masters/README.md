Placez le master `Cadrage_fonctionnel_template_MASTER.docx` dans ce dossier.

Étapes précises pour tests locaux
1) Placer le master dans `masters/`.
2) Créer un fichier `mappings.json` à côté du master. Pour DOCX/PPTX définissez la section `placeholders` :

Exemple `mappings.json` :
```
{
	"placeholders": {
		"PROJECT_TITLE": "projet",
		"CLIENT_NAME": "client",
		"AUTHOR": "author"
	}
}
```

Remarques : les clés sont le nom du placeholder (sans accolades). Dans le DOCX, placez les placeholders sous la forme `{{PROJECT_TITLE}}` (les doubles accolades sont attendues). IMPORTANT : Word peut segmenter le texte en plusieurs runs — pour que le remplacement fonctionne de façon fiable, veillez à ce que chaque placeholder soit contenu dans un seul run (écrire `{{PROJECT_TITLE}}` comme texte continu dans le document).

3) Créer le fichier JSON de données, par ex. `input.json` :
```
{
	"projet": "Nom du projet",
	"client": "ACME Corp",
	"author": "Arnaud"
}
```

4) Lancer la commande depuis la racine du repo :
```
node scripts/fill_master.js --skill av-cadrage-fonctionnel --master .agents/skills/av-cadrage-fonctionnel/masters/Cadrage_fonctionnel_template_MASTER.docx --data .agents/skills/av-cadrage-fonctionnel/input.json --name v1 --out .agents/skills/av-cadrage-fonctionnel/out
```

Le script fera une simple recherche/remplacement XML dans `word/document.xml`. S'il ne trouve pas `mappings.json`, il utilisera `mappings.example.json` comme référence. Si vous avez besoin d'une solution robuste (placeholders répartis sur plusieurs runs), je peux intégrer `docxtemplater` ensuite.
