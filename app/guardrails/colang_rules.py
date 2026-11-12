

from app.guardrails.injection import find_question_injection

def injection_check(text:str) -> bool:
    return bool(find_question_injection(text))