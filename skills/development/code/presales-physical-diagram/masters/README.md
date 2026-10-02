Placez le master `architecture_physique.json` dans ce dossier.

Exemple `mappings.json` :
```
{
	"topology_key": "value"
}
```

Commande de test :
```
node scripts/fill_master.js --skill presales-physical-diagram --master skills/development/code/presales-physical-diagram/masters/architecture_physique.json --data skills/development/code/presales-physical-diagram/input.json --name v1 --out skills/development/code/presales-physical-diagram/out
```

Pour générer un fichier `.excalidraw` adapté, je peux fournir un script de transformation JSON→Excalidraw.
