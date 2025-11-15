"""
Enhanced LLM Client with multiple provider support
Supports: Ollama, HuggingFace, Together.ai, Replicate, OpenAI-compatible APIs
"""

import json
import logging
import time
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    headers: Dict[str, str]
    supports_streaming: bool = False
    max_tokens_limit: int = 4096
    timeout: int = 30


class RetryableError(Exception):
    """Error that can be retried"""

    pass


class RateLimitError(Exception):
    """Rate limit exceeded"""

    pass


class EnhancedLLMClient:
    """Enhanced LLM client with multiple provider support and resilience"""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session = requests.Session()
        self.provider_configs = self._initialize_providers()
        self.current_provider = self._get_provider_config(cfg.provider)

        # Setup retry configuration
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_factor = 2.0

    def _initialize_providers(self) -> Dict[str, ProviderConfig]:
        """Initialize all supported provider configurations"""
        return {
            "ollama": ProviderConfig(
                name="Ollama",
                base_url="http://localhost:11434",
                headers={"Content-Type": "application/json"},
                supports_streaming=True,
                max_tokens_limit=4096,
                timeout=60,
            ),
            "huggingface": ProviderConfig(
                name="HuggingFace",
                base_url="https://api-inference.huggingface.co/models",
                headers={
                    "Authorization": f"Bearer {self.cfg.api_key}",
                    "Content-Type": "application/json",
                },
                supports_streaming=False,
                max_tokens_limit=2048,
                timeout=30,
            ),
            "together": ProviderConfig(
                name="Together.ai",
                base_url="https://api.together.xyz/v1",
                headers={
                    "Authorization": f"Bearer {self.cfg.api_key}",
                    "Content-Type": "application/json",
                },
                supports_streaming=True,
                max_tokens_limit=4096,
                timeout=45,
            ),
            "replicate": ProviderConfig(
                name="Replicate",
                base_url="https://api.replicate.com/v1",
                headers={
                    "Authorization": f"Bearer {self.cfg.api_key}",
                    "Content-Type": "application/json",
                },
                supports_streaming=False,
                max_tokens_limit=4096,
                timeout=60,
            ),
            "openai": ProviderConfig(
                name="OpenAI-compatible",
                base_url=self.cfg.api_endpoint or "https://api.openai.com/v1",
                headers={
                    "Authorization": f"Bearer {self.cfg.api_key}",
                    "Content-Type": "application/json",
                },
                supports_streaming=True,
                max_tokens_limit=4096,
                timeout=30,
            ),
        }

    def _get_provider_config(self, provider_name: str) -> ProviderConfig:
        """Get provider configuration by name"""
        provider = self.provider_configs.get(provider_name.lower())
        if not provider:
            logger.warning(f"Unknown provider {provider_name}, falling back to ollama")
            provider = self.provider_configs["ollama"]
        return provider

    def _make_request_with_retry(self, url: str, payload: Dict, headers: Dict) -> Dict:
        """Make HTTP request with retry logic"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.current_provider.timeout,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get("Retry-After", self.retry_delay)
                    )
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    raise RateLimitError(f"Rate limited: {response.text}")

                # Handle server errors
                if response.status_code >= 500:
                    raise RetryableError(f"Server error: {response.status_code}")

                response.raise_for_status()
                return response.json()

            except (requests.RequestException, RetryableError, RateLimitError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (self.backoff_factor**attempt)
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}), retrying in {delay}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All retries failed: {e}")

        raise last_error

    def chat(
        self, messages: List[Dict[str, str]], timeout: Optional[int] = None
    ) -> str:
        """Chat with LLM using current provider"""
        provider = self.current_provider
        timeout = timeout or provider.timeout

        try:
            if provider.name.lower() == "ollama":
                return self._chat_ollama(messages, timeout)
            elif provider.name.lower() == "huggingface":
                return self._chat_huggingface(messages, timeout)
            elif provider.name.lower() == "together":
                return self._chat_together(messages, timeout)
            elif provider.name.lower() == "replicate":
                return self._chat_replicate(messages, timeout)
            elif provider.name.lower() == "openai-compatible":
                return self._chat_openai(messages, timeout)
            else:
                raise ValueError(f"Unsupported provider: {provider.name}")

        except Exception as e:
            logger.error(f"LLM call failed with {provider.name}: {e}")
            return f"[LLM Error] {provider.name} unavailable: {str(e)}"

    def _chat_ollama(self, messages: List[Dict], timeout: int) -> str:
        """Chat with Ollama API"""
        url = f"{self.current_provider.base_url}/api/chat"
        payload = {
            "model": self.cfg.model_name,
            "messages": messages,
            "max_tokens": min(
                self.cfg.max_tokens, self.current_provider.max_tokens_limit
            ),
            "temperature": self.cfg.temperature,
            "stream": False,
        }

        try:
            data = self._make_request_with_retry(
                url, payload, self.current_provider.headers
            )
            return data.get("message", {}).get("content", "No response from Ollama")
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                return f"[Ollama Error] Model '{self.cfg.model_name}' not found. Available models: {self._list_ollama_models()}"
            raise

    def _chat_huggingface(self, messages: List[Dict], timeout: int) -> str:
        """Chat with HuggingFace API"""
        # Convert messages to single prompt for HF
        prompt = self._messages_to_prompt(messages)

        url = f"{self.current_provider.base_url}/{self.cfg.model_name}"
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": min(
                    self.cfg.max_tokens, self.current_provider.max_tokens_limit
                ),
                "temperature": self.cfg.temperature,
                "return_full_text": False,
            },
        }

        data = self._make_request_with_retry(
            url, payload, self.current_provider.headers
        )

        if isinstance(data, list) and len(data) > 0:
            return data[0].get("generated_text", "No response from HuggingFace")
        elif isinstance(data, dict):
            return data.get("generated_text", "No response from HuggingFace")
        else:
            return "Unexpected response format from HuggingFace"

    def _chat_together(self, messages: List[Dict], timeout: int) -> str:
        """Chat with Together.ai API"""
        url = f"{self.current_provider.base_url}/chat/completions"
        payload = {
            "model": self.cfg.model_name,
            "messages": messages,
            "max_tokens": min(
                self.cfg.max_tokens, self.current_provider.max_tokens_limit
            ),
            "temperature": self.cfg.temperature,
            "stream": False,
        }

        data = self._make_request_with_retry(
            url, payload, self.current_provider.headers
        )
        return data["choices"][0]["message"]["content"]

    def _chat_replicate(self, messages: List[Dict], timeout: int) -> str:
        """Chat with Replicate API"""
        prompt = self._messages_to_prompt(messages)

        url = f"{self.current_provider.base_url}/predictions"
        payload = {
            "version": self.cfg.model_name,
            "input": {
                "prompt": prompt,
                "max_new_tokens": min(
                    self.cfg.max_tokens, self.current_provider.max_tokens_limit
                ),
                "temperature": self.cfg.temperature,
            },
        }

        # Replicate uses async predictions, so we need to poll
        data = self._make_request_with_retry(
            url, payload, self.current_provider.headers
        )
        prediction_url = data["urls"]["get"]

        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            response = self.session.get(
                prediction_url, headers=self.current_provider.headers
            )
            response.raise_for_status()
            result = response.json()

            if result["status"] == "succeeded":
                return "".join(result["output"])
            elif result["status"] == "failed":
                raise Exception(f"Replicate prediction failed: {result['error']}")

            time.sleep(1)

        raise TimeoutError("Replicate prediction timed out")

    def _chat_openai(self, messages: List[Dict], timeout: int) -> str:
        """Chat with OpenAI-compatible API"""
        url = f"{self.current_provider.base_url}/chat/completions"
        payload = {
            "model": self.cfg.model_name,
            "messages": messages,
            "max_tokens": min(
                self.cfg.max_tokens, self.current_provider.max_tokens_limit
            ),
            "temperature": self.cfg.temperature,
            "stream": False,
        }

        data = self._make_request_with_retry(
            url, payload, self.current_provider.headers
        )
        return data["choices"][0]["message"]["content"]

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert message list to single prompt for non-chat APIs"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"Human: {content}")

        return "\n\n".join(prompt_parts) + "\n\nAssistant: "

    def _list_ollama_models(self) -> str:
        """List available Ollama models"""
        try:
            response = self.session.get(
                f"{self.current_provider.base_url}/api/tags", timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                return ", ".join([model["name"] for model in models])
        except:
            pass
        return "Unable to fetch models"

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to current provider"""
        try:
            start_time = time.time()
            response = self.chat([{"role": "user", "content": "Hello"}], timeout=10)
            response_time = time.time() - start_time

            return {
                "success": True,
                "provider": self.current_provider.name,
                "model": self.cfg.model_name,
                "response_time": response_time,
                "response_preview": response[:100] + "..."
                if len(response) > 100
                else response,
            }
        except Exception as e:
            return {
                "success": False,
                "provider": self.current_provider.name,
                "model": self.cfg.model_name,
                "error": str(e),
            }

    def switch_provider(self, provider_name: str) -> bool:
        """Switch to a different provider"""
        if provider_name.lower() in self.provider_configs:
            self.current_provider = self._get_provider_config(provider_name)
            self.cfg.provider = provider_name.lower()
            logger.info(f"Switched to provider: {provider_name}")
            return True
        return False
