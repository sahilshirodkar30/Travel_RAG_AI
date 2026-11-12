
from functools import lru_cache
from langchain_openai import ChatOpenAI
from app.config import get_settings

@lru_cache
def get_llm(tier:str) -> ChatOpenAI:
    s = get_settings()
    if tier == "smart":
        config_id,model = s.portkey_config_smart,s.smart_model
    else:
        config_id,model = s.portkey_config_fast,s.fast_model


    return ChatOpenAI(
        model=model,
        base_url=s.portkey_url,
        api_key="portkey",
        temperature=.3,
        timeout=20,
        max_retries=0,
        default_headers={
            "x-portkey-api-key":s.portkey_api_key,
            "x-portkey-config":config_id
        }
    )