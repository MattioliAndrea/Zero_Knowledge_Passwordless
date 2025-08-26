import argparse
import sys
import os
from getpass import getpass
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from libs.zkp_core import ZKPCore
from actors.peggyCore import PeggyCore


SERVER_HOST = "localhost"
SERVER_PORT = 8081  # Anthony proxy
CLIENT_DB = "clientDB"
DEFAULT_KEY_SIZE = 64

def print_devices(devices):
    for i, d in enumerate(devices):
        print(f"[{i}] Chiave pubblica: {d['public_key']}")
    
def is_power_of_two_bitwise(n:int):
    if n <= 0:
        return False
    return (n & (n - 1)) == 0

def handle_registration(peggy,email,password,key_size):
                                               
    print("📱 Registrazione nuovo dispositivo...")
    credentials = peggy.save_credentials(email, password,key_size)
    print("✅ Dispositivo registrato localmente.")

    registration_msg = {
        "type": "registration_request",
        "user_id": email,
        "public_key": credentials['public_key'],
        "system_params": credentials['system_params']
    }

    response = next(peggy.communicate_with_server([registration_msg]))
    if response.get("success"):
        print("📡 Dispositivo registrato anche su Victor.")
    else:
        print(f"❌ Errore server: {response.get('message')}")
        peggy.remove_credential(email,password,credentials['public_key'])


def handle_login(peggy,email,password):
    if not peggy.verify_password(password, email):
        print("❌ Password errata o account non trovato.")
        return

    stored = peggy.load_credentials(email)
    devices = stored.get("devices", [])
    if not devices:
        print("⚠️  Nessun dispositivo registrato.")
        return

    if len(devices) > 1:
        print("📱 Dispositivi disponibili:")
        print_devices(devices)
        try:
            idx = int(input("Seleziona l'indice del dispositivo: ").strip())
            selected_device = devices[idx]
        except Exception:
            print("❌ Selezione non valida.")
            return
    else:
        selected_device = devices[0]

    system_params = {k: int(v) for k, v in selected_device["system_params"].items()}
    print("[PeggyCLI] → Parametri usati:")
    print("  system_params:", system_params)
    print("  public_key:", selected_device["public_key"])

    try:    
        # Fasi ZKP
        commitment, nonce = peggy.zkp.create_commitment(password, email, system_params)

        steps = [
            {"type": "auth_request"},
            {
                "type": "commitment",
                "user_id": email,
                "device_public_key": selected_device,
                "commitment": commitment
                }
            ]
        
        responses = peggy.communicate_with_server(steps)          
        next(responses)  # challenge_request
        challenge_data = next(responses)
        if challenge_data.get("type") != "challenge":
            raise ValueError("Challenge non ricevuta")

        challenge = challenge_data["challenge"]
        response = peggy.zkp.create_response(nonce, challenge, password, email, system_params)

        final = {
            "type": "response",
            "user_id": email,
            "device_public_key": selected_device,
            "response": response
        }

        result = next(peggy.communicate_with_server([final]))
        if result.get("success"):
            print("✅ Autenticazione riuscita!")
        else:
            print("❌ Autenticazione fallita.")
    except Exception as e:
        print(f"❌ Errore nel flusso ZKP: {e}")


def main():
    # CLI args
    parser = argparse.ArgumentParser(description="🔐 PeggyCLI - Login/Registrazione ZKP")
    parser.add_argument("--host", type=str, default="localhost", help="Host di connessione a Victor/Anthony")
    parser.add_argument("--port", type=int, default=8081, help="Porta di connessione a Victor/Anthony")
    args = parser.parse_args()
    
    print("🛠️  PeggyCLI Daemon avviato")
    print("💡 Usa 'exit' o 'quit' per uscire dal programma")

    # Init
    peggy = PeggyCore(ZKPCore(),server_host=args.host, server_port=args.port)

	# Store last used credentials
    last_email = ""
    last_password = ""
    while True:
        try:
            print("\n=== PEGGY CLI DAEMON ===\n")
            
            # Get user input with default from previous cycle
            if last_email:
                print(f"📧 Email e password precedenti disponibili: {last_email}")
                choice = input("➤ Usare email precedente? (s/n) o 'exit'/'quit' per uscire: ").strip().lower()
                
                if choice in ['exit', 'quit', 'q']:
                    print("👋 Arrivederci!")
                    break
                elif choice in ['s', 'si', 'y', 'yes', '']:
                    email = last_email
                    password = last_password
                    print(f"📧 Utilizzando email precedente: {email}")
                elif choice in ['n', 'no']:
                    email = input("📧 Inserisci nuova email: ").strip()
                    password = getpass("🔑 Password: ").strip()
                else:
                    print("⚠️  Scelta non valida. Usa 's' per sì o 'n' per no.")
                    continue
            else:
                email = input("📧 Email (o 'exit'/'quit' per uscire): ").strip()
                password = getpass("🔑 Password: ").strip()
            
            # Check for exit commands
            if email.lower() in ['exit', 'quit', 'q']:
                print("👋 Arrivederci!")
                break
                
            if not email:
                print("⚠️  Email non può essere vuota.")
                continue
                
            if not password:
                print("⚠️  Password non può essere vuota.")
                continue
            
            last_email=email
            last_password=password
            
            action = input("➤ Azione (login / registra): ").strip().lower()
            
            if action=="login":
                handle_login(peggy,email,password)
            elif action=="registra":
                key_size=int(input(("Seleziona la dimensione della chiave in bit: ")))
                        
                if not is_power_of_two_bitwise(key_size):
                    print("Chiave inserita non è una potenzadi due")
                    continue
                
                handle_registration(peggy,email,password,key_size)
            else:
                print("⚠️  Azione non riconosciuta. Usa 'login' o 'registra'.")
                continue 
        
        except KeyboardInterrupt:
            print("\n\n👋 Programma interrotto dall'utente. Arrivederci!")
            break
        except Exception as e:
            print(f"❌ Errore imprevisto: {e}")
            print("🔄 Riprovo...")
            continue

if __name__ == "__main__":
    main()
