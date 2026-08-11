from pathlib import Path
import yaml

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

HEADER = {
    'User-Agent': USER_AGENT,
    'Accept-Language': 'pl-PL,pl;q=0.9,en;q=0.8',
}


def zapisz_md(artykul: dict, docs_dir: Path) -> None:
    nazwa = artykul['url'].rstrip('/').split('/')[-1] + '.md'
    sciezka = docs_dir / artykul['agent'] / nazwa
    sciezka.parent.mkdir(parents=True, exist_ok=True)

    meta = {k: artykul[k] for k in ('url', 'tytul', 'agent', 'podslug')}
    frontmatter = '---\n' + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + '---\n\n'
    sciezka.write_text(frontmatter + artykul['tresc'], encoding='utf-8')
