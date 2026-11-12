COMPLEX_WORDS = {"itinerary", "plan", "compare", "budget", "route", "schedule", "days"}

def pick_tier(question:str) -> str:
    q = question.lower()
    if len(q.split()) > 30 or any(w in q for w in COMPLEX_WORDS):
        return "smart"

    return "fast"