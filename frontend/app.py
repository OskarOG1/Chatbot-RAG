import streamlit as st
import httpx

API_URL = "http://127.0.0.1:8000/chat"

NEGACJE = {"nie", "nie o to chodziło", "nie o to mi chodziło", "to nie to", "źle"}


def jest_negacja(tekst: str) -> bool:
    """True tylko gdy CAŁA wiadomość to negacja (pełny tekst, nie prefiks),
    żeby 'nie mogę się zalogować' nie zostało potraktowane jako odrzucenie."""
    return tekst.strip().lower() in NEGACJE


with st.sidebar:
    st.header("Ustawienia")
    wybor = st.selectbox("Sekcja (agent)", ["auto", "konto", "zakupy", "platnosci"])
agent_param = None if wybor == "auto" else wybor

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'historia_api' not in st.session_state:
    st.session_state.historia_api = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg['content'])

if prompt := st.chat_input():
    # user odrzucił korektę ("nie") → wróć do oryginału sprzed korekty, bez korektora
    if jest_negacja(prompt) and st.session_state.get("ostatnia_korekta"):
        wiadomosc = st.session_state.ostatnia_korekta
        bez_korekty = True
        st.session_state.ostatnia_korekta = None  # nie zapętlaj kolejnym "nie"
    else:
        wiadomosc = prompt
        bez_korekty = False

    historia = list(st.session_state.historia_api)

    # w czacie pokazujemy to, co user NAPISAŁ (prompt), a do API leci wiadomosc
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generuję odpowiedź"):
            odp = httpx.post(API_URL, json={"message": wiadomosc, "agent": agent_param,
                                            "history": historia,
                                            "agent_poprzedni": st.session_state.get("ostatni_agent"),
                                            "bez_korekty": bez_korekty},
                             timeout=100000)
            dane = odp.json()
            answer = dane['answer']
        st.caption(f"Sekcja: {dane['agent']}")
        if dane.get('doprecyzowanie'):
            st.info(dane['doprecyzowanie'])
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    # zapamiętaj ORYGINAŁ tej tury do obsługi "nie"; przy normalnej turze wyczyść
    if dane.get('doprecyzowanie'):
        st.session_state.ostatnia_korekta = wiadomosc
    elif not bez_korekty:
        st.session_state.ostatnia_korekta = None

    # czysta historia + sticky agent TYLKO dla udanych wymian (agent != '')
    if dane['agent']:
        st.session_state.historia_api.append({"role": "user", "content": wiadomosc})
        st.session_state.historia_api.append({"role": "assistant", "content": answer})
        st.session_state.ostatni_agent = dane['agent']

    zrodla = dane.get('sources', [])
    if zrodla:
        st.caption("Źródła:")
        for url in zrodla:
            st.markdown(f"- [{url}]({url})")
