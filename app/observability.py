import logfire
from app.config import get_settings

_configured = False
settings = get_settings()
def setup_observability() -> None:
    global _configured
    if _configured:
        return

    logfire.configure(
        token= settings.logfire_token or None,
        service_name="logs-goa-travel",
        send_to_logfire="if-token-present"
    )
    logfire.instrument_openai()
    _configured = True