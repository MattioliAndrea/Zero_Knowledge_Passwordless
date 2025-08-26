import json
import socket
import threading
import jwt
import time
import smtplib
from email.message import EmailMessage
from pymongo import MongoClient
from typing import Optional

from libs.interfaces.icrypto_utils import ICryptoUtils
from libs.interfaces.izkp_core import IZKPCore
from libs.zkp_core import ZKPCore
from libs.crypto_utils import CryptoUtils

SECRET = "supersecret"
    
class VictorCore:
    def __init__(self, db_url="mongodb://localhost:27017", db_name="zkp_system", collection="users", host="localhost", port=8080,zkp: IZKPCore = None,utils: ICryptoUtils = None):
        self.zkp = zkp or ZKPCore()
        self.utils = utils or CryptoUtils()
        self.client = MongoClient(db_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection]
        self.host = host
        self.port = port
        self.server_socket = None

    def start_socket_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[Victor] In ascolto su {self.host}:{self.port}...")
        
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                print(f"[Victor] Connessione accettata da {addr} requested on {client_socket.getsockname()}")
                threading.Thread(target=self.handle_request, args=(client_socket,), daemon=True).start()
        except KeyboardInterrupt:
            print("[Victor] Arresto richiesto.")
        finally:
            self.server_socket.close()

    def handle_request(self, client_socket):
        try:
            buffer = ""
            while True:
                data = client_socket.recv(4096).decode()
                if not data:
                    break
                buffer += data
                try:
                    message = json.loads(buffer)
                    buffer = ""  # reset buffer after successful parse
                    response = {}

                    if message['type'] == 'registration_request':
                        response = self.register_user(
                            message['user_id'],
                            message['public_key'],
                            message['system_params']
                        )

                    elif message['type'] == 'auth_request':
                        # Nessuna risposta utile, solo segnale per avviare il flusso
                        response = {"type": "challenge_request"}

                    elif message['type'] == 'commitment':
                        q=message["device_public_key"].get("system_params").get("q")
                        challenge = self.generate_challenge(int(q))
                        
                        # Invia la challenge includendo l'ID utente e la chiave pubblica
                        response = {
                            "type": "challenge",
                            "user_id": message["user_id"],
                            "device_public_key": message["device_public_key"].get("public_key"),
                            "challenge": challenge,
                            "commitment": message["commitment"]
                        }
                        # Salva dati necessari per la verifica
                        self.temp_commitment = message["commitment"]
                        self.temp_challenge = challenge
                        self.temp_user_id = message["user_id"]
                        self.temp_device_pk = message["device_public_key"]

                    elif message['type'] == 'response':
                        if message.get("user_id")==self.temp_user_id:
                            if message.get("device_public_key")==self.temp_device_pk:
                            
                                verification = self.verify_proof(
                                    user_id=message.get("user_id"),
                                    device_public_key=message.get("device_public_key"),
                                    commitment=self.temp_commitment,
                                    challenge=self.temp_challenge,
                                    response=message['response']
                                    )
                                response = {
                                    "type": "auth_result",
                                    "success": verification['success'],
                                    "message": verification['message']
                                }
                            else:
                                response = {
                                    "type": "auth_result",
                                    "success": False
                                }
                        else:
                            response = {
                                    "type": "auth_result",
                                    "success": False
                                }
                    elif message['type'] == 'manage devices':
                        VictorCore.handle_manage_request(message["user_id"],message["user_email"])
                    else:
                        print(f"[DEBUG] messaggio non riconosciuto:\n\t{message}")
                    client_socket.send(json.dumps(response).encode())
        
                except json.JSONDecodeError:
                        continue  # wait for complete JSON
        except Exception as e:
            print(f"[Victor] Errore nella gestione della richiesta: {e}")
        finally:
            client_socket.close()


    def get_all_users(self):
        return list(self.collection.find({}, {"_id": 0}))

    def get_user(self, user_id: str) -> Optional[dict]:
        return self.collection.find_one({"user_id": user_id})

    def is_params_compatible(self, stored_params: dict) -> bool:
        return self.utils.check_parameter_consistency(stored_params)

    def register_user(self, user_id: str, public_key: int, system_params: dict) -> dict:

        # Cast to string (safety for Mongo)
        safe_public_key = str(public_key)
        safe_system_params = {k: str(v) for k, v in system_params.items()}
        
        # print("[Victor DEBUG] Prima di insert_one:")
        # print(f"→ public_key: {safe_public_key} (type={type(safe_public_key)})")
        # print(f"→ system_params: {safe_system_params}")
        
        user = self.get_user(user_id)
        
        
        if user:
            print(f"[Victor] Utente '{user_id}' ESISTE già.")
            # L'utente esiste già → stiamo registrando un nuovo dispositivo
            
            #SE SI VUOLE UN SOLO DISPOSITIVO A UTENTE
            # existing_params = user.get("system_params", {})
            # if not self.utils.check_parameter_consistency(system_params, existing_params):
            #     return {"success": False, "message": "Parametri incompatibili con i dispositivi esistenti dell'utente."}
                
            # Aggiungi il nuovo dispositivo (opzionale: puoi generare un device_id)
            new_device = {
                "public_key": safe_public_key,
                "system_params": safe_system_params
                }
            
            # Verifica se il dispositivo è già registrato
            for d in user.get("devices", []):
                if d["public_key"] == safe_public_key and d["system_params"] == safe_system_params:
                    return {"success": False, "message": "Dispositivo già registrato."}

            
            self.collection.update_one(
                {"user_id": user_id},
                {"$push": {"devices": new_device}}
            )

            return {"success": True, "message": f"Nuovo dispositivo registrato per '{user_id}'."}
        
        else:
            print(f"[Victor] Utente '{user_id}' NUOVA REGISTRAZIONE.")
            # Primo dispositivo per questo utente → nuova registrazione
            self.collection.insert_one({
                "user_id": user_id,
                #"system_params": safe_system_params,
                "devices": [{
                    "public_key": safe_public_key,
                    "system_params": safe_system_params
                    }]
                })
  

            return {"success": True, "message": f"Utente '{user_id}' registrato."}

    def verify_proof(self, user_id: str, device_public_key: str, commitment: int, challenge: int, response: int) -> dict:
        
        #User
        user = self.get_user(user_id)
        if not user:
            return {"success": False, "message": "Utente non trovato."}
        
        # Estrai il valore corretto della chiave pubblica
        device_pk_value = (
            device_public_key["public_key"]
            if isinstance(device_public_key, dict)
            else device_public_key
        )

        # Cerca il dispositivo corretto
        # Cast a stringa entrambi i lati per garantire compatibilità con MongoDB
        device = next(
            (d for d in user.get("devices", []) if str(d["public_key"]) == str(device_pk_value)),
            None
        )
              
        if not device:
            return {"success": False, "message": "Dispositivo non trovato  per l'utente.."}

        # Prova sul dispositivo registrato
        try:
            public_key = int(device["public_key"])
            system_params = {k: int(v) for k, v in device["system_params"].items()}
        except Exception as e:
            return {"success": False, "message": f"Errore nella conversione dei parametri: {e}"}
        valid = self.zkp.verify_response(commitment, challenge, response, public_key, system_params)
        return {
            "success": valid,
            "message": "Autenticazione riuscita." if valid else "Autenticazione fallita."
        }

    def generate_challenge(self, q: int) -> int:
        return self.zkp.generate_challenge(q)
    
    
    
    ### SURPLUS


    def generate_jwt(user_id):
        payload = {
            "user_id": user_id,
            "exp": int(time.time()) + 300  # 5 minuti
        }
        return jwt.encode(payload, SECRET, algorithm="HS256")

    def send_device_management_email(user_email, jwt_token):
        link = f"http://localhost:8503/manage?token={jwt_token}"
        msg = EmailMessage()
        msg["Subject"] = "Gestione dispositivi ZKP"
        msg["From"] = "victor@zkp.local"
        msg["To"] = user_email
        msg.set_content(f"""
    Hai richiesto di gestire i tuoi dispositivi ZKP.

    Clicca qui per accedere: {link}

    Se non sei stato tu, ignora questa email.
    """)
        try:
            with smtplib.SMTP("localhost", 1025) as smtp:
                smtp.send_message(msg)
            print(f"[Victor] Email inviata a {user_email}")
        except Exception as e:
            print(f"[Victor] Errore durante invio email: {e}")
            
    def handle_manage_request( user_id, user_email):
        print(f"[Victor] Ricevuta richiesta gestione dispositivi per {user_id}")
        token = VictorCore.generate_jwt(user_id)
        VictorCore.send_device_management_email(user_email, token)


