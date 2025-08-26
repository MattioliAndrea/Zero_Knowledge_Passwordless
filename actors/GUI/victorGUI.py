import sys
import os
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import streamlit as st
from actors.victorCore import VictorCore


#partenza di VictorCore
if "victor" not in st.session_state:
    victor = VictorCore()
    st.session_state.victor = victor
    threading.Thread(target=st.session_state.victor.start_socket_server, daemon=True).start()
    
st.set_page_config(page_title="Victor - Verifier Dashboard", layout="wide")
st.title("🛡️ Victor - Verifica Zero-Knowledge")

with st.expander("📋 Utenti registrati", expanded=True):
    users = st.session_state.victor.get_all_users()
    if not users:
        st.warning("Nessun utente registrato.")
    else:
        for user in users:
            with st.expander(f" 👤 Utente: **{user['user_id']}** ", expanded=False):
                for i, device in enumerate(user.get("devices", []), 1):
                    st.markdown(f"{i}. 📱 **Dispositivo {device['system_params']}** - 🔑 `{device['public_key']}`")

st.subheader("🔍 Verifica ZKP manuale")
with st.form("verify_form"):
    user_id = st.text_input("Email utente")
    commitment = st.text_input("Commitment ricevuto")
    response = st.text_input("Response ricevuto")
    submitted = st.form_submit_button("Verifica")

if submitted:
    try:
        commitment = int(commitment)
        response = int(response)
        challenge = victor.generate_challenge()

        result = victor.verify_proof(user_id, commitment, challenge, response)
        with st.container():
            st.write(f"📨 Challenge generata: `{challenge}`")
            if result['success']:
                st.success("✅ Verifica superata")
            else:
                st.error(f"❌ Verifica fallita: {result['message']}")
    except ValueError:
        st.error("⚠️ Inserisci valori numerici validi per commitment e response")
        