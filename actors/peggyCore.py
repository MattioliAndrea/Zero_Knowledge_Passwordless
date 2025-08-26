import os
import json
import socket
from typing import Optional, List, Dict
from libs.interfaces.izkp_core import IZKPCore
from libs.zkp_core import ZKPCore
from libs.interfaces.icrypto_utils import ICryptoUtils
from libs.crypto_utils import CryptoUtils

class PeggyCore:
    def __init__(self, zkp: IZKPCore = None, utils: ICryptoUtils = None, client_db="clientDB", server_host="localhost", server_port=8081):
        self.zkp = zkp or ZKPCore()
        self.server_host=server_host
        self.server_port=server_port
        self.utils = utils or CryptoUtils()
        self.client_db = client_db
        os.makedirs(self.client_db, exist_ok=True)

    def get_credentials_path(self, user_id: str) -> str:
        return os.path.join(self.client_db, f"{user_id}_credentials.json")

    def credentials_exist(self, user_id: str) -> bool:
        return os.path.exists(self.get_credentials_path(user_id))

    def load_credentials(self, user_id: str) -> Optional[dict]:
        path = os.path.join(self.client_db, f"{user_id}_credentials.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return None

    def save_credentials(self, user_id: str, password: str, bit_length:int) -> dict:
        # Genera parametri per nuovo dispositivo
        system_params = self.utils.generate_system_parameters(bit_length)
        private_key = (self.utils.hash_password(password, user_id) % (system_params["q"] - 1)) + 1
        public_key = pow(system_params["g"], private_key, system_params["p"])

        new_device = {
            "public_key": str(public_key),
            "system_params": {k: str(v) for k, v in system_params.items()}
        }

        path = os.path.join(self.client_db, f"{user_id}_credentials.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
        else:
            data = {
                "user_id": user_id,
                "password_hash": self.utils.hash_password(password, user_id),
                "devices": []
            }

        # Aggiunge il nuovo device se non già presente
        if not any(d["public_key"] == new_device["public_key"] for d in data["devices"]):
            data["devices"].append(new_device)

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return {
            "user_id": user_id,
            "public_key": public_key,
            "system_params": system_params
        }
        
    def remove_credential(self, user_id: str, password: str, public_key_to_remove: int) -> dict:
        """
        Rimuove una specifica chiave pubblica per l'utente.
        Se era l'ultimo dispositivo, rimuove l'intero file di credenziali.
        """
        path = os.path.join(self.client_db, f"{user_id}_credentials.json")

        if not os.path.exists(path):
            return {"success": False, "message": "Credenziali non trovate per l'utente."}

        with open(path) as f:
            data = json.load(f)

        # Verifica che la password sia corretta
        stored_hash = data.get("password_hash")
        if stored_hash != self.utils.hash_password(password, user_id):
            return {"success": False, "message": "Password errata."}

        original_count = len(data["devices"])
        # Rimuove i device con quella chiave pubblica
        data["devices"] = [d for d in data["devices"] if str(public_key_to_remove) != d["public_key"]]

        if not data["devices"]:
            # Nessun device rimasto → elimina il file
            os.remove(path)
            return {"success": True, "message": "Ultima chiave rimossa. File credenziali eliminato."}

        elif len(data["devices"]) < original_count:
            # Almeno una chiave è stata rimossa, altre rimangono
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
            return {"success": True, "message": "Chiave pubblica rimossa."}
        else:
            # Nessuna corrispondenza trovata
            return {"success": False, "message": "Chiave pubblica non trovata tra i dispositivi."}


    def verify_password(self, password: str, email: str) -> bool:
        credentials = self.load_credentials(email)
        if not credentials:
            return False
        return credentials["password_hash"] == self.utils.hash_password(password, email)

    def create_commitment(self, password: str, user_id: str,system_params:dict):
        return self.zkp.create_commitment(password, user_id,system_params)

    def create_response(self, nonce: int, challenge: int, password: str, user_id: str, system_params: dict):
        return self.zkp.create_response(nonce, challenge, password, user_id,system_params)
    
    def get_device_keys(self, user_id: str) -> list:
        """
        Restituisce tutte le chiavi pubbliche (principale + dispositivi registrati) per l'utente.
        """
        credentials = self.load_credentials(user_id)
        if not credentials:
            return []

        devices = credentials.get("devices", [])
        return devices  # ciascuno è già un dict con public_key e system_params
    
    def get_system_parameters(self):
        return self.zkp.get_system_parameters()
    
    def communicate_with_server(self, messages):
        """
        Comunica con il server (Victor tramite Anthony) inviando una o più richieste.
        Usa un generatore per gestire il flusso di risposte.
        """
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.server_host, self.server_port))
        try:
            for msg in messages:
                client_socket.send(json.dumps(msg).encode())
                response = client_socket.recv(4096).decode()
                yield json.loads(response)
            #print(f"[PEGGY] invio messaggio {messages}")
        except Exception as e:
            raise ConnectionError(f"Errore di comunicazione con il server: {e}")
        finally:
            client_socket.close()
            
    def send_manage_request_to_victor_request(self,user_id, user_email):
        import requests
        print(f"[Peggy] Invio richiesta ad Anthony per utente {user_id}")
        payload = [{"type":"manage devices","user_id": user_id, "user_email": user_email}]
        try:
            print(payload)
            result = next(PeggyCore.communicate_with_server(self,payload))
            print(f"[Peggy] Risposta da Anthony: {result}")
        except Exception as e:
            print(f"[Peggy] Errore nella richiesta: {e}")
