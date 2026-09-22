Placez le master `architecture-logique.json` dans ce dossier.

Exemple `mappings.json` pour JSON masters :
```
{
	"topology_key": "value",
	"notes": "Map top-level keys or provide a transform script"
}
```

Commande (copie simple ou transformation personnalisée) :
```
node scripts/fill_master.js --skill av-schema-logique --master skills/sales/av-schema-logique/masters/architecture-logique.json --data skills/sales/av-schema-logique/input.json --name v1 --out skills/sales/av-schema-logique/out
```

Pour des transformations JSON complexes (fusion, tableaux, génération d'excalidraw), créez un petit script Node dans `scripts/` du skill. Je peux en générer un exemple si besoin.
