"""
Unit tests for pharmaguard.utils.llm_factory and multi-provider support.
"""

import copy
import os
import pytest
from unittest.mock import patch, MagicMock

from pharmaguard.utils.config_loader import load_config
from pharmaguard.utils.llm_factory import get_llm, check_ollama_status
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama


@pytest.fixture(autouse=True)
def ensure_api_keys(monkeypatch):
    """Ensure dummy API keys exist so ChatGoogleGenerativeAI can instantiate in CI/test environments."""
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        monkeypatch.setenv("GOOGLE_API_KEY", "dummy_test_api_key_for_testing")


@pytest.fixture
def base_config():
    """Load base config fresh."""
    return load_config(reload=True)


class TestLLMFactory:
    """Test get_llm instantiation for Google and Ollama providers."""

    def test_default_provider_returns_chat_google(self, base_config):
        cfg = copy.deepcopy(base_config)
        cfg.agent.llm_provider = "google"
        cfg.agent.llm_model = "gemini-3.1-flash-lite"
        llm = get_llm(cfg)
        assert isinstance(llm, ChatGoogleGenerativeAI)
        assert llm.model == "gemini-3.1-flash-lite"
        assert llm.temperature == 0.0

    def test_ollama_provider_returns_chat_ollama(self, base_config):
        cfg = copy.deepcopy(base_config)
        cfg.agent.llm_provider = "ollama"
        cfg.agent.ollama_model = "qwen2.5:7b"
        llm = get_llm(cfg)
        assert isinstance(llm, ChatOllama)
        assert llm.model == "qwen2.5:7b"
        assert llm.base_url == "http://localhost:11434"
        assert llm.temperature == 0.0

    def test_explicit_provider_override(self, base_config):
        # Config says google, but caller explicitly requests ollama
        cfg = copy.deepcopy(base_config)
        cfg.agent.llm_provider = "google"
        llm = get_llm(cfg, provider="ollama", model="llama3.1:8b", temperature=0.2)
        assert isinstance(llm, ChatOllama)
        assert llm.model == "llama3.1:8b"
        assert llm.temperature == 0.2

    def test_unsupported_provider_raises(self, base_config):
        cfg = copy.deepcopy(base_config)
        cfg.agent.llm_provider = "openai"
        with pytest.raises(ValueError, match="Unsupported llm_provider 'openai'"):
            get_llm(cfg)

    def test_check_ollama_status_success(self):
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "models": [{"name": "qwen2.5:7b"}, {"name": "llama3.2:3b"}]
            }
            mock_get.return_value = mock_resp

            is_running, models = check_ollama_status("http://localhost:11434")
            assert is_running is True
            assert "qwen2.5:7b" in models
            assert "llama3.2:3b" in models

    def test_check_ollama_status_offline(self):
        with patch("requests.get", side_effect=Exception("Connection refused")):
            is_running, models = check_ollama_status("http://localhost:11434")
            assert is_running is False
            assert models == []
