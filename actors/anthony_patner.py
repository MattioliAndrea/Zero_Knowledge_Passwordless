import os
import json
import socket
import time
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from libs.zkp_core import ZKPCore

SERVER_HOST = "localhost"
SERVER_PORT = 8080  # Anthony ascolta qui
CRACKED_FOLDER = "Cracked_Key"

def load_cracked_keys():
    credentials = []
    for fname in os.listdir(CRACKED_FOLDER):
        if fname.endswith(".json"):
            with open(os.path.join(CRACKED_FOLDER, fname)) as f:
                try:
                    data = json.load(f)
                    params = data.get("params")
                    if not isinstance(params, dict):
                        print(f"⚠️ File {fname} ha un formato invalido: params non è un dizionario")
                        continue
                except json.JSONDecodeError:
                    print(f"{fname} -> JSON non valido")
                try:
                    credentials.append({
                        "user_id": data["user_id"],
                        "private_key": data["private_key"],
                        "public_key": data["public_key"],
                        "g": params["g"],
                        "p": params["p"],
                        "q": params["q"],
                        "bit_length": params["bit_length"],
                    })
                except KeyError as e:
                    print(f"⚠️ Chiave mancante in {fname}: {e}")
    return credentials

def authenticate(user):
    zkp = ZKPCore()
    private_key = user["private_key"]
    g, p, q = user["g"], user["p"], user["q"]
    user_id = user["user_id"]
    bit_length=user["bit_length"]
    y = user["public_key"]

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            print(f"🔌 Connesso a {SERVER_HOST}:{SERVER_PORT} per utente {user_id}")

            # 1. Invia richiesta di auth
            s.send(json.dumps({
                "type": "auth_request"
            }).encode())

            response = json.loads(s.recv(4096).decode())
            if response.get("type") != "challenge_request":
                print("❌ Errore: risposta inattesa")
                return

            # 2. Invia commitment
            system_params = {
                "g": str(g),
                "p": str(p),
                "q": str(q),
                "bit_length": str(bit_length)
            }
            commitment,nonce = zkp.create_commitment("foo","bar", system_params)

            s.send(json.dumps({
                "type": "commitment",
                "user_id": user_id,
                "device_public_key": {
                    "public_key": str(y),
                    "system_params": system_params
                },
                "commitment": commitment
            }).encode())

            challenge_msg = json.loads(s.recv(4096).decode())
            challenge = challenge_msg.get("challenge")

            # 3. Invia risposta finale
            response_value = (nonce + challenge * int(private_key)) % int(q)
            

            s.send(json.dumps({
                "type": "response",
                "user_id": user_id,
                "device_public_key": {
                    "public_key": str(y),
                    "system_params": system_params
                },
                "response": response_value
            }).encode())

            # 4. Ricevi risultato
            final = json.loads(s.recv(4096).decode())
            if final.get("success"):
                print(f"✅ Autenticazione riuscita per {user_id}")
            else:
                print(f"❌ Autenticazione fallita per {user_id}: {final.get('message')}")
    except Exception as e:
        print(f"[!] Errore nella comunicazione per {user_id}: {e}")

def main():
    creds = load_cracked_keys()
    if not creds:
        print("⚠️ Nessuna chiave trovata in Cracked_Key/")
        return
    print(f"🔓 Trovate {len(creds)} credenziali.")
    for user in creds:
        authenticate(user)
        time.sleep(1)  # per evitare flood

if __name__ == "__main__":
    main()
