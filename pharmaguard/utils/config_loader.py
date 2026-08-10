"""
Config Loader - parses config.yaml into strongly typed structures.

Owner: Krishna Sikheriya (IIT2023139)
"""

import os
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_PATH = _PROJECT_ROOT / "config.yaml"


class AgentConfig(BaseModel):
    mode: str = Field(pattern="^(react|fixed_pipeline)$")


class PlausibilityConfig(BaseModel):
    source: str = Field(pattern="^(lookup_first|force_agent)$")


class ConfidenceWeightsConfig(BaseModel):
    w_signal: float
    w_grade: float
    w_plausibility: float


class CacheConfig(BaseModel):
    enabled: bool
    dir: str
    ttl_seconds: int


class ApisConfig(BaseModel):
    faers_endpoint: str
    max_pubmed_abstracts: int
    request_delay_seconds: float


class LoggingConfig(BaseModel):
    level: str
    transcript_dir: str


class PathsConfig(BaseModel):
    data_dir: str
    prompts_dir: str
    output_dir: str


class AppConfig(BaseModel):
    agent: AgentConfig
    plausibility: PlausibilityConfig
    confidence_weights: ConfidenceWeightsConfig
    cache: CacheConfig
    apis: ApisConfig
    logging: LoggingConfig
    paths: PathsConfig


_config_instance = None

def load_config() -> AppConfig:
    global _config_instance
    if _config_instance is None:
        if not _CONFIG_PATH.exists():
            raise FileNotFoundError(f"Missing config.yaml at {_CONFIG_PATH}")
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)
        _config_instance = AppConfig(**raw_data)
    return _config_instance
