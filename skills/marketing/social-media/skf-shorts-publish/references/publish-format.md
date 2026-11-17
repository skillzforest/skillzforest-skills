# Format de la publication — `shorts/<slug>/publish.json`

Chemins relatifs au dossier du short. Écrit par l'agent, vérifié par `publish.py validate`,
envoyé par `publish.py send` (Postiz) ou exporté par `publish.py kit` (envoi à la main).

```json
{
  "status": "draft",
  "when": { "type": "schedule", "date": "2026-11-20T17:00:00Z" },
  "targets": [
    {
      "platform": "youtube",
      "account": "@acme",
      "integrationId": "",
      "video": "out/short-9x16.mp4",
      "cover": "out/thumb-16x9.jpg",
      "title": "Tes devis en 30 secondes (sans recopier) #Shorts",
      "text": "Tu passes tes soirées sur tes devis ?\nAcme écrit le devis à partir de ta description, prêt à envoyer.\n\nEssaie-le : https://acme.app",
      "hashtags": ["#artisan", "#devis", "#productivité"],
      "settings": {}
    },
    {
      "platform": "tiktok",
      "video": "out/short-9x16.mp4",
      "text": "3 h de devis par semaine → 30 s 😮‍💨 Lien en bio",
      "hashtags": ["#artisan", "#entrepreneur", "#astuce"]
    },
    {
      "platform": "instagram",
      "video": "out/short-9x16.mp4",
      "cover": "out/cover-9x16.jpg",
      "text": "Tes devis en 30 secondes.\nTu décris le chantier, Acme chiffre, tu envoies.\n\n👉 Lien en bio",
      "hashtags": ["#artisan", "#devis", "#entrepreneur", "#gaindetemps"]
    },
    {
      "platform": "x",
      "video": "out/short-4x5.mp4",
      "text": "Un devis complet en 30 secondes, à partir d'une simple description.\n\nhttps://acme.app",
      "hashtags": []
    },
    {
      "platform": "bluesky",
      "video": "out/short-4x5.mp4",
      "text": "On a chronométré : 30 secondes pour un devis complet, prêt à envoyer. https://acme.app",
      "alt": "Démonstration : une description de chantier devient un devis chiffré en quelques secondes.",
      "hashtags": []
    }
  ]
}
```

| Champ | Contenu |
|---|---|
| `status` | `draft` → `approved` (accord explicite de l'utilisateur) → `published`, `scheduled`, `drafted` ou `partial` (posé par le script) |
| `when.type` | `now`, `schedule` (avec `date` ISO 8601 en UTC) ou `draft` (brouillon dans Postiz) |
| `targets[].date` | date propre à un réseau (étaler la diffusion) ; sinon `when.date` |
| `account` | compte visé quand plusieurs comptes du même réseau sont connectés |
| `integrationId` | canal Postiz (rempli par `publish.py bind --write`) |
| `video`, `cover` | fichiers de `out/` |
| `title` | YouTube : ≤ 100 caractères, ≈ 60 lisibles dans le fil, mot-clé en tête |
| `text` | légende (YouTube : description) ; les `hashtags` absents du texte sont ajoutés à la fin |
| `alt` | texte alternatif de la vidéo (Bluesky, et pour l'accessibilité partout) |
| `settings` | réglages Postiz propres au réseau ; `"@upload:out/thumb-16x9.jpg"` envoie le fichier et met sa référence (miniature, couverture) |
| `skip` | `true` pour garder la cible sans l'envoyer |

## Écrire chaque légende

La vidéo porte le message ; la légende **prolonge l'accroche** et dit quoi faire. Réécrire
pour chaque réseau, ne pas copier-coller.

| Réseau | Longueur | Ce qui marche |
|---|---|---|
| YouTube Shorts | titre ≤ 60 utiles ; description 2–4 lignes | titre = promesse + mot-clé recherché ; lien en description ; 3 hashtags ; `#Shorts` facultatif |
| TikTok | 1–2 lignes | accroche complémentaire, pas une redite ; « lien en bio » (les liens ne sont pas cliquables) ; 3–5 hashtags de niche + 1 large |
| Instagram Reels | 1re ligne = accroche (coupée après ~125 car.) | 2–4 lignes aérées ; « lien en bio » ; 3–5 hashtags précis en fin |
| X | ≤ 280 (URL = 23) | une phrase qui se suffit + lien ; 0–2 hashtags ; le 4:5 occupe mieux le fil |
| Bluesky | ≤ 300 | ton conversationnel, pas de jargon marketing ; lien seul en fin ; texte alternatif obligatoire |
| LinkedIn | 3–6 lignes | angle métier (le problème, le résultat) ; lien en fin ; 3 hashtags |

Règles : mêmes faits que la vidéo (rien d'ajouté) ; la langue et le tu/vous du kit ; pas plus
d'un emoji par ligne ; pas de hashtag inventé pour faire du volume — des mots que le public
cherche vraiment.

## Quand publier

Sans données propres au compte, ne pas promettre « la meilleure heure ». Proposer : en
semaine, en fin de journée du fuseau du public ; étaler les réseaux sur 1 à 3 jours plutôt
que tout à la même minute ; ne pas publier deux shorts le même jour sur le même compte.
Les statistiques de chaque réseau (Studio YouTube, TikTok Studio, Instagram) diront ensuite
mieux.
