Placez le master `Cadrage_plateforme_template_MASTER.docx` dans ce dossier.

Exemple minimal `mappings.json` pour DOCX :
```
{
	"placeholders": {
		"PROJECT_NAME": "projet",
		"PLATFORM": "plateforme"
	}
}
```

Commande de test :
```
node scripts/fill_master.js --skill presales-platform-scoping --master skills/development/code/presales-platform-scoping/masters/Cadrage_plateforme_template_MASTER.docx --data skills/development/code/presales-platform-scoping/input.json --name v1 --out skills/development/code/presales-platform-scoping/out
```

Voir remarques sur `masters/README.md` de `presales-functional-scoping` concernant les placeholders Word et les limites du remplacement XML simple.
