"""Fonctions de sécurité : mots de passe et jetons d'accès."""
import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-before-deployment")
ALGORITHM = "HS256"
TOKEN_MINUTES = 60 * 24
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Ne jamais enregistrer le mot de passe en clair."""
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Compare un mot de passe saisi à son empreinte enregistrée."""
    return pwd_context.verify(password, password_hash)

def create_access_token(subject: str) -> str:
    """Crée un jeton signé avec une durée de validité limitée."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode({"sub": subject, "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)

def read_access_token(token: str) -> str | None:
    """Retourne l'identifiant du compte si le jeton est valide."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except JWTError:
        return None
