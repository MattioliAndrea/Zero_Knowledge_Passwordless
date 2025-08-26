# manage_devices.py
import streamlit as st
import jwt
import datetime
import pymongo
from bson.objectid import ObjectId

# Config
SECRET = "supersecret"  # deve essere identico a quello usato in VictorCore

# Connessione MongoDB
def get_mongo_client():
    return pymongo.MongoClient("mongodb://localhost:27017")

def get_devices_for_user(user_id):
    client = get_mongo_client()
    db = client["zkp_system"]
    collection = db["users"]
    user_entry = collection.find_one({"user_id": user_id})
    return user_entry["devices"] if user_entry and "devices" in user_entry else []

def delete_all_devices(user_id):
    client = get_mongo_client()
    db = client["zkp_system"]
    collection = db["users"]
    result = collection.update_one({"user_id": user_id}, {"$set": {"devices": []}})
    return result.modified_count > 0

# Streamlit UI
st.set_page_config(page_title="Gestione Dispositivi", layout="centered")

st.title("🔐 Malia - Gestione Dispositivi Registrati")

token = st.query_params.get("token")
if not token:
    st.error("❌ Token mancante nell'URL.")
    st.stop()

try:
    payload = jwt.decode(token, SECRET, algorithms=["HS256"])
    user_id = payload["user_id"]
    exp = datetime.datetime.fromtimestamp(payload["exp"])

    st.success(f"Benvenuto, utente **{user_id}**")
    st.caption(f"Token valido fino al: {exp.strftime('%Y-%m-%d %H:%M:%S')}")

    devices = get_devices_for_user(user_id)

    if not devices:
        st.warning("Nessun dispositivo registrato.")
    else:
        for idx, device in enumerate(devices, start=1):
            st.markdown(f"### 📱 Dispositivo {idx}")
            st.code(f"Chiave pubblica: {device['public_key']}")
            st.json(device["system_params"])

        if st.button("🗑️ Rimuovi tutti i dispositivi"):
            if delete_all_devices(user_id):
                st.success("Dispositivi rimossi con successo!")
            else:
                st.error("Errore durante la rimozione.")

except jwt.ExpiredSignatureError:
    st.error("❌ Token scaduto.")
except jwt.InvalidTokenError:
    st.error("❌ Token non valido.")
