"""Client API minimal pour LM Studio."""

import requests
from core.config import LM_STUDIO_URL, DEFAULT_MODEL, TEMPERATURE, MAX_TOKENS, REQUEST_TIMEOUT


class LMStudioClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.base_url = LM_STUDIO_URL
        self.url = f"{LM_STUDIO_URL}/chat/completions"

    def check_connection(self) -> dict:
        """Vérifie la connexion à LM Studio et retourne les infos du serveur."""
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("data", [])
            loaded = models[0] if models else None
            return {
                "connected": True,
                "models": [m.get("id", "?") for m in models],
                "loaded_model": loaded.get("id", "?") if loaded else None
            }
        except requests.RequestException as e:
            return {"connected": False, "error": str(e), "models": [], "loaded_model": None}
        
    def chat(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        resp = requests.post(
            self.url,
            json={
                "model": self.model,
                "messages": messages,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS
            },
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]