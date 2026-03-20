from __future__ import annotations

import json
from typing import Any

import requests

from app.core.errors import DependencyUnavailableError, UpstreamRequestError


class LlmClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: int = 120,
        provider: str = "ollama",
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.provider = provider
        self.api_key = api_key

    def generate_json(self, prompt: str) -> dict[str, Any]:
        if self.provider == "groq":
            return self._generate_json_groq(prompt)
        return self._generate_json_ollama(prompt)

    def _generate_json_ollama(self, prompt: str) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            raw = payload.get("response", "{}")
            return requests.models.complexjson.loads(raw)
        except requests.exceptions.ConnectionError as exc:
            raise DependencyUnavailableError(
                message="LLM local inaccessible",
                status_code=503,
                details={
                    "service": "llm",
                    "base_url": self.base_url,
                    "model": self.model,
                    "hint": "Verifier que le serveur LLM est demarre et que LLM_BASE_URL est correct.",
                },
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise DependencyUnavailableError(
                message="LLM local indisponible ou trop lent",
                status_code=504,
                details={
                    "service": "llm",
                    "base_url": self.base_url,
                    "model": self.model,
                    "hint": "Augmenter LLM_TIMEOUT_SECONDS ou verifier la charge du serveur LLM.",
                },
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else 502
            details = {
                "service": "llm",
                "upstream_status": status_code,
                "base_url": self.base_url,
                "model": self.model,
            }
            if status_code == 404:
                response_text = exc.response.text[:300] if exc.response is not None else ""
                details["upstream_body"] = response_text
                details["hint"] = (
                    "Sur Ollama, un 404 signifie souvent que le modele n'est pas installe. "
                    "Verifier `curl http://localhost:11434/api/tags` et installer le modele configure."
                )
            raise UpstreamRequestError(
                message="Le serveur LLM a repondu avec une erreur",
                status_code=502,
                details=details,
            ) from exc
        except ValueError as exc:
            raise UpstreamRequestError(
                message="Le serveur LLM a renvoye une reponse JSON invalide",
                status_code=502,
                details={
                    "service": "llm",
                    "base_url": self.base_url,
                    "model": self.model,
                    "hint": "Verifier que le modele renvoie bien un JSON strict.",
                },
            ) from exc

    def _generate_json_groq(self, prompt: str) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Return valid JSON only. Do not wrap the JSON in markdown or any extra text.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.2,
                    "stream": False,
                    "response_format": {"type": "json_object"},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            content = (((payload.get("choices") or [{}])[0]).get("message") or {}).get("content", "{}")
            return _parse_json_content(content)
        except requests.exceptions.ConnectionError as exc:
            raise DependencyUnavailableError(
                message="Groq inaccessible",
                status_code=503,
                details={
                    "service": "groq",
                    "base_url": self.base_url,
                    "model": self.model,
                    "hint": "Verifier la connectivite reseau et GROQ_BASE_URL.",
                },
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise DependencyUnavailableError(
                message="Groq ne repond pas a temps",
                status_code=504,
                details={
                    "service": "groq",
                    "base_url": self.base_url,
                    "model": self.model,
                    "hint": "Augmenter LLM_TIMEOUT_SECONDS ou verifier l'etat de l'API Groq.",
                },
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else 502
            response_text = exc.response.text[:300] if exc.response is not None else ""
            details = {
                "service": "groq",
                "upstream_status": status_code,
                "base_url": self.base_url,
                "model": self.model,
                "upstream_body": response_text,
            }
            if status_code == 401:
                details["hint"] = "Verifier GROQ_API_KEY."
            elif status_code == 404:
                details["hint"] = "Verifier GROQ_BASE_URL et le modele configure."
            elif status_code == 429:
                details["hint"] = "Limite Groq atteinte. Reessayer plus tard ou changer de modele."
            raise UpstreamRequestError(
                message="Groq a repondu avec une erreur",
                status_code=502,
                details=details,
            ) from exc
        except ValueError as exc:
            raise UpstreamRequestError(
                message="Groq a renvoye une reponse JSON invalide",
                status_code=502,
                details={
                    "service": "groq",
                    "base_url": self.base_url,
                    "model": self.model,
                    "hint": "Verifier que le prompt force bien un JSON strict et que le modele choisi est adapte.",
                },
            ) from exc


def _parse_json_content(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3:
            stripped = "\n".join(lines[1:-1]).strip()
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = stripped[start : end + 1]
        return json.loads(candidate)

    raise ValueError("No valid JSON object found in model response")
