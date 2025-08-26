import argparse
import os
import sys
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from actors.victorCore import VictorCore
import time
import json

def list_users(victor):
    print("\n📋 Utenti registrati:")
    users = victor.get_all_users()
    if not users:
        print("ℹ️  Nessun utente registrato.")
        return
    for user in users:
        print(f"\n👤 User ID: {user['user_id']}")
        for i, device in enumerate(user.get("devices", []), 1):
            print(f"  {i}. 📱 Dispositivo:")
            print(f"     - 🔑 Public Key: {device['public_key']}")
            print(f"     - ⚙️  Parametri: {json.dumps(device['system_params'], indent=4)}")

def manual_verify(victor, user_id):
    user = victor.get_user(user_id)
    if not user:
        print("❌ Utente non trovato nel database.")
        return

    challenge = victor.generate_challenge()
    print(f"🔐 Challenge generata: {challenge}")

    try:
        commitment = int(input("🔐 Inserisci commitment ricevuto da Peggy: "))
        response = int(input("✍️ Inserisci response ricevuto da Peggy: "))
    except ValueError:
        print("❌ Inserisci solo numeri interi.")
        return

    result = victor.verify_proof(user_id, commitment, challenge, response)
    if result['success']:
        print("✅ Verifica riuscita. ZKP valido.")
    else:
        print(f"❌ Verifica fallita: {result['message']}")

def main():
    parser = argparse.ArgumentParser(description="Victor CLI - ZKP Verifier")
    parser.add_argument("--listen", action="store_true", help="Avvia Victor in modalità ascolto socket")
    parser.add_argument("--list-users", action="store_true", help="Mostra gli utenti registrati")
    parser.add_argument("--verify", metavar="USER_ID", help="Avvia verifica manuale per un utente")

    args = parser.parse_args()

    victor = VictorCore()

    if args.listen:
        print("🛡️ Victor in ascolto su socket...")
        threading.Thread(target=victor.start_socket_server, daemon=True).start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Server interrotto manualmente.")
            sys.exit(0)

    elif args.list_users:
        list_users(victor)

    elif args.verify:
        manual_verify(victor, args.verify)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
