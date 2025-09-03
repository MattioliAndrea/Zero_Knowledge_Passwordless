import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from getpass import getpass
from actors.peggyCore import PeggyCore

SERVER_HOST = 'localhost'
SERVER_PORT = 8081  # Anthony proxy
CLIENT_DB = "clientDB"



st.set_page_config(page_title="Peggy Login", layout="centered")
st.title("🔐 Peggy - Passwordless Login")
st.sidebar.title("⚙️ Configurazione")
key_size = st.sidebar.selectbox("Dimensione della chiave", [8, 16, 32, 64, 128, 256, 512, 1024, 2048], index=3)

# Init
peggy = PeggyCore()
if "peggy" not in st.session_state:
    st.session_state.peggy = peggy

# Stato utente
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "devices" not in st.session_state:
    st.session_state.devices = []
if "email" not in st.session_state:
    st.session_state.email = ""
if "password" not in st.session_state:
    st.session_state.password = ""
    
# FORM login
with st.form("login_form"):
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    action = st.selectbox("Azione", ["Login", "Registra nuovo dispositivo"])
    submitted = st.form_submit_button("Procedi")

if submitted and email and password:
    
    if(action !="Login" and action!="Registra nuovo dispositivo"):
        st.warning("⚠️ azione sconosciuta!")
    else:
        st.session_state.email = email
        st.session_state.password = password
        stored = peggy.load_credentials(email)


        if stored and peggy.verify_password(password, email) and action == "Login":
            st.success("🔓 Password verificata")
            st.session_state.authenticated = True
            st.session_state.devices = stored.get("devices", [])
            del stored 
                    
        elif action == "Registra nuovo dispositivo":
                st.info("Registrazione nuovo dispositivo in corso...")
                credentials = peggy.save_credentials(email, password,key_size)
                print("[Peggy DEBUG] Credenziali salvate:", credentials)
                st.success("📱 Dispositivo registrato con successo in locale")
                
                registration_msg = {
                    "type": "registration_request",
                    "user_id": email,
                    "public_key": credentials['public_key'],
                    "system_params": credentials['system_params']
                }
                server_response = next(peggy.communicate_with_server([registration_msg]))
                if server_response['success']:
                    
                    st.success("📡 Dispositivo registrato anche su Victor")
                else:
                    st.error(f"Errore nella registrazione: {server_response['message']}")
        else:
            st.warning("⚠️ Password errata o account non registrato.")

# Mostra selectbox solo se login + dispositivi ≥ 1
if st.session_state.authenticated and action == "Login" and len(st.session_state.devices) >= 1:
    device_map = {d["public_key"]: d for d in st.session_state.devices}
    selected_key = st.selectbox("📱 Seleziona il dispositivo", list(device_map.keys()))
    selected_device = device_map[selected_key]
        
    if st.button("🔍 Verifica dispositivo selezionato"):
        st.info("Avvio autenticazione con Victor...")
        email = st.session_state.email
        device_params = {k: int(v) for k, v in selected_device["system_params"].items()}
            
        #fasi ZKP
        
        commitment, nonce = peggy.zkp.create_commitment(password, email,device_params)
        steps = [
            {
                "type": "auth_request"
            },
            {
                "type": "commitment",
                "user_id": email,
                "device_public_key":selected_device,
                "commitment": commitment
            }
        ]

        server_responses = peggy.communicate_with_server(steps)
        try:
            next(server_responses)  # challenge_request
            challenge_response = next(server_responses)
            if challenge_response['type']=="challenge":
                
                challenge = challenge_response['challenge']
                
                response = peggy.zkp.create_response(nonce, challenge, password, email,device_params)
                
                print("[Peggy] → Parametri usati:")
                print("  system_params:", device_params)
                print("  public_key:", selected_device['public_key'])
                
                final = {
                    "type": "response",
                    "user_id": email,
                    "device_public_key":selected_device,
                    "response": response
                    }
                    
                result = next(peggy.communicate_with_server([final]))
                
                if result['success']:
                    st.success("✅ Autenticazione riuscita!")
                else:
                    st.error("❌ Autenticazione fallita")
            else:
                st.error("❌ Autenticazione fallita")
        except Exception as e:
            st.error(f"Errore durante il flusso: {e}")


# Dispositivi
if st.button("📬 Gestisci dispositivi via email"):
    peggy.send_manage_request_to_victor_request(email, email+"@prover.local")
    st.success("Email inviata! Controlla la casella su MailHog (http://localhost:8025).")
    
