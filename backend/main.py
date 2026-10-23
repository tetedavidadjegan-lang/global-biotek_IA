"""Point d'entrée FastAPI du Conseiller IA Médical Global Biotek."""
import os
import sqlite3
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from passlib.exc import UnknownHashError

from backend.security import hash_password, verify_password, create_access_token, read_access_token
from backend.ai_service import answer_question

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend" / "index.html"
DB_PATH = Path(os.getenv("DATABASE_PATH", "data/global_biotek.db"))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT / DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=os.getenv("APP_NAME", "Conseiller IA Médical Global Biotek"),
              version="1.0.0",
              description="API de démonstration du conseiller d'information générale en santé.")

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content TEXT NOT NULL,
            thematique TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS thematiques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            description TEXT,
            icone TEXT DEFAULT '🏥',
            is_default INTEGER NOT NULL DEFAULT 1
        )""")
        # Insérer les thématiques par défaut si elles n'existent pas
        themes_defaut = [
            ("Médecine générale", "Questions générales de santé et symptômes courants", "🩺"),
            ("Nutrition & Alimentation", "Conseils nutritionnels, régimes, vitamines et minéraux", "🥗"),
            ("Santé mentale", "Bien-être psychologique, stress, anxiété et sommeil", "🧠"),
            ("Maladies chroniques", "Diabète, hypertension, maladies cardiovasculaires", "❤️‍🩹"),
            ("Pédiatrie", "Santé des nourrissons et des enfants", "👶"),
            ("Grossesse & Maternité", "Suivi de grossesse, accouchement et post-partum", "🤰"),
            ("Médicaments", "Informations générales sur les médicaments et traitements", "💊"),
            ("Urgences & Premiers secours", "Que faire en cas d'urgence médicale", "🚑"),
            ("Dermatologie", "Problèmes de peau, allergies cutanées, soins", "🧴"),
            ("Sport & Activité physique", "Bienfaits du sport, blessures sportives et rééducation", "🏃"),
        ]
        for (nom, desc, icone) in themes_defaut:
            conn.execute(
                "INSERT OR IGNORE INTO thematiques(nom, description, icone, is_default) VALUES(?,?,?,1)",
                (nom, desc, icone)
            )

init_db()

class RegisterIn(BaseModel):
    nom: str = Field(min_length=2, max_length=80)
    telephone: str = Field(min_length=6, max_length=24)
    mot_de_passe: str = Field(min_length=8, max_length=128)

class LoginIn(BaseModel):
    telephone: str = Field(min_length=6, max_length=24)
    mot_de_passe: str = Field(min_length=8, max_length=128)

class ChatIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    thematique: str | None = Field(default=None, max_length=120)

class ThematiqueIn(BaseModel):
    nom: str = Field(min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=300)
    icone: str | None = Field(default="📋", max_length=10)

def current_user(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Connectez-vous pour continuer.")
    user_id = read_access_token(authorization.split(" ", 1)[1].strip())
    if not user_id:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée.")
    with connect_db() as conn:
        user = conn.execute("SELECT id, nom, telephone FROM users WHERE id=?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Compte introuvable.")
    return dict(user)

@app.get("/")
def home():
    """Affiche l'interface web."""
    if not FRONTEND.exists():
        raise HTTPException(status_code=404, detail="Interface frontend introuvable.")
    return FileResponse(FRONTEND)

@app.get("/api/health")
def health():
    """Vérifie simplement que le serveur fonctionne."""
    return {"ok": True, "app": app.title}

@app.post("/api/auth/inscription", status_code=201)
def register(data: RegisterIn):
    nom = data.nom.strip()
    telephone = "".join(data.telephone.split())
    if not nom or not telephone:
        raise HTTPException(status_code=422, detail="Nom et téléphone obligatoires.")
    with connect_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE telephone=?", (telephone,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Ce numéro est déjà inscrit.")
        cursor = conn.execute(
            "INSERT INTO users(nom, telephone, password_hash) VALUES(?,?,?)",
            (nom, telephone, hash_password(data.mot_de_passe))
        )
        user_id = str(cursor.lastrowid)
    return {"message": "Compte créé avec succès.", "access_token": create_access_token(user_id), "token_type": "bearer"}

@app.post("/api/auth/connexion")
def login(data: LoginIn):
    telephone = "".join(data.telephone.split())
    with connect_db() as conn:
        user = conn.execute("SELECT id, password_hash FROM users WHERE telephone=?", (telephone,)).fetchone()
    if not user or not verify_password(data.mot_de_passe, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Téléphone ou mot de passe incorrect.")
    return {"message": "Connexion réussie.", "access_token": create_access_token(str(user["id"])), "token_type": "bearer"}

@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return {"id": user["id"], "nom": user["nom"], "telephone": user["telephone"]}

@app.get("/api/thematiques")
def list_thematiques():
    """Retourne la liste de toutes les thématiques disponibles."""
    with connect_db() as conn:
        rows = conn.execute("SELECT id, nom, description, icone, is_default FROM thematiques ORDER BY id").fetchall()
    return {"thematiques": [dict(row) for row in rows]}

@app.post("/api/thematiques", status_code=201)
def add_thematique(data: ThematiqueIn, user=Depends(current_user)):
    """Ajoute une thématique personnalisée."""
    nom = data.nom.strip()
    if not nom:
        raise HTTPException(status_code=422, detail="Le nom est obligatoire.")
    with connect_db() as conn:
        existing = conn.execute("SELECT id FROM thematiques WHERE nom=?", (nom,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail="Cette thématique existe déjà.")
        cursor = conn.execute(
            "INSERT INTO thematiques(nom, description, icone, is_default) VALUES(?,?,?,0)",
            (nom, data.description or "", data.icone or "📋")
        )
    return {"message": "Thématique ajoutée.", "id": cursor.lastrowid}

@app.get("/api/chat/historique")
def history(user=Depends(current_user)):
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT role, content, thematique, created_at FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 30",
            (user["id"],)
        ).fetchall()
    return {"messages": [dict(row) for row in reversed(rows)]}

@app.post("/api/chat")
async def chat(data: ChatIn, user=Depends(current_user)):
    question = data.question.strip()
    thematique = (data.thematique or "").strip() or None
    if not question:
        raise HTTPException(status_code=422, detail="Écrivez une question.")
    with connect_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 8",
            (user["id"],)
        ).fetchall()
    history_items = [dict(row) for row in reversed(rows)]
    # Enregistrer la question puis la réponse pour conserver le fil de conversation.
    with connect_db() as conn:
        conn.execute("INSERT INTO messages(user_id, role, content, thematique) VALUES(?,?,?,?)",
                     (user["id"], "user", question, thematique))
    answer = await answer_question(question, history_items, thematique=thematique)
    with connect_db() as conn:
        conn.execute("INSERT INTO messages(user_id, role, content, thematique) VALUES(?,?,?,?)",
                     (user["id"], "assistant", answer, thematique))
    return {"answer": answer, "thematique": thematique}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
