"""Adaptateur d'IA : appelle une API compatible OpenAI si elle est configurée."""
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """Tu es le Conseiller IA Médical Global Biotek, un assistant d'information générale
sur la santé qui répond en français clair, avec empathie et sans jugement.
Réponds directement aux questions générales et explique les termes difficiles.
Tu n'es pas médecin et ne poses pas de diagnostic certain. Ne prescris pas de médicaments,
ne propose pas de dosage personnalisé et ne conseille pas d'arrêter un traitement.
Pour les symptômes potentiellement graves (douleur thoracique, difficulté à respirer,
perte de connaissance, signes d'AVC, saignement important, réaction allergique sévère,
idées suicidaires ou urgence similaire), recommande immédiatement les services d'urgence
locaux ou le centre de santé le plus proche.
Précise quand les informations sont incertaines et encourage un professionnel de santé
pour les symptômes persistants, l'enfant, la grossesse ou les maladies chroniques.
Ne prétends pas avoir consulté un dossier médical ou une source en temps réel.
Ne demande pas de données personnelles identifiantes.
"""

async def answer_question(question: str, history: list[dict] | None = None, thematique: str | None = None) -> str:
    """Génère une réponse via l'API configurée ; mode démo explicite sinon."""
    api_key = os.getenv("AI_API_KEY", "").strip()
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "").strip()
    timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "45"))

    if not api_key or not model:
        return (
            "Le mode démonstration est actif : aucune clé d'IA n'est configurée, "
            "donc je ne peux pas générer une réponse complète pour le moment. "
            "Configurez AI_API_KEY et AI_MODEL dans le fichier .env, puis redémarrez le serveur. "
            "Pour une question médicale urgente, contactez immédiatement les services d'urgence "
            "locaux ou le centre de santé le plus proche."
        )

    system_content = SYSTEM_PROMPT
    if thematique:
        system_content += f"\n\nL'utilisateur a choisi la thématique : **{thematique}**. Concentre tes réponses sur ce domaine en priorité."
    messages = [{"role": "system", "content": system_content}]
    for item in (history or [])[-8:]:
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            messages.append({"role": role, "content": content[:4000]})
    messages.append({"role": "user", "content": question[:4000]})

    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.4}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        answer = data["choices"][0]["message"]["content"]
        if isinstance(answer, str) and answer.strip():
            return answer.strip()
        return "Le fournisseur d'IA a renvoyé une réponse vide. Réessayez dans un instant."
    except httpx.TimeoutException:
        return "Le service d'IA met trop de temps à répondre. Réessayez dans un instant."
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return (
            "Je n'arrive pas à joindre correctement le service d'IA. Vérifiez AI_BASE_URL, "
            "AI_API_KEY et AI_MODEL dans .env, puis consultez les journaux du serveur."
        )
