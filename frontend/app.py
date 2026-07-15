import streamlit as st
import httpx

API_URL = "http://127.0.0.1:8000/chat" 

with st.sidebar:
    st.header("Ustawienia")
    wybor = st.selectbox("Sekcja (agent)", ["auto", "konto", "zakupy", "platnosci"])
agent_param = None if wybor == "auto" else wybor

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg['content'])

if prompt := st.chat_input():
    historia = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("Generuje odpowiedź"):
            odp = httpx.post(API_URL, json={"message": prompt, "agent": agent_param,
                                            "history": historia,
                                            "agent_poprzedni": st.session_state.get("ostatni_agent")},
                             timeout=100000)
            dane = odp.json()
            answer = dane['answer']
        st.caption(f"Sekcja: {dane['agent']}")
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.ostatni_agent = dane['agent']

    zrodla = dane.get('sources', [])
    if zrodla:
        st.caption("Źródła:")
        for url in zrodla:
            st.markdown(f"- [{url}]({url})")