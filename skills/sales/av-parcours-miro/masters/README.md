Placez le master `User story mapping - Template.jpg` dans ce dossier.

Si vous utilisez une image comme master, le script copiera simplement le fichier :
```
node scripts/fill_master.js --skill av-parcours-miro --master skills/sales/av-parcours-miro/masters/"User story mapping - Template.jpg" --name v1 --out skills/sales/av-parcours-miro/out
```

Pour la génération Miro automatisée (duplication de board), ce repo ne gère pas l'API Miro automatiquement — il faudra provisionner des clés et appeler l'API Miro. Dites-moi si vous voulez que je génère le flux de duplication Miro/board.
