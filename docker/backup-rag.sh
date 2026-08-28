#!/usr/bin/env bash
set -euo pipefail

KATALOG_SKRYPTU="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KATALOG_RAG="${KATALOG_RAG:-$(dirname "$KATALOG_SKRYPTU")/RAG}"
KATALOG_KOPII="${KATALOG_KOPII:-/opt/backup/rag}"
DNI_PRZECHOWYWANIA="${DNI_PRZECHOWYWANIA:-14}"
MIN_ROZMIAR_ARCHIWUM=40
PLIKI=(log_analytics.jsonl trudne.jsonl)
PLIKI_OPCJONALNE=(kolejka.jsonl)
WZORZEC_ARCHIWUM='log_analytics.jsonl.przed-resetem-*'

policz_linie() {
    local sciezka="$1"
    if [ -f "$sciezka" ]; then
        wc -l < "$sciezka" | tr -d ' '
    else
        echo 0
    fi
}

zbierz_do_archiwum() {
    DO_ARCHIWUM=("${PLIKI[@]}")
    ILE_OPCJONALNYCH=0
    local sciezka plik
    for plik in "${PLIKI_OPCJONALNE[@]}"; do
        if [ -f "$KATALOG_RAG/$plik" ]; then
            DO_ARCHIWUM+=("$plik")
            ILE_OPCJONALNYCH=$(( ILE_OPCJONALNYCH + 1 ))
        fi
    done
    for sciezka in "$KATALOG_RAG"/$WZORZEC_ARCHIWUM; do
        if [ -f "$sciezka" ]; then
            DO_ARCHIWUM+=("$(basename "$sciezka")")
        fi
    done
}

sprawdz_zrodla() {
    local brakujace=()
    local plik
    for plik in "${PLIKI[@]}"; do
        [ -f "$KATALOG_RAG/$plik" ] || brakujace+=("$plik")
    done
    if [ "${#brakujace[@]}" -gt 0 ]; then
        echo "brak plikow zrodlowych w $KATALOG_RAG: ${brakujace[*]}" >&2
        exit 1
    fi
}

zrob_kopie() {
    mkdir -p "$KATALOG_KOPII"
    sprawdz_zrodla

    local data archiwum rozmiar linie_log linie_trudne linie_kolejka ile_archiwow
    data="$(date -u +%Y-%m-%d)"
    archiwum="$KATALOG_KOPII/rag-$data.tar.gz"

    zbierz_do_archiwum
    ile_archiwow=$(( ${#DO_ARCHIWUM[@]} - ${#PLIKI[@]} - ILE_OPCJONALNYCH ))

    tar -czf "$archiwum.tmp" -C "$KATALOG_RAG" "${DO_ARCHIWUM[@]}"
    mv "$archiwum.tmp" "$archiwum"

    rozmiar="$(stat -c%s "$archiwum")"
    if [ "$rozmiar" -lt "$MIN_ROZMIAR_ARCHIWUM" ]; then
        echo "archiwum $archiwum jest puste ($rozmiar B)" >&2
        exit 1
    fi

    find "$KATALOG_KOPII" -maxdepth 1 -name 'rag-*.tar.gz' -mtime "+$DNI_PRZECHOWYWANIA" -delete

    linie_log="$(policz_linie "$KATALOG_RAG/log_analytics.jsonl")"
    linie_trudne="$(policz_linie "$KATALOG_RAG/trudne.jsonl")"
    linie_kolejka="$(policz_linie "$KATALOG_RAG/kolejka.jsonl")"

    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $archiwum ${rozmiar}B log_analytics=$linie_log trudne=$linie_trudne kolejka=$linie_kolejka archiwa_resetu=$ile_archiwow" \
        >> "$KATALOG_KOPII/historia.log"
    echo "zapisano $archiwum (${rozmiar}B, log_analytics=$linie_log, trudne=$linie_trudne, kolejka=$linie_kolejka, archiwa resetu=$ile_archiwow)"
}

odtworz() {
    local archiwum="$1"
    local znacznik plik

    if [ ! -f "$archiwum" ]; then
        echo "nie ma archiwum $archiwum" >&2
        exit 1
    fi

    znacznik="$(date -u +%Y%m%dT%H%M%SZ)"

    cd "$KATALOG_SKRYPTU"
    docker compose stop api

    for plik in "${PLIKI[@]}" "${PLIKI_OPCJONALNE[@]}"; do
        if [ -f "$KATALOG_RAG/$plik" ]; then
            mv "$KATALOG_RAG/$plik" "$KATALOG_RAG/$plik.przed-odtworzeniem-$znacznik"
            echo "odlozono $plik.przed-odtworzeniem-$znacznik"
        fi
    done

    tar -xzf "$archiwum" -C "$KATALOG_RAG"
    docker compose start api

    for plik in "${PLIKI[@]}" "${PLIKI_OPCJONALNE[@]}"; do
        if [ -f "$KATALOG_RAG/$plik" ]; then
            echo "odtworzono $plik: $(policz_linie "$KATALOG_RAG/$plik") linii"
        fi
    done
}

case "${1:-}" in
    '')
        zrob_kopie
        ;;
    --odtworz)
        if [ "$#" -lt 2 ]; then
            echo "uzycie: $0 --odtworz <archiwum.tar.gz>" >&2
            exit 1
        fi
        odtworz "$2"
        ;;
    *)
        echo "uzycie: $0 [--odtworz <archiwum.tar.gz>]" >&2
        exit 1
        ;;
esac
