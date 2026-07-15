import re

MIN_ZNAKI = 3
MAX_ZNAKI = 500
IGNORUJ = [
    'ignore previous', 'ignoruj instrukcje', 'zapomnij instrukcje',
    'system prompt', 'act as', 'udawaj', 'jailbreak', 'pomin instrukcje',
]

def liter(q:str) -> float:
    return sum(z.isalpha() for z in q) / len(q) if q else 0.0

def sprawdz(query: str) -> str | None:
    q = query.strip()

    if len(q) < MIN_ZNAKI:
        return "Napisz proszę pełne pytanie."
    if len(q) > MAX_ZNAKI:
        return "Pytanie jest za długie, opisz jeden problem na raz."
    if liter(q) < 0.4:
        return "Nie rozumiem pytania. Czy możesz napisać je inaczej?"
    
    low = q.lower()
    if any(i in low for i in IGNORUJ):
        return "Mogę pomóc tylko w sprawach zakupów, konta i płatności"
    
    return None