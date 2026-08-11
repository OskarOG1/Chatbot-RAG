import re

ARTYKUL_REGEX = re.compile(
    r'^https://allegro\.pl/pomoc/dla-kupujacych/[^/]+/[^/]+-[A-Za-z0-9]{6,}$'
    r'|^https://help\.allegro\.com/(?:pl|en)/sell/a/[^/]+-[A-Za-z0-9]{6,}$'
)
