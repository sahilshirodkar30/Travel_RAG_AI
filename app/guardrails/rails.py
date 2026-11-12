from functools import lru_cache
from pathlib import Path

from nemoguardrails import LLMRails,RailsConfig
from app.gateway.gateway import get_llm
from app.guardrails.colang_rules import injection_check

CONFIG_DIR = Path(__file__).parent /"config"

@lru_cache
def get_rails(tier:str) -> LLMRails:
    config = RailsConfig.from_path(str(CONFIG_DIR))
    rails = LLMRails(config,llm=get_llm(tier))
    rails.register_action(injection_check,name="injection_check")
    return rails