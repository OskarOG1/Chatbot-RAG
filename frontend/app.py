import streamlit as st
import httpx
import json
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat/stream")

NEGACJE = {"nie", "nie o to chodziło", "nie o to mi chodziło", "to nie to", "źle"}


def jest_negacja(tekst: str) -> bool:
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
    if jest_negacja(prompt) and st.session_state.get("ostatnia_korekta"):
        wiadomosc = st.session_state.ostatnia_korekta
        bez_korekty = True
        st.session_state.ostatnia_korekta = None
    else:
        wiadomosc = prompt
        bez_korekty = False

    historia = list(st.session_state.historia_api)

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        status = st.status("Myślę…", expanded=True)
        caption_ph = st.empty()
        info_ph = st.empty()
        answer_ph = st.empty()
        holder = {"dane": None, "blad": None}

        def strumien():
            try:
                with httpx.stream("POST", API_URL,
                                  json={"message": wiadomosc, "agent": agent_param,
                                        "history": historia,
                                        "agent_poprzedni": st.session_state.get("ostatni_agent"),
                                        "bez_korekty": bez_korekty},
                                  timeout=httpx.Timeout(120.0, connect=5.0)) as r:
                    for linia in r.iter_lines():
                        if not linia or not linia.startswith("data:"):
                            continue
                        ev = json.loads(linia[5:].strip())
                        typ = ev["typ"]
                        if typ == "krok":
                            status.write(ev["tekst"])
                        elif typ == "token":
                            yield ev["tekst"]
                        elif typ == "wynik":
                            holder["dane"] = ev["dane"]
                        elif typ == "blad":
                            holder["blad"] = ev["tekst"]
            except httpx.ConnectError:
                holder["blad"] = "Backend nie odpowiada — spróbuj ponownie za chwilę."
            except httpx.TimeoutException:
                holder["blad"] = "Zbyt długi czas odpowiedzi — spróbuj ponownie."
            except httpx.HTTPError:
                holder["blad"] = "Połączenie zostało przerwane — spróbuj ponownie."
            except (json.JSONDecodeError, KeyError, UnicodeDecodeError):
                holder["blad"] = "Nieprawidłowa odpowiedź serwera — spróbuj ponownie."

        with answer_ph.container():
            st.write_stream(strumien)

        dane = holder["dane"]
        status.update(label="Gotowe" if dane else "Błąd",
                      state="complete" if dane else "error")

        if dane is None:
            dane = {"agent": "", "answer": holder["blad"] or "Backend nie odpowiedział — spróbuj ponownie za chwilę.",
                    "sources": [], "citations": [], "doprecyzowanie": None}

        answer = dane["answer"]
        if dane["agent"]:
            caption_ph.caption(f"Sekcja: {dane['agent']}")
        if dane.get("doprecyzowanie"):
            info_ph.info(dane["doprecyzowanie"])
        answer_ph.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

    if dane.get("doprecyzowanie"):
        st.session_state.ostatnia_korekta = wiadomosc
    elif not bez_korekty:
        st.session_state.ostatnia_korekta = None

    if dane["agent"]:
        st.session_state.historia_api.append({"role": "user", "content": wiadomosc})
        st.session_state.historia_api.append({"role": "assistant", "content": answer})
        st.session_state.ostatni_agent = dane["agent"]

    zrodla = dane.get("sources", [])
    if zrodla:
        st.caption("Źródła:")
        for url in zrodla:
            st.markdown(f"- [{url}]({url})")
