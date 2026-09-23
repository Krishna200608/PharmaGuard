"""
LLM Factory — Multi-provider abstraction supporting Google Gemini and local Ollama.

Centralizes LLM instantiation for PharmaGuard, enabling zero-code-change switching
between Google Cloud API (Gemini) and local offline inference via Ollama.

Owner: Krishna Sikheriya (IIT2023139)
"""

import logging
import os
from typing import Optional, Any
import requests
from langchain_core.language_models.chat_models import BaseChatModel

from pharmaguard.utils.config_loader import AppConfig, load_config

logger = logging.getLogger(__name__)


def check_ollama_status(base_url: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    """
    Diagnostic helper to check if Ollama daemon is reachable and query loaded models.
    Returns:
        (is_online, list_of_model_names)
    """
    clean_url = base_url.rstrip("/")
    try:
        resp = requests.get(f"{clean_url}/api/tags", timeout=3.0)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            return True, models
        return False, []
    except Exception as exc:
        logger.debug("Ollama connectivity check failed at %s: %s", clean_url, exc)
        return False, []


def get_llm(
    config: Optional[AppConfig] = None,
    temperature: Optional[float] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseChatModel:
    """
    Factory function returning an instantiated LangChain ChatModel.

    Args:
        config: Optional AppConfig. If omitted, loads via load_config().
        temperature: Override temperature. Defaults to config setting (or 0.0).
        provider: Override provider ('google', 'gemini', 'ollama').
        model: Override model name.

    Returns:
        BaseChatModel: ChatGoogleGenerativeAI or ChatOllama instance.
    """
    if config is None:
        config = load_config()

    target_provider = (provider or getattr(config.agent, "llm_provider", "google")).lower().strip()
    temp = temperature if temperature is not None else getattr(config.agent, "temperature", 0.0)

    if target_provider in ("google", "gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        target_model = model or getattr(config.agent, "llm_model", "gemini-3.1-flash-lite")
        logger.info(
            "Instantiating Google Gemini LLM | model=%s | temperature=%.2f",
            target_model,
            temp,
        )
        return ChatGoogleGenerativeAI(model=target_model, temperature=temp)

    elif target_provider == "ollama":
        from langchain_ollama import ChatOllama

        base_url = getattr(config.agent, "ollama_base_url", "http://localhost:11434")
        target_model = model or getattr(config.agent, "ollama_model", "qwen2.5:7b")

        # Proactive connectivity check
        is_online, available_models = check_ollama_status(base_url)
        if not is_online:
            logger.warning(
                "Ollama daemon appears unreachable at %s. Ensure 'ollama serve' is running.",
                base_url,
            )
        elif available_models:
            # Check if requested model is in available models
            model_base = target_model.split(":")[0]
            matches = [m for m in available_models if m == target_model or m.startswith(f"{model_base}:")]
            if not matches:
                logger.warning(
                    "Model '%s' not found in loaded Ollama models: %s. Run 'ollama pull %s'.",
                    target_model,
                    available_models,
                    target_model,
                )

        logger.info(
            "Instantiating local Ollama LLM | model=%s | base_url=%s | temperature=%.2f",
            target_model,
            base_url,
            temp,
        )
        return ChatOllama(
            model=target_model,
            base_url=base_url,
            temperature=temp,
        )

    else:
        raise ValueError(
            f"Unsupported llm_provider '{target_provider}'. Valid options: 'google', 'gemini', 'ollama'."
        )
