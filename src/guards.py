
import re
import unicodedata

MIN_ZNAKI = 3
MAX_ZNAKI = 500

LEET = str.maketrans({'0': 'o', '1': 'l', '3': 'e', '4': 'a', '5': 's', '@': 'a', '$': 's'})

WZORCE_INJEKCJI = tuple(re.compile(wzorzec) for wzorzec in (
    r'\b(?:z)?ignoruj\w*(?:\s+\w+){0,3}\s+(?:instrukcj|polecen|wytyczn|zasad|regul)',
    r'\bzapomnij(?:\s+\w+){0,3}\s+(?:instrukcj|polecen|wytyczn|zasad)',
    r'\b(?:pomin|omin|zignoruj)\w*(?:\s+\w+){0,3}\s+(?:instrukcj|polecen|wytyczn)',
    r'\b(?:ignore|disregard|forget|override|bypass|skip)(?:\s+\w+){0,3}\s+'
    r'(?:previous|prior|above|earlier|all|any|your|system|instruction|rule)',
    r'\b(?:system|systemow\w*)\s*prompt',
    r'\bprompt\w*\s+systemow',
    r'\b(?:nowa|nowe)\s+(?:instrukcj|polecen)',
    r'\bnew\s+(?:instruction|rule|system)',
    r'\bact\s+as\b',
    r'\budawaj\b',
    r'\bpretend\s+(?:to\s+be|you|that)',
    r'\bjailbreak',
    r'\bdan\s+mode\b',
    r'\b(?:reveal|show|print|repeat)(?:\s+\w+){0,2}\s+(?:prompt|instruction|system)',
    r'\bpoka[zż]\w*(?:\s+\w+){0,3}\s+(?:prompt|instrukcj)',
))

def bez_ogonkow(s: str) -> str:
    s = s.replace('ł', 'l').replace('Ł', 'L')
    rozlozone = unicodedata.normalize('NFKD', s)
    return ''.join(z for z in rozlozone if not unicodedata.combining(z))

def normalizuj(q: str) -> str:
    return re.sub(r'\s+', ' ', bez_ogonkow(q.lower())).strip()

def liter(q:str) -> float:
    return sum(z.isalpha() for z in q) / len(q) if q else 0.0

def alfabet_lacinski(q:str) -> float:
    litery = [z for z in q if z.isalpha()]
    if not litery:
        return 1.0
    lacinskie = sum('LATIN' in unicodedata.name(z, '') for z in litery)
    return lacinskie / len(litery)

def wykryj_injekcje(q: str) -> bool:
    plaski = normalizuj(q)
    for wariant in (plaski, plaski.translate(LEET)):
        if any(wzorzec.search(wariant) for wzorzec in WZORCE_INJEKCJI):
            return True
    return False

def sprawdz(query: str) -> str | None:
    q = query.strip()

    if len(q) < MIN_ZNAKI:
        return "Napisz proszę pełne pytanie."
    if len(q) > MAX_ZNAKI:
        return "Pytanie jest za długie, opisz jeden problem na raz."
    if liter(q) < 0.4:
        return "Nie rozumiem pytania. Czy możesz napisać je inaczej?"
    if alfabet_lacinski(q) < 0.5:
        return "Pomagam w sprawach Allegro po polsku — napisz proszę pytanie po polsku."

    if wykryj_injekcje(q):
        return "Mogę pomóc tylko w sprawach zakupów, konta i płatności"

    return None
