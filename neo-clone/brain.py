"""
brain.py - Central reasoning engine (Neo-like) and LLM integration.

Implements:
- Single LLM client per process (provider abstraction via config)
- Conversation context/history (last N turns)
- Intent parser (keyword-based, extensible)
- Skill router (map intent to skill from registry)
- Structured response (explanation + skill output)
- Error handling/logging
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from config import Config, load_config
from skills import SkillRegistry
import requests

logger = logging.getLogger(__name__)

@dataclass
class Message:
    role: str
    content: str

class ConversationHistory:
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._messages: List[Message] = []

    def add(self, role: str, content: str):
        self._messages.append(Message(role=role, content=content))
        # Limit the history size
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages:]

    def to_list(self) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self._messages]

    def clear(self):
        self._messages = []

class LLMClient:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.session = requests.Session()

    def chat(self, messages: List[Dict[str, str]], timeout: int = 15) -> str:
        provider = self.cfg.provider.lower()
        if provider == "ollama":
            # Ollama local API: POST /api/chat
            url = self.cfg.api_endpoint.rstrip("/") + "/api/chat"
            payload = {
                "model": self.cfg.model_name,
                "messages": messages,
                "max_tokens": self.cfg.max_tokens,
                "temperature": self.cfg.temperature,
            }
            try:
                resp = self.session.post(url, json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "No response.")
            except Exception as e:
                logger.error(f"Ollama call failed: {e}")
                return "[Neo Error] LLM unavailable: " + str(e)
        # Add more providers here (Together.ai, HF) if needed
        return "[Neo Error] Provider not supported or missing integration."

class Brain:
    def __init__(self, config: Config, skills: SkillRegistry, llm_client: Optional[LLMClient]=None):
        self.cfg = config
        self.skills = skills
        self.llm = llm_client or LLMClient(config)
        self.history = ConversationHistory(max_messages=20)

    def parse_intent(self, text: str) -> Dict[str, str]:
        lowered = text.lower()
        # Simple keyword matching for skill routing
        if any(word in lowered for word in ["train", "model", "simulate", "recommend"]):
            return {"intent": "skill", "skill": "ml_training"}
        if any(word in lowered for word in ["sentiment", "analyze", "moderate", "toxic"]):
            return {"intent": "skill", "skill": "text_analysis"}
        if any(word in lowered for word in ["csv", "json", "data", "summary", "stats"]):
            return {"intent": "skill", "skill": "data_inspector"}
        if any(word in lowered for word in ["code", "python", "generate", "snippet", "explain"]):
            return {"intent": "skill", "skill": "code_generation"}
        return {"intent": "chat"}

    def route_to_skill(self, skill_name: str, text: str) -> Dict:
        try:
            skill = self.skills.get(skill_name)
            # Format params
            params = {"text": text}
            result = skill.execute(params)
            return {
                "chosen_skill": skill_name,
                "meta": {
                    "description": skill.description,
                    "example": skill.example_usage,
                },
                "output": result,
                "reasoning": f"Chose skill '{skill_name}' due to detected keywords."
            }
        except Exception as e:
            logger.error(f"Skill routing failed: {e}")
            return {"error": f"Skill routing failed: {e}"}

    def send_message(self, text: str) -> str:
        self.history.add("user", text)
        intent = self.parse_intent(text)
        if intent["intent"] == "skill" and intent.get("skill"):
            skill_name = intent["skill"]
            result = self.route_to_skill(skill_name, text)
            self.history.add("assistant", f"[Skill:{skill_name}] {result}")
            return f"[Neo Reasoning] {result['reasoning']}\n[Skill Output]\n{result['output']}"
        # Otherwise, chat via LLM
        llm_response = self.llm.chat(self.history.to_list())
        self.history.add("assistant", llm_response)
        return llm_response

    def clear_history(self):
        self.history.clear()