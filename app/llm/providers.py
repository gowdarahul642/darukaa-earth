import logging
from abc import ABC, abstractmethod
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        pass


class MockLLMProvider(BaseLLMProvider):
    """Fallback provider used when local GPU/Ollama is offline or timing out."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        prompt_lower = prompt.lower()

        # 1. Report Synthesis Prompts
        if "synthesize a complete ecological report" in prompt_lower:
            return (
                "## Environmental Assessment\n"
                "The site demonstrates multi-metric degradation pressures driven by soil organic carbon depletion, "
                "moisture stress, and monoculture cropping.\n\n"
                "## Key Interactions\n"
                "* **SOC & Moisture Stress:** Low soil organic carbon impairs water retention capacity.\n"
                "* **Monoculture & Soil Biota:** Continuous monoculture suppresses microbial activity.\n\n"
                "## Recommended Actions\n"
                "1. **Legume Cover Crops:** Rebuilds soil aggregate structure and microbial biomes.\n"
                "2. **Native Flowering Strips:** Diversifies micro-habitats and boosts native pollinators.\n"
            )

        # 2. General Query Fallbacks
        return (
            f"**[Ollama Offline]** Unable to reach local model engine.\n\n"
            f"**Query Received:** *\"{prompt}\"*\n\n"
            "*(Ensure Ollama is running at http://127.0.0.1:11434)*"
        )


class OllamaProvider(BaseLLMProvider):
    """Robust Ollama provider with strict IPv4 routing and model retention."""

    def __init__(self, model_name: str = None, base_url: str = None):
        raw_model = model_name or getattr(settings, "llm_model_name", "gemma:2b")
        raw_url = base_url or getattr(settings, "llm_base_url", "http://127.0.0.1:11434")

        self.model_name = raw_model
        # Force IPv4 127.0.0.1 to avoid Windows IPv6 localhost resolution failures
        self.base_url = raw_url.replace("localhost", "127.0.0.1")
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "keep_alive": "1h",  # Instructs Ollama to keep gemma:2b in RAM/VRAM
            "options": {
                "temperature": 0.2,
                "num_predict": 350,  # Optimized token cap for faster CPU inference
            },
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                return res.json().get("response", "")
        except httpx.ReadTimeout:
            print(f"\n⚠️ [OLLAMA TIMEOUT]: Call to {url} timed out after 120s.\n")
            return MockLLMProvider().generate(prompt, system_prompt)
        except Exception as e:
            print(f"\n❌ [OLLAMA ERROR]: Connection to {url} failed: {e}\n")
            return MockLLMProvider().generate(prompt, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory getter for active LLM provider."""
    provider_type = getattr(settings, "llm_provider", "ollama").lower()
    if provider_type == "ollama":
        return OllamaProvider()
    return MockLLMProvider()