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
node scripts/fill_master.js --skill av-cadrage-plateforme --master skills/sales/av-cadrage-plateforme/masters/Cadrage_plateforme_template_MASTER.docx --data skills/sales/av-cadrage-plateforme/input.json --name v1 --out skills/sales/av-cadrage-plateforme/out
```

Voir remarques sur `masters/README.md` de `av-cadrage-fonctionnel` concernant les placeholders Word et les limites du remplacement XML simple.
