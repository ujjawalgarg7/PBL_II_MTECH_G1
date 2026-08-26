import json
import urllib.error
import urllib.request


class OllamaClient:
    """Client for communicating with a local Ollama server."""

    def __init__(
        self,
        model="qwen2.5-coder:3b",
        host="http://localhost:11434",
    ):
        self.model = model
        self.host = host.rstrip("/")

    def generate(self, prompt):
        """Send a prompt to Ollama and return its response."""

        url = f"{self.host}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        data = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=120,
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

                return result.get("response", "")

        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not connect to Ollama. "
                "Make sure Ollama is running."
            ) from exc