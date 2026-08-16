Placez le master `architecture_physique.json` dans ce dossier.

Exemple `mappings.json` :
```
{
	"topology_key": "value"
}
```

Commande de test :
```
node scripts/fill_master.js --skill av-schema-physique --master .agents/skills/av-schema-physique/masters/architecture_physique.json --data .agents/skills/av-schema-physique/input.json --name v1 --out .agents/skills/av-schema-physique/out
```

Pour générer un fichier `.excalidraw` adapté, je peux fournir un script de transformation JSON→Excalidraw.
