# Conseiller IA Médical Global Biotek

Application web de démonstration avec :
- interface de discussion en français ;
- API FastAPI ;
- inscription et connexion ;
- stockage SQLite des comptes et des conversations ;
- connexion facultative à une API d'IA compatible OpenAI ;
- réponses de secours si aucune clé IA n'est configurée.

## Important
Cette application ne remplace pas un médecin. L'IA peut se tromper et ne doit pas servir à diagnostiquer une urgence, prescrire un traitement ou modifier un médicament. En cas d'urgence, contactez les services d'urgence locaux ou rendez-vous dans un centre de santé. Ne saisissez pas de données médicales permettant d'identifier une personne.

Sans clé API valide, le serveur utilise un mode de démonstration limité : il ne peut pas fournir de vraies réponses générées par un modèle d'IA. Pour obtenir des réponses générées, configurez `AI_API_KEY` et `AI_MODEL` dans `.env`.

## 1. Installation sous Windows
Installez Python 3.11 ou plus récent, puis ouvrez PowerShell dans ce dossier :

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Ouvrez `.env` et renseignez `AI_API_KEY`, `AI_BASE_URL` et `AI_MODEL` selon le fournisseur d'IA choisi. Gardez la clé secrète : ne la mettez jamais dans le code du navigateur et ne la publiez pas sur GitHub.

## 2. Démarrer
```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Puis ouvrez http://127.0.0.1:8000

Documentation de l'API : http://127.0.0.1:8000/docs

## 3. Tester
- Créez un compte avec un nom, téléphone et mot de passe.
- Connectez-vous.
- Posez une question dans le chat.
- Vérifiez la documentation `/docs` si un endpoint ne fonctionne pas.

## Structure et explication des fichiers
- `backend/main.py` : API, pages web, inscription, connexion, chat et gestion de base de données.
- `backend/ai_service.py` : appel au fournisseur d'IA et mode de secours.
- `backend/security.py` : hachage des mots de passe et jetons d'accès.
- `frontend/index.html` : interface du chat et formulaires.
- `requirements.txt` : bibliothèques Python nécessaires.
- `.env.example` : exemple de configuration sans secrets.
- `data/` : la base SQLite sera créée automatiquement au démarrage.
- `tests/test_security.py` : test simple du hachage de mot de passe.

## Limites et mise en production
Le projet est un socle de départ, pas un système médical certifié. Avant une mise en production : HTTPS, politique de confidentialité, validation juridique locale, limitation de débit, gestion des comptes et des sessions renforcée, sauvegardes, surveillance, tests de sécurité et validation clinique par des professionnels. Ne publiez pas la base SQLite contenant les comptes.
