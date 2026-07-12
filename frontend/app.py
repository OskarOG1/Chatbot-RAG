import streamlit as st
import httpx

API_URL = "http://127.0.0.1:8000/chat" 

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg['content'])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generuje odpowiedź"):
            odp = httpx.post(API_URL, json={"message": prompt}, timeout=1000000 )
            dane = odp.json()
            answer = dane['answer']
        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
